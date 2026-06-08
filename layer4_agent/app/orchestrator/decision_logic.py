# layer4_agent/app/orchestrator/decision_logic.py

OBSERVE_THRESHOLD = 0.30
SUSPECT_THRESHOLD = 0.70
EXTRACT_THRESHOLD = 0.70

def get_decision_stage(p_scam: float) -> str:
    """
    Returns the current stage based on scam probability.
    
    Stages:
      observe  → p_scam < 0.30  : just watch, do nothing
      suspect  → 0.30 to 0.70   : mild engagement, keep monitoring
      engage   → p_scam >= 0.70 : activate honeypot agent
      extract  → p_scam >= 0.70 : trigger Layer 5 intelligence extraction
    """
    if p_scam < OBSERVE_THRESHOLD:
        return "observe"
    elif p_scam < SUSPECT_THRESHOLD:
        return "suspect"
    else:
        return "engage"

def should_extract_intelligence(p_scam: float, turn_count: int) -> bool:
    """
    Decides whether to trigger Layer 5 intelligence extraction.
    
    Conditions:
    - Scam probability must cross the extraction threshold
    - At least 3 turns must have happened (avoid extracting too early)
    """
    return p_scam >= EXTRACT_THRESHOLD and turn_count >= 3

def should_activate_honeypot(p_scam: float) -> bool:
    """
    Decides whether to activate the honeypot agent.
    Mirrors the FSM condition in fsm.py.
    """
    return p_scam >= SUSPECT_THRESHOLD

def get_full_decision(p_scam: float, turn_count: int) -> dict:
    """
    Returns a full decision summary for logging and routing.
    """
    stage = get_decision_stage(p_scam)
    activate = should_activate_honeypot(p_scam)
    extract = should_extract_intelligence(p_scam, turn_count)

    print(f"[DecisionLogic]: p_scam={p_scam:.2f} | stage={stage} | activate={activate} | extract={extract}")

    return {
        "stage": stage,
        "activate_honeypot": activate,
        "trigger_extraction": extract,
        "p_scam": p_scam,
        "turn_count": turn_count
    }