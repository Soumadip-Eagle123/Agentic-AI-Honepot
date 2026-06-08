"""
ingress_layer/app.py
--------------------
Layer 1: Telegram Ingress Layer (Async Loop Handler)
Hardened with an explicit Typing Heartbeat loop to survive heavy local LLM processing delays.
"""
import os
import sys
import time
import logging
import json
import asyncio 
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction   

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ml_model.pipeline import run_layer2_engine

_LAYER3_CALLBACK_ROUTER = None
SESSION_TELEMETRY = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    SESSION_TELEMETRY[user_id] = {"turns": 0, "time_gaps": [], "last_message_time": time.time()}
    await update.message.reply_text("Hello? Who is this?")

async def send_typing_heartbeat(bot, chat_id, stop_event):
    """Keeps the Telegram gateway open by sending a typing flag every 4 seconds."""
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)
    except Exception as e:
        print(f"⚠️ [HEARTBEAT WARNING]: Typing indicator exception caught -> {e}")

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _LAYER3_CALLBACK_ROUTER
    message = update.message
    if not message or not message.text:
        print("📥 [LAYER 1] Ignoring non-text event (sticker/photo/etc)...")
        return
    user_id = message.from_user.id
    text = message.text
    provided_time = time.time()

    if user_id not in SESSION_TELEMETRY:
        SESSION_TELEMETRY[user_id] = {"turns": 0, "time_gaps": [], "last_message_time": provided_time}

    session = SESSION_TELEMETRY[user_id]
    session["turns"] += 1

    time_gap = provided_time - session["last_message_time"]
    if session["turns"] > 1:
        session["time_gaps"].append(round(time_gap, 2))
    session["last_message_time"] = provided_time

    print(f"\n📥 [LAYER 1] Live Telegram Event from {user_id}. Running Layer 2 ML Model...")
    ml_signals = run_layer2_engine(text)

    raw_telemetry_packet = {
        "user_id": str(user_id),
        "text": text,
        "turns": session["turns"],
        "time_gaps": session["time_gaps"],
        "last_delta_t": round(time_gap, 2),
        "ml_signals": ml_signals
    }
    print(f"DEBUG [LAYER 1]: Built packet keys: {list(raw_telemetry_packet.keys())}")
    
    if _LAYER3_CALLBACK_ROUTER:
        print(f"🔄 [LAYER 1] Data packaged. Handing off to Layer 3 router...")
        
        stop_heartbeat = asyncio.Event()
        heartbeat_task = asyncio.create_task(
            send_typing_heartbeat(context.bot, message.chat_id, stop_heartbeat)
        )
        
        try:
            fresh_agent_response = await _LAYER3_CALLBACK_ROUTER(raw_telemetry_packet)
        finally:
            stop_heartbeat.set()
            await heartbeat_task

        print(f"👑 [LAYER 3 COMPLETED] Reply generated.")
        await message.reply_text(str(fresh_agent_response), parse_mode=None)
    else:
        await message.reply_text("Understood.")

def start_telegram_ingress_node(token: str, layer3_router_func):
    global _LAYER3_CALLBACK_ROUTER
    _LAYER3_CALLBACK_ROUTER = layer3_router_func
    
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_incoming_message))
    application.run_polling()
