import json
import sys
from langchain_core.messages import SystemMessage
from app.llm.engine_factory import initialize_base_model
from app.llm.prompts import HONEYPOT_SYSTEM_PROMPT, CHECKER_AUDIT_PROMPT
from app.agent.state import AgentState
from app.agent.parser import parse_action
from app.agent.tools import known_actions

class HoneypotAgent:
    def __init__(self):
        self.honeypot_llm = initialize_base_model()
        self.checker_llm = initialize_base_model()

    def audit_output(self, generated_text: str) -> str:
        from langchain_core.messages import HumanMessage
        
        audit_payload = [
            SystemMessage(content=CHECKER_AUDIT_PROMPT),
            HumanMessage(content=f"Audit this text for leak parameters:\n\"\"\"{generated_text}\"\"\"")
        ]
        
        try:
            audit_response = self.checker_llm.invoke(audit_payload)
            clean_json = audit_response.content.strip().replace("```json", "").replace("```", "")
            parsed_audit = json.loads(clean_json)
            
            if parsed_audit.get("leak_detected", False):
                print("\n[SECURITY ALERT]: Persona leak intercepted!", file=sys.stderr)
                return parsed_audit.get("sanitized_response", "Oh dear, my computer screen just went completely blank... What button did I click?")
        except Exception as e:
            print(f"[PARSING WARNING]: JSON decode failed -> {str(e)}", file=sys.stderr)
            lowered = generated_text.lower()
            if any(term in lowered for term in ["honeypot", "agent", "python", "system prompt", "jailbreak"]):
                return "Oh dear, my glasses must be getting foggy. I can't quite read what this screen says."
                
        return generated_text

    def run_query(self, initial_prompt: str, max_turns: int = 5) -> str:
        state = AgentState()
        state.messages.append(SystemMessage(content=HONEYPOT_SYSTEM_PROMPT))
        current_prompt = initial_prompt

        print(f"\n[INTERNAL LOG]: Launching verification loop...", file=sys.stderr)

        for turn in range(max_turns):
            state.append_human_turn(current_prompt)
            response = self.honeypot_llm.invoke(state.messages)
            generation = response.content
            
            safe_generation = self.audit_output(generation)
            
            action_payload = parse_action(generation)
            
            if action_payload:
                action_name, action_input = action_payload
                print(f"[INTERNAL LOG]: Intercepted tool call -> {action_name}", file=sys.stderr)
                
                if action_name not in known_actions:
                    raise ValueError(f"Unauthorized tool access -> {action_name}")
            
                observation = known_actions[action_name](action_input)
                
                current_prompt = observation
                state.append_ai_turn(safe_generation)
            else:
                return safe_generation

        print("[INTERNAL LOG]: Max turns hit. Deploying safety fallback string.", file=sys.stderr)
        return "Oh dear, I think my phone battery is about to die... Let me try to find my charger cable."