# layer7_api_ui/pii_masker.py
import re
import sys
import os

# Ensure import paths resolve from root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from layer4_agent.app.orchestrator.persona_manager import get_persona
except ImportError:
    # Fallback if import fails
    def get_persona(name="Margaret"):
        return {
            "name": "Margaret",
            "bank": "Federal Security Bank",
            "account_number": "994821034",
            "location": "Oak Street, suburban neighborhood",
            "grandson": "Tommy, 19 years old"
        }

# Generic Regex Patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b') # 13 to 16 digit cards

class PIIMasker:
    def __init__(self, persona_name="Margaret"):
        self.persona_name = persona_name
        self.persona = get_persona(persona_name)
        
        # Build compile patterns for specific victim persona keywords
        self.victim_keywords = {}
        
        # Add basic persona details
        if "name" in self.persona:
            self.victim_keywords["name"] = (re.compile(re.escape(self.persona["name"]), re.IGNORECASE), "[MASKED_VICTIM_NAME]")
            
        if "bank" in self.persona:
            self.victim_keywords["bank"] = (re.compile(re.escape(self.persona["bank"]), re.IGNORECASE), "[MASKED_VICTIM_BANK]")
            # Also mask partial matches like "Federal Security"
            partial_bank = self.persona["bank"].replace("Bank", "").strip()
            if len(partial_bank) > 3:
                self.victim_keywords["bank_partial"] = (re.compile(re.escape(partial_bank), re.IGNORECASE), "[MASKED_VICTIM_BANK]")
                
        if "account_number" in self.persona:
            self.victim_keywords["account"] = (re.compile(re.escape(self.persona["account_number"])), "[MASKED_VICTIM_ACCOUNT]")
            
        if "location" in self.persona:
            # Oak Street, etc.
            street = self.persona["location"].split(",")[0].strip()
            self.victim_keywords["location"] = (re.compile(re.escape(street), re.IGNORECASE), "[MASKED_VICTIM_ADDRESS]")
            
        if "grandson" in self.persona:
            # Tommy
            grandson_name = self.persona["grandson"].split(",")[0].strip()
            self.victim_keywords["grandson"] = (re.compile(re.escape(grandson_name), re.IGNORECASE), "[MASKED_VICTIM_RELATION_NAME]")

    def mask_text(self, text: str, role: str) -> str:
        """Masks PII within a text string based on the user's role."""
        if not text:
            return text
            
        role = role.lower()
        
        # Developer mode does not perform redaction in text, rather it flags details.
        # But for normal views (SOC, LE), we always redact victim PII.
        if role == "developer":
            # Developer sees original text but we will highlight it in UI.
            return text
            
        masked = text
        
        # 1. Mask email addresses
        masked = EMAIL_PATTERN.sub("[MASKED_EMAIL]", masked)
        
        # 2. Mask credit cards
        masked = CARD_PATTERN.sub("[MASKED_CARD]", masked)
        
        # 3. Mask victim specific keywords
        for key, (pattern, replacement) in self.victim_keywords.items():
            masked = pattern.sub(replacement, masked)
            
        # 4. General phone number masking (if it's associated with the victim/honeypot)
        # Note: Scammer phone numbers should NOT be masked for Law Enforcement!
        # If the sender is Margaret, or if the text is talking about Margaret's number, we mask.
        # Otherwise, if the role is SOC, we can mask general phone numbers except known IOCs,
        # but let's keep it simple: if the role is SOC, we redact general phone numbers unless they're scammer's.
        return masked

    def mask_conversation(self, turns: list, role: str) -> list:
        """Processes conversation turns and masks PII dynamically based on the role."""
        masked_turns = []
        for turn in turns:
            sender = turn.get("sender", "")
            message = turn.get("message", "")
            p_scam = turn.get("p_scam", 0.0)
            
            # Identify message direction
            is_victim = sender.lower() in ["margaret", "agent", "honeypot"]
            
            masked_message = message
            
            if role.lower() != "developer":
                # Redact PII in victim's messages
                if is_victim:
                    masked_message = self.mask_text(message, role)
                else:
                    # For scammer's messages, mask any victim references (e.g. "Is this Margaret?")
                    # But keep scammer UPI, scammer bank, scammer numbers unmasked for analysis
                    masked_message = self.mask_text(message, role)
                    
            masked_turns.append({
                "id": turn.get("id"),
                "turn_number": turn.get("turn_number"),
                "sender": "Margaret (Honeypot)" if is_victim else "Scammer",
                "original_sender": sender,
                "message": masked_message,
                "raw_message": message, # Kept for Developer audit side-by-side
                "timestamp": turn.get("timestamp"),
                "p_scam": p_scam,
                "channel": turn.get("channel", "telegram")
            })
        return masked_turns

    def mask_report(self, report: dict, role: str) -> dict:
        """Masks PII inside the intelligence report structure."""
        if not report:
            return report
            
        role = role.lower()
        masked_report = dict(report)
        
        # Entities extraction masking
        entities = dict(report.get("entities", {}))
        masked_entities = {
            "phone_numbers": list(entities.get("phone_numbers", [])),
            "upi_ids": list(entities.get("upi_ids", [])),
            "urls": list(entities.get("urls", [])),
            "bank_names": list(entities.get("bank_names", [])),
            "account_numbers": list(entities.get("account_numbers", []))
        }
        
        # If not developer, strip out victim entities
        if role != "developer":
            # Strip out Margaret's bank and account from extracted threat actor entities
            victim_bank = self.persona.get("bank", "").lower()
            victim_account = self.persona.get("account_number", "")
            
            masked_entities["bank_names"] = [
                b for b in masked_entities["bank_names"]
                if victim_bank not in b.lower()
            ]
            masked_entities["account_numbers"] = [
                a for a in masked_entities["account_numbers"]
                if a != victim_account
            ]
            
            # Mask timelines and summaries
            timeline = dict(report.get("timeline", {}))
            masked_timeline = {}
            for stage, text in timeline.items():
                if text:
                    masked_timeline[stage] = self.mask_text(text, role)
                else:
                    masked_timeline[stage] = None
                    
            masked_report["timeline"] = masked_timeline
            
            if "confidence_note" in masked_report:
                masked_report["confidence_note"] = self.mask_text(masked_report["confidence_note"], role)
                
            # If SOC, mask scammer details partially to show they are threat intelligence
            # but preserve them fully for law_enforcement.
            if role == "soc":
                # SOC sees masked scammer details partially for dashboard (e.g. +91 987***3210 or f*****@paytm)
                # This shows privacy safety inside the dashboard.
                masked_entities["phone_numbers"] = [
                    self._obfuscate_value(p) for p in masked_entities["phone_numbers"]
                ]
                masked_entities["upi_ids"] = [
                    self._obfuscate_value(u) for u in masked_entities["upi_ids"]
                ]
                masked_entities["account_numbers"] = [
                    self._obfuscate_value(a) for a in masked_entities["account_numbers"]
                ]
                
        masked_report["entities"] = masked_entities
        
        # Clean the raw conversation embedded in report
        if "raw_conversation" in masked_report:
            masked_report["raw_conversation"] = self.mask_conversation(
                masked_report["raw_conversation"], role
            )
            
        return masked_report

    def _obfuscate_value(self, val: str) -> str:
        """Helper to partially obfuscate scammer artifacts for general SOC dashboards."""
        if not val:
            return val
        if "@" in val: # UPI or email
            parts = val.split("@")
            username = parts[0]
            domain = parts[1]
            if len(username) <= 3:
                masked_user = "***"
            else:
                masked_user = username[:2] + "***" + username[-1]
            return f"{masked_user}@{domain}"
        else: # Phone or Account number
            clean_val = val.replace(" ", "").replace("-", "")
            if len(clean_val) <= 4:
                return "****"
            return val[:3] + "***" + val[-3:]
