from langchain_google_genai import ChatGoogleGenerativeAI
from app.llm.config import GOOGLE_API_KEY

def initialize_base_model():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        max_output_tokens=512
    )
    return llm
