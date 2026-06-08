# 🕵️‍♂️ Agentic AI Honeypot: Autonomous Conversational Scam Baiting System

An advanced, multi-layered agentic defense framework engineered to intercept, identify, and actively neutralize financial scammers in real-time. Instead of acting as a static text filter, this system treats incoming malicious attacks as evolving narratives. It deploys an autonomous state-machine agent that traps fraudsters in stalling conversation loops, protects high-risk populations, enforces anti-prompt-injection walls, and extracts structured threat intelligence for security operation centers (SOC).

---

## 🏗️ 6-Layer System Architecture

The project is split into decoupled operational layers to ensure clean execution boundaries and high data throughput:

```
[Layer 1: Ingress (Telegram Polling)] ──> Captures message data & reply delay cycles
│
▼
[Layer 2: Scam Signal Engine (ML)]    ──> Extracts 22 engineered linguistic features
│
▼
[Layer 3: Decision Gate Router]       ──> Evaluates operational & financial cost thresholds
│
▼
[Layer 4: Agent Orchestrator]         ──> Drives state graph (LangGraph) & Persona loop
│
▼
[Layer 5: Scam Intel Extractor]       ──> Collects malicious entities (UPI, links, PII)
│
▼
[Layer 6: Threat Intel Analytics]     ──> Calculates risk profiles & correlates campaigns
```

- **Layer 1: Ingress Layer (`ingress_layer/`)** – The asynchronous gateway node connecting text channels. Tracks behavioral signals like metadata timestamps and response gaps (replies changing from milliseconds to seconds flag a shift from bots to manual human operators).
- **Layer 2: Scam Signal Engine (`ml_model/`)** – An ensemble model combining Logistic Regression, Random Forest, and calibrated Linear SVC. Combines sublinear TF-IDF vectorization with 22 hand-engineered features extracted via spaCy.
- **Layer 3: Decision Gate Router (`decision_gate/`)** – The overarching controller regulating token consumption and coordinating the operational rules between the signal engines and graph networks.
- **Layer 4: Agent Orchestrator (`layer4_agent/`)** – A state machine powered by `LangGraph` and `LangChain`. Manages persistent memory registers, tracks state edge transitions, and structures the ReAct loop handling the target persona profile.
- **Layer 5: Scam Intelligence Profile Extractor (`layer5_intelligence/`)** – An analytical entity-harvesting framework using spaCy NER structures and custom regex matchers to isolate malicious artifacts.
- **Layer 6: Threat Intelligence Correlation Engine (`layer6_threat_intelligence/`)** – A database cross-matching module that links matching bank records, URLs, or indicators to outline global active fraudulent campaigns.

---

## 🛠️ Prerequisites & Installation

### Core System Requirements

- Linux environment (tested extensively on Pop!_OS / Ubuntu)
- Python 3.9 or higher
- SQLite3
- Local Ollama instance or active API keys

### Step 1: Clone and Set Up Environment

```bash
git clone https://github.com/your-repo/Agentic-AI-Honeypot.git
cd Agentic-AI-Honeypot
```

Create and activate a virtual environment within the repository root directory (or specific sub-layers using explicit path lookups to avoid PEP 668 restrictions):

```bash
cd layer4_agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

### Step 2: Configure Environment Variables

Create a standard `.env` file inside the project root folder:

```env
# Telemetry Gateway Token
TELEGRAM_BOT_TOKEN="your_telegram_bot_api_token_here"

# External API Integrations (Optional)
GOOGLE_API_KEY="your_gemini_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
MISTRAL_API_KEY="your_mistral_api_key_here"
TAVILY_API_KEY="your_tavily_search_key_here"
```

---

## 🔌 Multi-Model & API Configuration Guide

The Layer 4 Agent Orchestrator is completely backend-agnostic. You can hot-swap between a fully offline architecture or high-availability external APIs by modifying `layer4_agent/app/llm/engine_factory.py`.

### 1. Local Models via Ollama (Default)

To configure local models like LLaMA-3, Mistral, or specialized uncensored models, point `ChatOllama` to your local engine instance:

```python
from langchain_ollama import ChatOllama

def initialize_base_model():
    return ChatOllama(
        model="llama3:8b",  # Or "llama2-uncensored", "mistral"
        temperature=0.3,
        num_predict=512,
        base_url="http://localhost:11434"
    )
```

### 2. Google Gemini API Integration

For highly deterministic response structuring using professional cloud execution windows:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def initialize_base_model():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,  # Complete determinism
        max_output_tokens=512,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
```

### 3. OpenAI API Integration

```python
from langchain_openai import ChatOpenAI
import os

def initialize_base_model():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=512,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
```

### 4. Mistral API Integration

```python
from langchain_mistralai import ChatMistralAI
import os

def initialize_base_model():
    return ChatMistralAI(
        model="mistral-large-latest",
        temperature=0.2,
        max_tokens=512,
        mistral_api_key=os.getenv("MISTRAL_API_KEY")
    )
```

---

## 🤖 Telegram Bot Configuration & Deployment Guide

### Step 1: Create Your Bot Entity via BotFather

1. Open your Telegram client and search for the official account: `@BotFather`.
2. Start a conversation and send the command: `/newbot`
3. Provide a descriptive name for your bot (e.g., `CyberSecurity_Guard_Bot`).
4. Set a unique handle ending with `_bot` (e.g., `Margaret_Honeypot_bot`).
5. Copy the generated HTTP API Access Token and add it to your `.env` file under `TELEGRAM_BOT_TOKEN`.

### Step 2: Initialize & Build the ML Signal Weights

Before starting the polling infrastructure, compile your linguistic training data to optimize feature matrices:

```bash
cd ../ml_model
python3 -X utf8 train.py --eval --cv 5
```

This stores your production classifier weights under `models/scam_detector.joblib` and prints classification health validation charts.

### Step 3: Launch the Integrated Operational Pipeline

Navigate to the decision gate and fire the overarching framework orchestrator:

```bash
cd ../decision_gate
python3 -X utf8 router.py
```

> **Production Safeguard:** `ingress_layer/app.py` is configured with a continuous background typing heartbeat event queue loop task. When a heavy local model processing block triggers a 40–50s inference delay window, the bot continuously fires a `ChatAction.TYPING` indicator down the Telegram socket every 4 seconds, keeping polling gateways open and preventing connection timeouts.

---

## 🛡️ Applied Hardening Features (Troubleshooting Log)

- **State Alignment Over Long Sockets** – Rewrote the front-door adapter loop processing engine inside `layer4_agent/app_adapter.py`. The interface dynamically queries historical multi-turn transaction rows sequentially from local SQLite tables via `get_conversation(user_id)`. This aggregates previous thread context before sending it to the model execution loops, completely preventing character breakdown bugs.

- **Compliance Verification Loop** – Modified the primary defensive audit code block inside `react_agent.py`. It inspects generated outputs for compliance leaks, automatically stripping phrases like `"Sure, I can transfer..."` or vocabulary markers like `"As an AI..."`, and replacing them with confused persona stall overrides before execution.

- **System Path Modularity** – Implemented relative path tracking and fallback logic mapping absolute parent roots (`ROOT_DIR`) into the base of `sys.path`. This clears `ModuleNotFoundError` anomalies across micro-service endpoints when modules initialize from custom workspace folders.

---

## 📊 Analytical Reporting & Testing

To trace intelligence extraction processes from active databases without calling the polling bot network, launch the localized web microservice:

```bash
cd ../layer5_intelligence
uvicorn api:app --reload --port 8005
```

You can run automated cURL scripts targeting the `/manual_turn` and `/extract` routes to mock adversarial artifact injections (e.g., `paying@paytm`, `http://fake-link.net`) and visualize the generated threat indicators on your diagnostic console.

---

## 🚀 Commit Your Changes

Run the following from the repository root to track your architectural milestone:

```bash
cd ~/Desktop/AI\ Engineering/Agentic-AI-Honeypot/
git add .
git commit -m "Architectural milestone: Fixed multi-turn state alignment, synchronized CSV lexicons, and established structural multi-model README configuration"
```