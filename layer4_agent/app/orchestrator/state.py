
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class HoneypotGraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    scam_probability: float
    current_persona: str