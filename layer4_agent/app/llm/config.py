import os
from dotenv import load_dotenv
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
dotenv_path = os.path.join(ROOT_DIR, ".env")

load_dotenv(dotenv_path=dotenv_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(f"GOOGLE_API_KEY missing at targeted path: {dotenv_path}")
    
print("✅ [LAYER 4] Environment configuration verified and loaded successfully.")