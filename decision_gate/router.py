"""
decision_gate/router.py
-----------------------
Layer 3 Overarching Controller. Unified to manage local LLaMA-3 pipelines.
"""
import os
import sys
import json
from dotenv import load_dotenv

# ── Dynamic Path & Environment Variable Configuration ─────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

for folder in ["ml_model", "layer4_agent", "layer5_intelligence", "layer6_threat_intelligence"]:
    dir_path = os.path.join(ROOT_DIR, folder)
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

sys.modules['app'] = __import__('layer4_agent.app', fromlist=['*'])

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Critical Error: TELEGRAM_BOT_TOKEN missing from root .env!")
# ──────────────────────────────────────────────────────────────────────────────

# ── Framework Imports (RUN CLEANLY AFTER SYS.PATH SETTINGS ARE ACTIVE) ────────
from ingress_layer.app import start_telegram_ingress_node
from layer4_agent.app.orchestrator.fsm import compile_orchestrator_graph
from layer4_agent.app.memory.short_term import ShortTermMemory
from layer4_agent.app_adapter import execute_layer4_cascade

# 🟢 FIXED: Moved import beneath system path configuration to stop ModuleNotFoundError
from layer4_agent.app.llm.prompts import HONEYPOT_SYSTEM_PROMPT

from layer5_intelligence.extractor import run_extraction
from layer6_threat_intelligence.analyzer import run_layer6

HONEYPOT_STATE_MACHINE = compile_orchestrator_graph()

async def evaluate_layer3_rules(raw_packet: dict) -> str:
    global HONEYPOT_STATE_MACHINE
    
    user_id = raw_packet["user_id"]
    text_content = raw_packet["text"]
    turns = raw_packet["turns"]
    p_scam_computed = raw_packet["ml_signals"]["scam_probability"]
    tactic = raw_packet["ml_signals"]["manipulation_strategy"]

    print(f"🔍 [LAYER 3 DEBUG] text='{text_content[:50]}' | p_scam={p_scam_computed} | turns={turns} | tactic={tactic}")
    
    memory_manager = ShortTermMemory(session_id=user_id, channel="telegram")
    memory_manager.add_turn(sender="scammer", message=text_content, p_scam=p_scam_computed)

    if turns <= 1 and p_scam_computed < 0.70:
        force_graph_score = 0.15  
    elif p_scam_computed >= 0.35:
        force_graph_score = 0.95  
    else:
        force_graph_score = p_scam_computed

    # 🟢 FIXED: Removed duplicate keys payload conflict override here
    layer4_input_context = {
        "user_id": user_id,
        "message_text": text_content,
        "scam_probability": force_graph_score,
        "system_prompt_template": HONEYPOT_SYSTEM_PROMPT,
        "current_persona": "Margaret",
        "turn_count": turns,
        "strategy_tactic": tactic
    }

    print(f"🔄 [LAYER 3] Rules evaluated. Handing native payload to Layer 4 Local LLaMA-3 machine...")
    final_persona_reply = execute_layer4_cascade(HONEYPOT_STATE_MACHINE, layer4_input_context)

    memory_manager.add_turn(sender="Margaret", message=final_persona_reply, p_scam=force_graph_score)

    if force_graph_score >= 0.70 and turns >= 3:
        print(f"\n🕵️‍♂️ [LAYER 5] Extracting Cybersecurity Intelligence Profile (Local LLaMA-3 Engine)...")
        l5_report = run_extraction(session_id=user_id, final_p_scam=p_scam_computed)
        
        print(f"🛡️ [LAYER 6] Correlating Local Vector Space Threat Campaign Profiles...")
        l6_threat_profile = run_layer6(session_id=user_id)
        
        print("👑 [SUCCESS] Final Cybersecurity Threat Profile Completed successfully:")
        print(json.dumps(l6_threat_profile, indent=2))
        print("="*80)

    return final_persona_reply

def run_honeypot_system():
    print("🧠 [SYSTEM STATUS] All 6 Layers Unified on Local LLaMA-3 Machine Framework.")
    print("🚀 Connecting Ingress Handlers to Telegram long-polling gateways...")
    start_telegram_ingress_node(BOT_TOKEN, evaluate_layer3_rules)

if __name__ == "__main__":
    run_honeypot_system()