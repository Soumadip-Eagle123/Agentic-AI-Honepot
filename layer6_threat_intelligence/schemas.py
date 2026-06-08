# layer6_threat_intelligence/schemas.py

from pydantic import BaseModel
from typing import List


class BehavioralProfile(BaseModel):
    average_reply_gap: float = 0.0
    urgency_score: float = 0.0
    authority_score: float = 0.0
    question_skip_rate: float = 0.0


class CampaignMatch(BaseModel):
    linked_sessions: List[str] = []
    shared_artifacts: List[str] = []


class ThreatIntelligence(BaseModel):
    session_id: str

    threat_score: float

    severity: str

    campaign: CampaignMatch

    behavioral_profile: BehavioralProfile

    llm_summary: str

    recommended_action: str