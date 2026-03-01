# Tune/plugins/handler/welcome/editor.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import filters
from datetime import datetime
from Tune import app
from Tune.utils.database import mongodb

welcome_db = mongodb["welcome_settings"]

# ᴀᴅᴍɪɴ-ᴏɴʟʏ ʟᴏᴄᴋ
async def admin_welcome_lock(client, entity):
    """sᴛʀɪᴄᴛ ᴀᴅᴍɪɴ ᴄʜᴇᴄᴋ"""
    user_id = entity.from_user.id if hasattr(entity, 'from_user') else entity.message.from_user.id
    chat_id = entity.chat.id if hasattr(entity, 'chat') else entity.message.chat.id
    
    try:
        from Tune.core.misc import sudo
        if user_id in await sudo():
            return True
    except:
        pass
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ᴍᴇɴᴜs
WELCOME_TYPES = InlineKeyboardMarkup([
    [InlineKeyboardButton("📝 ᴛᴇxᴛ", callback_data="wtype_text")],
    [InlineKeyboardButton("📷 ᴘʜᴏᴛᴏ", callback_data="wtype_photo")],
    [InlineKeyboardButton("📹 ᴠɪᴅᴇᴏ", callback_data="wtype_video")],
    [InlineKeyboardButton("🎵 ᴠᴏɪᴄᴇ", callback_data="wtype_voice")],
    [InlineKeyboardButton("🧵 ᴛᴏᴘɪᴄs", callback_data="wtype_topic")],
    [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="h_welcome")]
])

STATUS_TOGGLE = InlineKeyboardMarkup([
    [InlineKeyboardButton("⏹️ sᴛᴀᴛᴜs", callback_data="wstatus_toggle")],
    [InlineKeyboardButton("✏️ ᴄᴜsᴛᴏᴍ ᴍsɢ", callback_data="wedit_msg")],
    [InlineKeyboardButton("📎 ᴍᴇᴅɪᴀ", callback_data="wmedia_type")],
    [InlineKeyboardButton("💬 ᴛᴏᴘɪᴄs", callback_data="wtopics")],
    [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="h_welcome")]
])

@app.on_callback_query(filters.regex(r"^h_welcome_config"))
async def welcome_config(client, callback: CallbackQuery):
    if not await admin_welcome_lock(client, callback):
        await callback.answer("🔒 **ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    data = await welcome_db.find_one({"chat_id": callback.message.chat.id}) or {}
    status = "✅ ᴏɴ" if data.get("status", True) else "⏹️ ᴏғғ"
    wtype = data.get("type", "text").upper()
    
    await callback.edit_message_text(
        f"""📢 **ᴡᴇʟᴄᴏᴍᴇ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ**

sᴛᴀᴛᴜs: {status}
ᴛʏᴘᴇ: {wtype}
ᴍᴇᴍʙᴇʀs ɢʀᴇᴇᴛᴇᴅ: {data.get('count', 0)}""",
        reply_markup=STATUS_TOGGLE
    )

@app.on_callback_query(filters.regex(r"^wstatus_toggle"))
async def toggle_welcome(client, callback):
    if not await admin_welcome_lock(client, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    data = await welcome_db.find_one({"chat_id": chat_id}) or {}
    data["status"] = not data.get("status", True)
    
    await welcome_db.update_one(
        {"chat_id": chat_id}, 
        {"$set": data}, 
        upsert=True
    )
    
    status = "✅ ᴇɴᴀʙʟᴇᴅ" if data["status"] else "❌ ᴅɪsᴀʙʟᴇᴅ"
    await callback.answer(f"ᴡᴇʟᴄᴏᴍᴇ {status}!", show_alert=True)
    await welcome_config(client, callback)

@app.on_callback_query(filters.regex(r"^wmedia_type"))
async def media_types(client, callback):
    if not await admin_welcome_lock(client, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    await callback.edit_message_text(
        "📎 **sᴇʟᴇᴄᴛ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇᴅɪᴀ ᴛʏᴘᴇ**",
        reply_markup=WELCOME_TYPES
    )

@app.on_callback_query(filters.regex(r"^wtype_(text|photo|video|voice|topic)"))
async def set_type(client, callback):
    if not await admin_welcome_lock(client, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    wtype = callback.data.split("_")[-1]
    
    await welcome_db.update_one(
        {"chat_id": chat_id}, 
        {"$set": {"type": wtype}}, 
        upsert=True
    )
    await callback.answer(f"✅ sᴇᴛ ᴛᴏ {wtype.upper()}", show_alert=True)
    await welcome_config(client, callback)

# ᴄᴜsᴛᴏᴍ ᴍsɢ ᴇᴅɪᴛᴏʀ
welcome_edit_state = {}

@app.on_callback_query(filters.regex(r"^wedit_msg"))
async def edit_welcome_msg(client, callback):
    if not await admin_welcome_lock(client, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    welcome_edit_state[user_id] = chat_id
    
    await callback.edit_message_text(
        """✏️ **ᴄᴜsᴛᴏᴍ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ**
ᴜsᴇ ʜᴛᴍʟ ᴀɴᴅ ᴄᴏɴғɪɢᴜʀᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ's ᴍᴇssᴀɢᴇ ʙᴀʙᴇs❤️‍🩹

**ᴀᴠᴀɪʟᴀʙʟᴇ ᴠᴀʀɪᴀʙʟᴇs:**
• `{ID}` = ᴜsᴇʀ ɪᴅ
• `{NAME}` = ᴜsᴇʀ ɴᴀᴍᴇ
• `{SURNAME}` = ᴜsᴇʀ sᴜʀɴᴀᴍᴇ
• `{NAMESURNAME}` = ɴᴀᴍᴇ + sᴜʀɴᴀᴍᴇ
• `{LANG}` = ᴜsᴇʀ ʟᴀɴɢᴜᴀɢᴇ
• `{DATE}` = ᴄᴜʀʀᴇɴᴛ ᴅᴀᴛᴇ
• `{TIME}` = ᴄᴜʀʀᴇɴᴛ ᴛɪᴍᴇ
• `{WEEKDAY}` = ᴡᴇᴇᴋ ᴅᴀʏ
• `{MENTION}` = ʟɪɴᴋ ᴛᴏ ᴜsᴇʀ
• `{USERNAME}` = ᴜsᴇʀɴᴀᴍᴇ
• `{GROUPNAME}` = ɢʀᴏᴜᴘ ɴᴀᴍᴇ
• `{RULES}` = ɢʀᴏᴜᴘ ʀᴜʟᴇs

**ʀᴇᴘʟʏ ᴛᴏ ᴛʜɪs ᴡɪᴛʜ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ᴛᴇxᴛ:**""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 sʏɴᴛᴀx ʜᴇʟᴘ", callback_data="whelp_syntax")],
            [InlineKeyboardButton("✅ ᴘʀᴇᴠɪᴇᴡ", callback_data="wpreview_msg")],
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="h_welcome_config")]
        ])
    )

@app.on_message(filters.reply & filters.text & filters.group)
async def save_welcome_msg(client, message):
    user_id = message.from_user.id
    
    if user_id not in welcome_edit_state:
        return
    
    if not await admin_welcome_lock(client, message):
        await message.reply("🔒 **ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴏɴʟʏ!**")
        return
    
    chat_id = welcome_edit_state.pop(user_id)
    custom_msg = message.text
    
    await welcome_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"msg": custom_msg}},
        upsert=True
    )
    await message.reply("✅ **ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ sᴀᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**")

# ᴡᴇʟᴄᴏᴍᴇ ᴛʀɪɢɢᴇʀ (ɴᴇᴡ ᴍᴇᴍʙᴇʀs)
@app.on_message(filters.new_chat_members & filters.group)
async def auto_welcome(client, message):
    chat_id = message.chat.id
    data = await welcome_db.find_one({"chat_id": chat_id})
    
    if not data or not data.get("status", False):
        return
    
    for user in message.new_chat_members:
        # ɢᴇᴛ ᴄᴜsᴛᴏᴍ ᴍsɢ ᴏʀ ᴅᴇғᴀᴜʟᴛ
        msg = data.get("msg", "ᴡᴇʟᴄᴏᴍᴇ {MENTION} ᴛᴏ {GROUPNAME}!")
        
        # ʀᴇᴘʟᴀᴄᴇ ᴠᴀʀɪᴀʙʟᴇs
        now = datetime.now()
        msg = msg.format(
            ID=user.id,
            NAME=user.first_name or "",
            SURNAME=user.last_name or "",
            NAMESURNAME=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            LANG=user.language_code or "ᴜɴᴋɴᴏᴡɴ",
            DATE=now.strftime("%Y-%m-%d"),
            TIME=now.strftime("%H:%M:%S"),
            WEEKDAY=now.strftime("%A"),
            MENTION=user.mention,
            USERNAME=f"@{user.username}" if user.username else "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ",
            GROUPNAME=message.chat.title,
            RULES="ᴄʜᴇᴄᴋ ᴘɪɴɴᴇᴅ"  # ᴄᴀɴ ғᴇᴛᴄʜ ғʀᴏᴍ ᴅʙ
        )
        
        # sᴇɴᴅ ʙᴀsᴇᴅ ᴏɴ ᴛʏᴘᴇ
        wtype = data.get("type", "text")
        if wtype == "text":
            await message.reply_text(msg)
        elif wtype == "photo":
            photo_url = data.get("media_url", "https://telegra.ph/file/welcome.jpg")
            await client.send_photo(chat_id, photo_url, caption=msg)
        elif wtype == "video":
            video_url = data.get("media_url", "https://telegra.ph/file/welcome.mp4")
            await client.send_video(chat_id, video_url, caption=msg)
        
        # ɪɴᴄʀᴇᴍᴇɴᴛ ᴄᴏᴜɴᴛ
        await welcome_db.update_one(
            {"chat_id": chat_id},
            {"$inc": {"count": 1}}
        )

print("✅ ᴡᴇʟᴄᴏᴍᴇ ᴇᴅɪᴛᴏʀ ʟᴏᴀᴅᴇᴅ!")
