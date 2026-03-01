from Tune import app
from pyrogram import filters
from collections import defaultdict
from datetime import datetime, timedelta

flood_data = defaultdict(list)
warns_data = defaultdict(int)

@app.on_message(filters.group & ~filters.me & filters.text)
async def anti_flood(client, message):
    chat_id = message.chat.id
    settings = await welcome_db.find_one({"chat_id": chat_id})  # Reuse DB
    if not settings.get("antispam", True): return
    
    user_id = message.from_user.id
    now = datetime.now()
    
    # Flood check (5 msgs per minute)
    flood_data[user_id].append(now)
    flood_data[user_id] = [t for t in flood_data[user_id] if now - t < timedelta(minutes=1)]
    
    if len(flood_data[user_id]) > settings.get("flood_limit", 5):
        warns_data[user_id] += 1
        await message.delete()
        
        if warns_data[user_id] >= settings.get("warns_max", 3):
            await client.ban_chat_member(chat_id, user_id)
            warns_data[user_id] = 0
            await client.send_message(chat_id, f"🚫 **{message.from_user.mention} banned** for flooding!")
