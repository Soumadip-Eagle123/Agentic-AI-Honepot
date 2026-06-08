# layer4_agent/app/orchestrator/fsm.py
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, HumanMessage
from app.orchestrator.state import HoneypotGraphState
from app.agent.react_agent import HoneypotAgent

from app.orchestrator.persona_manager import get_persona_summary

agent_core = HoneypotAgent()

def passive_observation_node(state: HoneypotGraphState):
    print("\n[GRAPH NODE]: Executing 'Passive Observation' State...")
    return {
        "messages": [AIMessage(content="[Ingress Log]: Monitoring conversational baseline metrics safely.")],
        "scam_probability": state.get("scam_probability", 0.0)
    }

def active_honeypot_node(state: HoneypotGraphState):
    print("\n[GRAPH NODE]: Routing to 'Active Honeypot Engagement' State!")

    last_human_message = [msg.content for msg in state["messages"] if isinstance(msg, HumanMessage)][-1]
    persona_name = state.get("current_persona", "Margaret")
    
    dynamic_instruction = get_persona_summary(persona_name)

    print(f"🧠 [NODE DEBUG]: Injecting full behavioral context tracking block into ReAct cycle.")

    agent_response_text = agent_core.run_query(
        initial_prompt=last_human_message,
        system_instruction_override=dynamic_instruction,
        max_turns=3
    )

    return {
        "messages": AIMessage(content=agent_response_text),
        "current_persona": persona_name
    }

def evaluate_scam_threshold_edge(state: HoneypotGraphState) -> str:
    score = state.get("scam_probability", 0.0)
    print(f"\n[CONDITIONAL EDGE]: Auditing Scam Probability Matrix -> Score: {score:.2f}")

    if score >= 0.70:
        print("[Edge Router Trigger]: Score crosses threshold! Deploying Honeypot Trap.")
        return "trigger_trap"

    print("[Edge Router Trigger]: Score is safe. Remaining in passive observation.")
    return "remain_passive"

def compile_orchestrator_graph():
    workflow = StateGraph(HoneypotGraphState)
    workflow.add_node("observation_state", passive_observation_node)
    workflow.add_node("honeypot_trap_state", active_honeypot_node)
    workflow.add_conditional_edges(
        START,
        evaluate_scam_threshold_edge,
        {
            "trigger_trap": "honeypot_trap_state",
            "remain_passive": "observation_state"
        }
    )
    workflow.add_edge("observation_state", END)
    workflow.add_edge("honeypot_trap_state", END)

    return workflow.compile()