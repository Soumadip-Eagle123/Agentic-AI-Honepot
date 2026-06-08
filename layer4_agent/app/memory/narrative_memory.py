
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_tavily import TavlySearchResults
import os

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

PERSONA_KNOWLEDGE_BASE = [
    Document(page_content="Margaret's bank is 'Federal Security Bank'. Account Number: 994821034.", metadata={"source": "sqlite_layer5"}),
    Document(page_content="Margaret lives in a quiet suburban neighborhood on Oak Street. Her phone is a very old flip phone.", metadata={"source": "sqlite_layer5"}),
    Document(page_content="Margaret's grandson is named Tommy. He is 19 years old and helps her fix the television.", metadata={"source": "sqlite_layer5"})
]

local_vector_db = FAISS.from_documents(PERSONA_KNOWLEDGE_BASE, embeddings_model)

tavly_search_client = TavlySearchResults(max_results=2)

def fetch_synchronized_context(user_query: str) -> str:
    """
    Executes an explicit Fallback Execution Chain combining local SQLite/FAISS vectors 
    with live external web lookups based on semantic alignment constraints.
    """
    print(f"\n[Layer 4 Memory Gateway]: Scanning knowledge layers for -> '{user_query}'")
    
    docs_with_scores = local_vector_db.similarity_search_with_score(user_query, k=1)
    
    if docs_with_scores:
        matched_doc, distance_score = docs_with_scores[0]
        print(f"[Vector Space Analysis]: Nearest match distance score = {distance_score:.4f}")
        
        if distance_score <= 0.60:
            print("[Precedence Match Found]: Local SQLite fact match verified. Enforcing internal precedence.")
            return f"CRITICAL CONTEXT (INTERNAL PRECEDENCE DATA):\n{matched_doc.page_content}"
            
    print("[FALLBACK GATEWAY ENGAGED]: Local confidence threshold insufficient. Querying live web search client...")
    try:
        web_search_payload = tavly_search_client.invoke({"query": user_query})
        compiled_web_facts = "\n".join([item.get("content", "") for item in web_search_payload])
        return f"CONTEXT (LIVE WEB FALLBACK DATA):\n{compiled_web_facts}"
    except Exception as e:
        print(f"[MEMORY GATEWAY EXCEPTION]: External client failed safely -> {str(e)}")
        return "CONTEXT: No additional verified data available."