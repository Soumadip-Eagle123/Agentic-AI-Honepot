from langchain_core.messages import HumanMessage
from app.orchestrator.fsm import compile_orchestrator_graph

def main():
    honeypot_graph = compile_orchestrator_graph()
    
    print("\n" + "="*20 + " FLIGHT TEST A: LOW PROBABILITY CHAT " + "="*20)
    safe_inputs = {
        "messages": [HumanMessage(content="Hello! Is this the customer care desk? I have a question.")],
        "scam_probability": 0.15 
    }
    output_a = honeypot_graph.invoke(safe_inputs)
    print(f"Final Graph Traffic State:\n{output_a['messages'][-1].content}")
    
    print("\n" + "="*20 + " FLIGHT TEST B: HIGH PROBABILITY ATTACK " + "="*20)
    scam_inputs = {
        "messages": [HumanMessage(content="Ma'am, why are you taking so long to open your banking app? Verification is mandatory right now!")],
        "scam_probability": 0.89
    }
    output_b = honeypot_graph.invoke(scam_inputs)
    print(f"Final Graph Traffic State:\n{output_b['messages'][-1].content}")

if __name__ == "__main__":
    main()