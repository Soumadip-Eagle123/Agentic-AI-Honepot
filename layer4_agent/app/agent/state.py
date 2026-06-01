from langchain_core.messages import HumanMessage, AIMessage

class AgentState:
    def __init__(self):
        self.messages = []

    def append_human_turn(self, content: str):
        self.messages.append(HumanMessage(content=content))

    def append_ai_turn(self, content: str):
        self.messages.append(AIMessage(content=content))