"""
ml_model/pipeline.py
--------------------
Layer 2: Scam Signal Engine. Called exclusively by Layer 1.
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models.scam_detector import ScamDetector
from nlp.sentiment_analyzer import SentimentAnalyzer

DETECTOR = None
ANALYZER = None

def run_layer2_engine(text: str) -> dict:
    """Calculates scam probability and manipulation strategy via ML."""
    global DETECTOR, ANALYZER
    
    if DETECTOR is None or ANALYZER is None:
        model_path = os.path.join(CURRENT_DIR, "models", "scam_detector.joblib")
        DETECTOR = ScamDetector.load(model_path) if os.path.exists(model_path) else ScamDetector()
        if os.path.exists(model_path): DETECTOR._is_fitted = True
        ANALYZER = SentimentAnalyzer()

    if not DETECTOR._is_fitted:
        is_scam_heuristic = any(w in text.lower() for w in ["upi", "card", "bank", "money", "pay", "otp"])
        proba = 0.85 if is_scam_heuristic else 0.15
        det_res = {"label": "Scam" if is_scam_heuristic else "Legitimate", "confidence": proba, "is_scam": is_scam_heuristic, "risk_level": "HIGH" if is_scam_heuristic else "LOW"}
    else:
        det_res = DETECTOR.predict(text)
        
    sent_res = ANALYZER.analyze(text)
    
    return {
        "scam_probability": float(det_res["confidence"]),
        "is_scam": bool(det_res["is_scam"]),
        "risk_level": det_res.get("risk_level", "LOW"),
        "manipulation_strategy": sent_res["label"],
        "strategy_confidence": float(sent_res["confidence"])
    }