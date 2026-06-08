"""
layer4_agent/app/llm/engine_factory.py
--------------------------------------
"""
from langchain_ollama import ChatOllama

def initialize_base_model():
    """Initializes a completely local Ollama instance running LLaMA-3."""
    llm = ChatOllama(
        model="llama2-uncensored",
        temperature=0.7,  
        num_predict=512,      
        base_url="http://localhost:11434"
    )
    return llm
