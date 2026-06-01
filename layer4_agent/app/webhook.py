from fastapi import FastAPI, Form, Response
from app.orchestrator.fsm import compile_orchestrator_graph
from langchain_core.messages import HumanMessage

app = FastAPI()

honeypot_workflow = compile_orchestrator_graph()

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    scammer_message = Body
    print(f"\n[INBOUND WHATSAPP]: Message received from {From} -> '{scammer_message}'")
    
    graph_inputs = {
        "messages": [HumanMessage(content=scammer_message)],
        "scam_probability": 0.95 
    }
    
    graph_output = honeypot_workflow.invoke(graph_inputs)
    
    final_persona_reply = graph_output["messages"][-1].content
    
    twiml_response = (
        f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        f"<Response>"
        f"<Message>{final_persona_reply}</Message>"
        f"</Response>"
    )
    
    return Response(content=twiml_response, media_type="application/xml")