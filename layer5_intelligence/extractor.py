# layer5_intelligence/extractor.py
import re
import json
import requests
from datetime import datetime
from typing import List

import spacy

from layer4_agent.app.memory.sqlite_store import get_conversation, save_report
from layer4_agent.app.orchestrator.persona_manager import get_active_persona_name
from layer5_intelligence.schemas import (
    IntelligenceReport, EntitiesSchema, TimelineSchema, SCHEMA_VERSION
)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    print("[Extractor]: spaCy model loaded.")
except OSError:
    raise OSError("spaCy model not found. Run: python -m spacy download en_core_web_sm")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# ─── Regex Patterns ───────────────────────────────────────────────────────────

PHONE_PATTERN = re.compile(
    r'(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,6}'
)
UPI_PATTERN = re.compile(r'[\w.\-]+@[\w]+')
URL_PATTERN = re.compile(
    r'(https?://|www\.)[^\s<>"\'()]+'
)
ACCOUNT_PATTERN = re.compile(r'\b\d{9,18}\b')

BANK_KEYWORDS = [
    "sbi", "hdfc", "icici", "axis", "kotak", "federal", "paytm",
    "phonepe", "gpay", "google pay", "upi", "neft", "imps", "bank"
]

TACTIC_PATTERNS = {
    "authority_impersonation": [
        "police", "officer", "bank official", "government", "rbi",
        "customer care", "support", "helpdesk", "manager"
    ],
    "fear_escalation": [
        "blocked", "suspended", "illegal", "arrest", "case filed",
        "locked", "penalty", "action", "consequences"
    ],
    "urgency": [
        "immediately", "right now", "urgent", "hurry", "fast",
        "deadline", "last chance", "act now", "today only"
    ],
    "financial_manipulation": [
        "upi", "transfer", "send money", "pay", "otp", "pin",
        "account number", "card number", "cvv"
    ],
    "trust_building": [
        "don't worry", "safe", "secure", "verified", "official",
        "just a formality", "routine"
    ]
}


# ─── Entity Extraction ────────────────────────────────────────────────────────

def extract_entities(conversation: List[dict]) -> EntitiesSchema:
    full_text = " ".join([t["message"] for t in conversation])

    phone_numbers = list(set(
        m.group() for m in PHONE_PATTERN.finditer(full_text)
        if len(m.group().replace(" ", "").replace("-", "")) >= 10
    ))
    upi_ids = list(set(m.group() for m in UPI_PATTERN.finditer(full_text)))
    urls = list(set(m.group() for m in URL_PATTERN.finditer(full_text)))
    account_numbers = list(set(m.group() for m in ACCOUNT_PATTERN.finditer(full_text)))

    # spaCy for bank names
    doc = nlp(full_text)
    bank_names = list(set(
        ent.text for ent in doc.ents
        if ent.label_ in ["ORG", "GPE"] and
        any(kw in ent.text.lower() for kw in BANK_KEYWORDS)
    ))

    # Fallback regex for bank keywords
    if not bank_names:
        bank_names = list(set(
            kw for kw in BANK_KEYWORDS
            if kw in full_text.lower()
        ))

    return EntitiesSchema(
        phone_numbers=phone_numbers,
        upi_ids=upi_ids,
        urls=urls,
        bank_names=bank_names,
        account_numbers=account_numbers
    )


# ─── Tactic Detection ─────────────────────────────────────────────────────────

def extract_tactics(conversation: List[dict]) -> List[str]:
    # Only scammer messages (not agent)
    scammer_text = " ".join([
        t["message"] for t in conversation
        if t["sender"].lower() not in ["margaret", "agent", "honeypot"]
    ]).lower()

    detected = []
    for tactic, keywords in TACTIC_PATTERNS.items():
        if any(kw in scammer_text for kw in keywords):
            detected.append(tactic)

    return detected


# ─── Timeline Reconstruction ──────────────────────────────────────────────────

def reconstruct_timeline(conversation: List[dict]) -> TimelineSchema:
    total = len(conversation)
    if total == 0:
        return TimelineSchema()

    scammer_turns = [
        t for t in conversation
        if t["sender"].lower() not in ["margaret", "agent", "honeypot"]
    ]

    if not scammer_turns:
        return TimelineSchema()

    n = len(scammer_turns)

    hook          = scammer_turns[0]["message"] if n >= 1 else None
    trust         = scammer_turns[1]["message"] if n >= 2 else None
    pressure      = scammer_turns[int(n * 0.6)]["message"] if n >= 3 else None
    payment       = scammer_turns[-1]["message"] if n >= 4 else None

    return TimelineSchema(
        hook=hook,
        trust_building=trust,
        pressure=pressure,
        payment_attempt=payment
    )


# ─── Ollama LLM Enrichment ────────────────────────────────────────────────────

def enrich_with_ollama(conversation: List[dict], entities: EntitiesSchema, tactics: List[str]) -> dict:
    conversation_text = "\n".join([
        f"{t['sender']}: {t['message']}" for t in conversation
    ])

    prompt = f"""
You are a scam intelligence analyst. Analyze this conversation and return ONLY a JSON object with these fields:
- "scam_type": one of [bank_fraud, upi_fraud, phishing, impersonation, other]
- "confidence_note": one sentence explaining why this is a scam
- "missed_entities": any phone numbers, UPI IDs, or URLs you spot that were missed
- "additional_tactics": any manipulation tactics not already listed: {tactics}

Conversation:
{conversation_text}

Return ONLY valid JSON. No explanation, no markdown.
"""

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=60)

        raw = response.json().get("response", "{}")
        clean = raw.strip().replace("```json", "").replace("```", "")
        return json.loads(clean)

    except Exception as e:
        print(f"[Extractor]: Ollama call failed -> {e}")
        return {
            "scam_type": "unknown",
            "confidence_note": "LLM unavailable — rule-based extraction only",
            "missed_entities": [],
            "additional_tactics": []
        }


# ─── Main Extraction Function ─────────────────────────────────────────────────

def run_extraction(session_id: str, final_p_scam: float) -> dict:
    print(f"\n[Layer 5]: Starting intelligence extraction for session -> {session_id}")

    conversation = get_conversation(session_id)

    if not conversation:
        print(f"[Layer 5]: No conversation found for session {session_id}")
        return {}

    entities  = extract_entities(conversation)
    tactics   = extract_tactics(conversation)
    timeline  = reconstruct_timeline(conversation)
    llm_data  = enrich_with_ollama(conversation, entities, tactics)

    # Merge any additional tactics from LLM
    all_tactics = list(set(tactics + llm_data.get("additional_tactics", [])))

    report = IntelligenceReport(
        session_id=session_id,
        timestamp=datetime.now().isoformat(),
        scam_confirmed=final_p_scam >= 0.70,
        final_p_scam=final_p_scam,
        entities=entities,
        tactics=all_tactics,
        timeline=timeline,
        conversation_turns=len(conversation),
        agent_persona_used=get_active_persona_name(),
        raw_conversation=[
            {"sender": t["sender"], "message": t["message"], "timestamp": t["timestamp"]}
            for t in conversation
        ]
    )

    report_dict = report.dict()
    report_dict["scam_type"]       = llm_data.get("scam_type", "unknown")
    report_dict["confidence_note"] = llm_data.get("confidence_note", "")

    save_report(session_id, report_dict)
    print(f"[Layer 5]: Extraction complete. Report saved for session {session_id}")

    return report_dict