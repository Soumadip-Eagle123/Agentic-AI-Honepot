# layer5_intelligence/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

SCHEMA_VERSION = "1.0"

class EntitiesSchema(BaseModel):
    phone_numbers: List[str] = []
    upi_ids: List[str] = []
    urls: List[str] = []
    bank_names: List[str] = []
    account_numbers: List[str] = []

class TimelineSchema(BaseModel):
    hook: Optional[str] = None
    trust_building: Optional[str] = None
    pressure: Optional[str] = None
    payment_attempt: Optional[str] = None

class IntelligenceReport(BaseModel):
    schema_version: str = SCHEMA_VERSION
    session_id: str
    timestamp: str
    scam_confirmed: bool
    final_p_scam: float
    entities: EntitiesSchema
    tactics: List[str] = []
    timeline: TimelineSchema
    conversation_turns: int
    agent_persona_used: str = "Margaret"
    raw_conversation: List[dict] = []