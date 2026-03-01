# Tune/plugins/handler/tagalert.py
import asyncio
from pyrogram.types import CallbackQuery
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid
from datetime import datetime
from Tune import app, LOGGER
from Tune.utils.database import mongodb

tagalert_db = mongodb["tagalert_users"]

# ᴛᴀɢ ᴘᴀᴛᴛᴇʀɴs
TAG_PATTERNS = [
    r"@[A-Za-z0-9_]{5,32}",  # ᴜsᴇʀɴᴀᴍᴇs
    r"[([^]]+)]",  # ᴍᴇɴᴛɪᴏɴs
    r"(?i)(id|ᴜɪᴅ):? ?(d+)",  # ᴜsᴇʀ ɪᴅs
]

async def is_tagalert_enabled(user_id: int) -> bool:
    """ᴄʜᴇᴄᴋ ɪғ ᴜsᴇʀ ʜᴀs ᴛᴀɢᴀʟᴇʀᴛ ᴏɴ"""
    data = await tagalert_db.find_one({"user_id": user_id})
    return data.get("enabled", True) if data else False

async def get_user_groups(user_id: int):
    """ɢᴇᴛ ɢʀᴏᴜᴘs ᴜsᴇʀ ɪs ɪɴ"""
    data = await tagalert_db.find_one({"user_id": user_id})
    return data.get("groups", []) if data else []

async def save_user_config(user_id: int, config: dict):
    """sᴀᴠᴇ ᴜsᴇʀ ᴄᴏɴғɪɢ"""
    await tagalert_db.update_one({"user_id": user_id}, {"$set": config}, upsert=True)

# ᴍᴀɪɴ ᴛᴀɢ ᴅᴇᴛᴇᴄᴛᴏʀ
@app.on_message(filters.group & filters.text)
async def tag_detector(_, message: Message):
    chat_id = message.chat.id
    chat_title = message.chat.title or "ᴜɴᴋɴᴏᴡɴ ɢʀᴏᴜᴘ"
    
    text = message.text
    mentioned_users = []
    
    # ᴇxᴛʀᴀᴄᴛ ᴍᴇɴᴛɪᴏɴᴇᴅ ᴜsᴇʀs
    for pattern in TAG_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            if "id" in pattern:
                # ᴘᴀʀsᴇ ᴜsᴇʀ ɪᴅ
                try:
                    uid = int(match.group(2))
                    mentioned_users.append(uid)
                except:
                    continue
            else:
                # ɢᴇᴛ ᴜsᴇʀ ɪᴅ ғʀᴏᴍ ᴜsᴇʀɴᴀᴍᴇ/ᴛᴇxᴛ
                username = match.group(0).replace("@", "").replace("[", "").replace("]", "")
                try:
                    user = await app.get_users(username)
                    mentioned_users.append(user.id)
                except:
                    continue
    
    # sᴇɴᴅ ᴀʟᴇʀᴛs
    for user_id in mentioned_users:
        if user_id == message.from_user.id:
            continue  # sᴋɪᴘ sᴇʟғ-ᴛᴀɢs
        
        if not await is_tagalert_enabled(user_id):
            continue
        
        try:
            alert_msg = (
                f"📢 **ʏᴏᴜ'ᴠᴇ ʙᴇᴇɴ ᴛᴀɢɢᴇᴅ!**\n"
                f"👥 **ɢʀᴏᴜᴘ:** {chat_title}\n"
                f"🆔 **ᴄʜᴀᴛ ɪᴅ:** `{chat_id}`\n"
                f"👤 **ʙʏ:** {message.from_user.mention_html()}\n"
                f"💬 **ᴍᴇssᴀɢᴇ:** {text[:100]}{'...' if len(text) > 100 else ''}\n"
                f"🕒 **ᴛɪᴍᴇ:** {datetime.now().strftime('%H:%M')}"
            )
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 ᴠɪᴇᴡ ɢʀᴏᴜᴘ", f"https://t.me/c/{str(chat_id)[4:]}/{message.id}")],
                [InlineKeyboardButton("⚙️ ᴛᴀɢᴀʟᴇʀᴛ sᴇᴛᴛɪɴɢs", "tagalert_settings")]
            ])
            
            await app.send_message(user_id, alert_msg, reply_markup=kb, parse_mode="html")
            
        except (UserNotParticipant, PeerIdInvalid):
            pass  # ᴜsᴇʀ ʙʟᴏᴄᴋᴇᴅ ʙᴏᴛ
        except Exception as e:
            LOGGER("Tune.tagalert").error(f"ᴇʀʀᴏʀ sᴇɴᴅɪɴɢ ᴀʟᴇʀᴛ: {e}")

# ᴜsᴇʀ sᴇᴛᴛɪɴɢs
@app.on_callback_query(filters.regex(r"^tagalert_settings"))
async def tagalert_settings(_, callback: CallbackQuery):
    user_id = callback.from_user.id
    config = await tagalert_db.find_one({"user_id": user_id}) or {}
    enabled = config.get("enabled", True)
    
    status = "✅ ᴏɴ" if enabled else "❌ ᴏғғ"
    
    await callback.edit_message_text(
        f"""🔔 **ᴛᴀɢᴀʟᴇʀᴛ sᴇᴛᴛɪɴɢs**

sᴛᴀᴛᴜs: {status}
ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴs sᴇɴᴛ: {config.get('notifications', 0)}

**ᴡʜᴇɴ ᴛᴀɢɢᴇᴅ ɪɴ ɢʀᴏᴜᴘs:**
• ɢʀᴏᴜᴘ ɴᴀᴍᴇ
• ᴡʜᴏ ᴛᴀɢɢᴇᴅ ʏᴏᴜ
• ᴍᴇssᴀɢᴇ ᴘʀᴇᴠɪᴇᴡ
• ᴅɪʀᴇᴄᴛ ʟɪɴᴋ""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{status} ᴛᴏɢɢʟᴇ", "tagalert_toggle")],
            [InlineKeyboardButton("📊 ᴠɪᴇᴡ sᴛᴀᴛs", "tagalert_stats")],
            [InlineKeyboardButton("🔙 ᴄʟᴏsᴇ", "close")]
        ])
    )

@app.on_callback_query(filters.regex(r"^tagalert_toggle"))
async def toggle_tagalert(_, callback: CallbackQuery):
    user_id = callback.from_user.id
    config = await tagalert_db.find_one({"user_id": user_id}) or {}
    config["enabled"] = not config.get("enabled", True)
    
    await save_user_config(user_id, config)
    status = "✅ ᴇɴᴀʙʟᴇᴅ" if config["enabled"] else "❌ ᴅɪsᴀʙʟᴇᴅ"
    
    await callback.answer(f"ᴛᴀɢᴀʟᴇʀᴛ {status}!", show_alert=True)
    await tagalert_settings(_, callback)

@app.on_callback_query(filters.regex(r"^tagalert_stats"))
async def tagalert_stats(_, callback: CallbackQuery):
    user_id = callback.from_user.id
    config = await tagalert_db.find_one({"user_id": user_id}) or {}
    
    await callback.edit_message_text(
        f"""📊 **ʏᴏᴜʀ ᴛᴀɢᴀʟᴇʀᴛ sᴛᴀᴛs**

ᴛᴏᴛᴀʟ ɴᴏᴛɪғs: {config.get('notifications', 0)}
ᴀᴄᴛɪᴠᴇ: {"✅ ʏᴇs" if config.get('enabled', True) else "❌ ɴᴏ"}

**ʟᴀsᴛ ᴜᴘᴅᴀᴛᴇ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", "tagalert_settings")]
        ])
    )

# ᴄʟᴏsᴇ ʙᴜᴛᴛᴏɴ
@app.on_callback_query(filters.regex(r"^close"))
async def close_callback(_, callback: CallbackQuery):
    try:
        await callback.delete()
    except:
        await callback.message.delete()

# ᴄᴏᴍᴍᴀɴᴅs (ᴏᴘᴛɪᴏɴᴀʟ)
@app.on_message(filters.private & filters.command("tagalert"))
async def tagalert_cmd(_, message: Message):
    config = await tagalert_db.find_one({"user_id": message.from_user.id}) or {}
    enabled = config.get("enabled", True)
    
    status = "✅ ᴏɴ" if enabled else "❌ ᴏғғ"
    
    await message.reply_text(
        f"🔔 **ᴛᴀɢᴀʟᴇʀᴛ:** {status}\n"
        "sᴇɴᴅ /tagalert ᴏғғ ᴛᴏ ᴛᴏɢɢʟᴇ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ sᴇᴛᴛɪɴɢs", "tagalert_settings")]
        ])
    )

@app.on_message(filters.private & filters.command("tagalert") & filters.regex(r"off"))
async def tagalert_off(_, message: Message):
    await tagalert_db.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"enabled": False}},
        upsert=True
    )
    await message.reply_text("🔔 **ᴛᴀɢᴀʟᴇʀᴛ ᴅɪsᴀʙʟᴇᴅ**")

@app.on_message(filters.private & filters.command("tagalert") & filters.regex(r"on"))
async def tagalert_on(_, message: Message):
    await tagalert_db.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"enabled": True}},
        upsert=True
    )
    await message.reply_text("🔔 **ᴛᴀɢᴀʟᴇʀᴛ ᴇɴᴀʙʟᴇᴅ**")

LOGGER("Tune.handler.tagalert").info("✅ ᴛᴀɢᴀʟᴇʀᴛ sʏsᴛᴇᴍ ʟᴏᴀᴅᴇᴅ!")
