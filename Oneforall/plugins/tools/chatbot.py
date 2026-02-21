import os
import aiohttp
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from Oneforall import app

# 🔐 Load from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

# 🧠 Store enabled chats (memory based)
CHATBOT_ENABLED = set()


# ==============================
# 🔘 TOGGLE COMMAND
# ==============================
@app.on_message(filters.command(["chatbot"]) & filters.group)
async def toggle_chatbot(client, message: Message):

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/chatbot on\n/chatbot off")

    # Only admins can toggle
    member = await app.get_chat_member(message.chat.id, message.from_user.id)

    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply_text("❌ Only admins can toggle chatbot.")

    action = message.command[1].lower()
    chat_id = message.chat.id

    if action == "on":
        CHATBOT_ENABLED.add(chat_id)
        await message.reply_text("🤖 Chatbot Enabled in this group.")
    elif action == "off":
        CHATBOT_ENABLED.discard(chat_id)
        await message.reply_text("🚫 Chatbot Disabled in this group.")
    else:
        await message.reply_text("Use:\n/chatbot on\n/chatbot off")


# ==============================
# 💬 GROUP AUTO REPLY
# ==============================
@app.on_message(filters.group & ~filters.command(["chatbot"]) & ~filters.via_bot & ~filters.forwarded)
async def group_chatbot(client, message: Message):

    chat_id = message.chat.id

    if chat_id not in CHATBOT_ENABLED:
        return

    if not message.text:
        return

    response = await generate_response(message.text)

    if response:
        await message.reply_text(response)


# ==============================
# 🔹 PRIVATE AUTO REPLY (Always ON)
# ==============================
@app.on_message(filters.private & ~filters.via_bot & ~filters.forwarded)
async def private_chatbot(client, message: Message):

    if not message.text:
        return

    response = await generate_response(message.text)

    if response:
        await message.reply_text(response)


# ==============================
# 🌐 OPENAI API FETCH (Direct HTTP)
# ==============================
async def generate_response(prompt: str):

    if not OPENAI_API_KEY:
        return "⚠️ OpenAI API key not set."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a fun and friendly music group assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 200,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENAI_API_URL, headers=headers, json=payload) as resp:
                data = await resp.json()

                if "choices" in data:
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return "⚠️ Error fetching response."

    except Exception as e:
        return f"⚠️ API Error: {e}"
