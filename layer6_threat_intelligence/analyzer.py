# layer6_threat_intelligence/analyzer.py

import json
import requests

from layer4_agent.app.memory.sqlite_store import (
    get_conversation,
    get_report,
    get_connection
)

from layer6_threat_intelligence.schemas import (
    BehavioralProfile,
    CampaignMatch,
    ThreatIntelligence
)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2-uncensored"


# ==========================================================
# Campaign Matcher
# ==========================================================

def find_related_sessions(report):

    conn = get_connection()
    cursor = conn.cursor()

    linked_sessions = set()
    shared_artifacts = []

    entities = report.get("entities", {})

    search_items = (
        entities.get("upi_ids", [])
        + entities.get("phone_numbers", [])
        + entities.get("urls", [])
        + entities.get("account_numbers", [])
    )

    cursor.execute("""
        SELECT session_id, report_json
        FROM intelligence_reports
    """)

    rows = cursor.fetchall()

    for row in rows:

        report_text = row["report_json"]

        for artifact in search_items:

            if artifact and artifact in report_text:
                linked_sessions.add(row["session_id"])
                shared_artifacts.append(artifact)

    conn.close()

    return CampaignMatch(
        linked_sessions=list(linked_sessions),
        shared_artifacts=list(set(shared_artifacts))
    )


# ==========================================================
# Behavioral Analysis
# ==========================================================

def build_behavior_profile(conversation):

    urgency_words = [
        "urgent",
        "immediately",
        "hurry",
        "fast",
        "today",
        "now"
    ]

    authority_words = [
        "bank",
        "police",
        "officer",
        "government",
        "rbi",
        "manager",
        "customer care"
    ]

    scammer_messages = []

    for turn in conversation:

        sender = turn["sender"].lower()

        if sender not in [
            "agent",
            "honeypot",
            "margaret"
        ]:
            scammer_messages.append(turn)

    total = max(1, len(scammer_messages))

    urgency_hits = 0
    authority_hits = 0
    questions = 0
    skipped = 0

    for i, msg in enumerate(scammer_messages):

        text = msg["message"].lower()

        if any(word in text for word in urgency_words):
            urgency_hits += 1

        if any(word in text for word in authority_words):
            authority_hits += 1

        if "?" in text:

            questions += 1

            if i + 1 < len(scammer_messages):

                next_text = scammer_messages[i + 1]["message"]

                if "?" in next_text:
                    skipped += 1

    return BehavioralProfile(

        average_reply_gap=2.0,

        urgency_score=round(
            urgency_hits / total,
            2
        ),

        authority_score=round(
            authority_hits / total,
            2
        ),

        question_skip_rate=round(
            skipped / max(1, questions),
            2
        )
    )


# ==========================================================
# Ollama Threat Analyst
# ==========================================================

def llm_analysis(report):

    prompt = f"""
You are a cyber threat intelligence analyst.

Analyze this scam report.

Return ONLY valid JSON.

{{
    "summary":"Short analyst summary.",
    "recommendation":"Recommended SOC action."
}}

Report:

{json.dumps(report, indent=2)}
"""

    try:

        response = requests.post(

            OLLAMA_URL,

            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },

            timeout=60

        )

        raw = response.json()["response"]

        cleaned = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(cleaned)

    except Exception as e:

        print(
            f"[Layer6] Ollama failed -> {e}"
        )

        return {
            "summary":
            "Rule-based analysis only.",

            "recommendation":
            "Manual analyst review recommended."
        }


# ==========================================================
# Threat Score
# ==========================================================

def calculate_threat_score(

    p_scam,

    behavior,

    campaign

):

    score = 0

    score += p_scam * 50

    score += behavior.urgency_score * 15

    score += behavior.authority_score * 15

    score += behavior.question_skip_rate * 10

    score += min(
        len(campaign.linked_sessions),
        5
    ) * 2

    return round(
        min(score, 100),
        2
    )


# ==========================================================
# Main Layer 6 Pipeline
# ==========================================================

def run_layer6(session_id):

    report = get_report(session_id)

    if not report:

        return None

    conversation = get_conversation(
        session_id
    )

    campaign = find_related_sessions(
        report
    )

    behavior = build_behavior_profile(
        conversation
    )

    llm = llm_analysis(
        report
    )

    threat_score = calculate_threat_score(

        report["final_p_scam"],

        behavior,

        campaign

    )

    if threat_score >= 80:
        severity = "CRITICAL"

    elif threat_score >= 60:
        severity = "HIGH"

    elif threat_score >= 40:
        severity = "MEDIUM"

    else:
        severity = "LOW"

    final_report = ThreatIntelligence(

        session_id=session_id,

        threat_score=threat_score,

        severity=severity,

        campaign=campaign,

        behavioral_profile=behavior,

        llm_summary=llm["summary"],

        recommended_action=llm[
            "recommendation"
        ]

    )

    return final_report.dict()