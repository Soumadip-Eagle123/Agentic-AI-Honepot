"""
layer4_agent/app_adapter.py
---------------------------
Layer 4 Front-Door Adapter. Enhanced to pull short-term SQLite history
to maintain narrative alignment boundaries over real-time communication sockets.
"""
from langchain_core.messages import HumanMessage, AIMessage
from layer4_agent.app.memory.sqlite_store import get_conversation

def execute_layer4_cascade(compiled_graph, raw_context_dict: dict) -> str:
    """
    Translates loose dictionary boundaries into a fully historically aligned 
    LangGraph state tracking primitive array list framework context window.
    """
    text = raw_context_dict["message_text"]
    score = raw_context_dict["scam_probability"]
    persona = raw_context_dict["current_persona"]
    user_id = raw_context_dict.get("user_id") 
    
    compiled_messages = []
    
    if user_id:
        db_history = get_conversation(str(user_id))
        
        for turn in db_history:
            if turn["sender"].lower() == "scammer":
                compiled_messages.append(HumanMessage(content=turn["message"]))
            else:
                compiled_messages.append(AIMessage(content=turn["message"]))
    if not compiled_messages:
        compiled_messages.append(HumanMessage(content=text))
    else:
        if compiled_messages[-1].content != text:
            compiled_messages.append(HumanMessage(content=text))

    print(f"⚙️ [LAYER 4 ADAPTER] Hydrated graph with {len(compiled_messages)} conversation history turns from SQLite.")

    graph_state_inputs = {
        "messages": compiled_messages,
        "scam_probability": score,
        "current_persona": persona
    }
    graph_output = compiled_graph.invoke(graph_state_inputs)

    final_reply_text = graph_output["messages"][-1].content
    return final_reply_text if hasattr(final_reply_text, 'content') else str(final_reply_text)