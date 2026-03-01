import re
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, CallbackQuery
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta

from Tune import app, LOGGER
from Tune.utils.database import mongodb

nsfw_db = mongodb["nsfw_filters"]
nsfw_words_db = mongodb["nsfw_custom_words"]

DEFAULT_NSFW = [
    "porn", "sex", "nude", "xxx", "adult", "nsfw", "leak", "onlyfans", "hentai",
    "bit.ly", "tinyurl", "short.link", "cutt.ly"
]

async def is_admin_nsfw(client, entity):
    user_id = entity.from_user.id if hasattr(entity, 'from_user') else entity.message.from_user.id
    chat_id = entity.chat.id if hasattr(entity, 'chat') else entity.message.chat.id
    try:
        from Tune.core.misc import sudo
        if user_id in await sudo(): return True
    except: pass
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except: return False

async def get_nsfw_config(chat_id: int):
    """ɢᴇᴛ ɴsғᴡ ᴄᴏɴғɪɢ"""
    config = await nsfw_db.find_one({"chat_id": chat_id})
    if not config:
        config = {
            "chat_id": chat_id,
            "nsfw_active": True,
            "delete_msg": True,
            "warn_user": False,
            "mute_user": False,
            "ban_user": False,
            "mute_duration": 300 # yeh iska matlab 5 minite 
        }
        await nsfw_db.insert_one(config)
    return config

async def get_custom_words(chat_id: int):
    """ɢᴇᴛ ᴄᴜsᴛᴏᴍ ᴡᴏʀᴅs"""
    data = await nsfw_words_db.find_one({"chat_id": chat_id})
    return data.get("words", []) if data else []


@app.on_message(filters.group & filters.text & ~filters.me)
async def nsfw_text_filter(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    
    if await is_admin_nsfw(app, message):
        return
    
    config = await get_nsfw_config(chat_id)
    if not config.get("nsfw_active", True):
        return
    
    text = message.text.lower()
    

    custom_words = await get_custom_words(chat_id)
    all_words = DEFAULT_NSFW + custom_words
    
    detected = False
    for word in all_words:
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            detected = True
            break
    
    if not detected:
        return
    
    try:

        if config.get("delete_msg", True):
            await message.delete()
        

        warn_text = ""
        if config.get("warn_user", False):
            warn_text = f"⚠️ **ᴡᴀʀɴᴇᴅ:** {message.from_user.mention}\n"
        

        if config.get("mute_user", False):
            duration = config.get("mute_duration", 300)
            await app.restrict_chat_member(
                chat_id, user_id,
                ChatPermissions(),
                until_date=datetime.now() + timedelta(seconds=duration)
            )
            warn_text += f"🔇 **ᴍᴜᴛᴇᴅ:** {duration // 60} ᴍɪɴᴜᴛᴇs\n"
        

        if config.get("ban_user", False):
            await app.ban_chat_member(chat_id, user_id)
            warn_text += f"🚫 **ʙᴀɴɴᴇᴅ:** {message.from_user.mention}\n"   
            

        if warn_text or config.get("delete_msg"):
            alert = (
                f"🚨 **ɴsғᴡ ᴅᴇᴛᴇᴄᴛᴇᴅ**\n"
                f"{warn_text}\n"
                f"**ʀᴇᴀsᴏɴ:** ʙʟᴏᴄᴋᴇᴅ ᴄᴏɴᴛᴇɴᴛ"
            )
            sent = await message.reply_text(alert)
            await asyncio.sleep(5)
            await sent.delete()
        

        await nsfw_db.update_one(
            {"chat_id": chat_id},
            {"$inc": {"total_blocks": 1}},
            upsert=True
        )
        
    except FloodWait as fw:
        await asyncio.sleep(fw.value)
    except Exception as e:
        LOGGER("Tune.nsfw").error(f"ᴇʀʀᴏʀ: {e}")


@app.on_message(filters.group & (filters.photo | filters.video | filters.document) & ~filters.me)
async def media_nsfw_filter(_, message: Message):
    if await is_admin_nsfw(app, message):
        return
    
    chat_id = message.chat.id
    config = await get_nsfw_config(chat_id)
    
    if not config.get("nsfw_active", True):
        return
    
    if message.caption:
        custom_words = await get_custom_words(chat_id)
        all_words = DEFAULT_NSFW + custom_words
        
        for word in all_words:
            if re.search(rf"\b{re.escape(word)}\b", message.caption.lower(), re.IGNORECASE):
                if config.get("delete_msg", True):
                    await message.delete()
                    await message.reply_text("🚫 **ɴsғᴡ ᴍᴇᴅɪᴀ ʙʟᴏᴄᴋᴇᴅ**")
                break


@app.on_callback_query(filters.regex(r"^h_filters_config"))
async def nsfw_menu(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    config = await get_nsfw_config(chat_id)
    
    status = "✅ ᴀᴄᴛɪᴠᴇ" if config.get("nsfw_active") else "❌ ᴅɪsᴀʙʟᴇᴅ"
    
    actions = []
    if config.get("delete_msg"): actions.append("🗑️ ᴅᴇʟᴇᴛᴇ")
    if config.get("warn_user"): actions.append("⚠️ ᴡᴀʀɴ")
    if config.get("mute_user"): actions.append("🔇 ᴍᴜᴛᴇ")
    if config.get("ban_user"): actions.append("🚫 ʙᴀɴ")
    
    actions_text = ", ".join(actions) if actions else "ɴᴏɴᴇ"
    
    await callback.edit_message_text(
        f"""🔒 **ɴsғᴡ & sᴘᴀᴍ ғɪʟᴛᴇʀ**

sᴛᴀᴛᴜs: {status}
ᴀᴄᴛɪᴏɴs: {actions_text}
ʙʟᴏᴄᴋs: {config.get('total_blocks', 0)}""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 ᴛᴏɢɢʟᴇ", "nsfw_toggle")],
            [InlineKeyboardButton("⚙️ ᴀᴄᴛɪᴏɴs", "nsfw_actions")],
            [InlineKeyboardButton("📝 ᴄᴜsᴛᴏᴍ ᴡᴏʀᴅs", "nsfw_custom_words")],
            [InlineKeyboardButton("📊 sᴛᴀᴛs", "nsfw_stats")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", "h_settings")]
        ])
    )

@app.on_callback_query(filters.regex(r"^nsfw_toggle"))
async def toggle_nsfw(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    config = await get_nsfw_config(chat_id)
    
    await nsfw_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"nsfw_active": not config.get("nsfw_active", True)}},
        upsert=True
    )
    
    await callback.answer("✅ ᴛᴏɢɢʟᴇᴅ!", show_alert=True)
    await nsfw_menu(_, callback)


@app.on_callback_query(filters.regex(r"^nsfw_actions"))
async def nsfw_actions_menu(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    config = await get_nsfw_config(chat_id)
    
    def icon(key):
        return "✅" if config.get(key, False) else "❌"
    
    await callback.edit_message_text(
        """⚙️ **sᴇʟᴇᴄᴛ ᴘᴜɴɪsʜᴍᴇɴᴛ ᴀᴄᴛɪᴏɴs**
ᴄʟɪᴄᴋ ᴛᴏ ᴛᴏɢɢʟᴇ ᴇᴀᴄʜ:""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{icon('delete_msg')} ᴅᴇʟᴇᴛᴇ ᴍsɢ", "act_delete")],
            [InlineKeyboardButton(f"{icon('warn_user')} ᴡᴀʀɴ ᴜsᴇʀ", "act_warn")],
            [InlineKeyboardButton(f"{icon('mute_user')} ᴍᴜᴛᴇ ᴜsᴇʀ", "act_mute")],
            [InlineKeyboardButton(f"{icon('ban_user')} ʙᴀɴ ᴜsᴇʀ", "act_ban")],
            [InlineKeyboardButton("⏱️ ᴍᴜᴛᴇ ᴅᴜʀᴀᴛɪᴏɴ", "act_duration")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", "h_filters_config")]
        ])
    )

@app.on_callback_query(filters.regex(r"^act_(delete|warn|mute|ban)"))
async def toggle_action(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    action = callback.data.split("_")[1]
    
    key_map = {
        "delete": "delete_msg",
        "warn": "warn_user",
        "mute": "mute_user",
        "ban": "ban_user"
    }
    
    key = key_map[action]
    config = await get_nsfw_config(chat_id)
    
    await nsfw_db.update_one(
        {"chat_id": chat_id},
        {"$set": {key: not config.get(key, False)}},
        upsert=True
    )
    
    await nsfw_actions_menu(_, callback)

@app.on_callback_query(filters.regex(r"^act_duration"))
async def mute_duration_menu(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    await callback.edit_message_text(
        "⏱️ **sᴇʟᴇᴄᴛ ᴍᴜᴛᴇ ᴅᴜʀᴀᴛɪᴏɴ**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("5 ᴍɪɴs", "dur_300"), InlineKeyboardButton("10 ᴍɪɴs", "dur_600")],
            [InlineKeyboardButton("30 ᴍɪɴs", "dur_1800"), InlineKeyboardButton("1 ʜᴏᴜʀ", "dur_3600")],
            [InlineKeyboardButton("1 ᴅᴀʏ", "dur_86400"), InlineKeyboardButton("ᴘᴇʀᴍᴀɴᴇɴᴛ", "dur_0")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", "nsfw_actions")]
        ])
    )

@app.on_callback_query(filters.regex(r"^dur_(d+)"))
async def set_duration(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    duration = int(callback.data.split("_")[1])
    
    await nsfw_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"mute_duration": duration}},
        upsert=True
    )
    
    dur_text = "ᴘᴇʀᴍᴀɴᴇɴᴛ" if duration == 0 else f"{duration // 60} ᴍɪɴs"
    await callback.answer(f"✅ sᴇᴛ: {dur_text}", show_alert=True)
    await mute_duration_menu(_, callback)


custom_word_state = {}

@app.on_callback_query(filters.regex(r"^nsfw_custom_words"))
async def custom_words_menu(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    words = await get_custom_words(chat_id)
    
    words_text = ", ".join(words) if words else "ɴᴏɴᴇ"
    
    await callback.edit_message_text(
        f"""📝 **ᴄᴜsᴛᴏᴍ ɴsғᴡ ᴡᴏʀᴅs**

ᴄᴜʀʀᴇɴᴛ: {words_text}

**ʀᴇᴘʟʏ ᴛᴏ ᴛʜɪs ᴍᴇssᴀɢᴇ** ᴡɪᴛʜ ᴡᴏʀᴅs (sᴘᴀᴄᴇ sᴇᴘᴀʀᴀᴛᴇᴅ):""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ ᴄʟᴇᴀʀ ᴀʟʟ", "clear_custom_words")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", "h_filters_config")]
        ])
    )
    
    custom_word_state[callback.from_user.id] = chat_id

@app.on_message(filters.reply & filters.text & filters.group)
async def save_custom_words(client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in custom_word_state:
        return
    
    if not await is_admin_nsfw(client, message):
        await message.reply("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**")
        return
    
    chat_id = custom_word_state.pop(user_id)
    words = message.text.lower().split()
    
    await nsfw_words_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"words": words}},
        upsert=True
    )
    
    await message.reply(f"✅ **{len(words)} ᴄᴜsᴛᴏᴍ ᴡᴏʀᴅs sᴀᴠᴇᴅ!**")

@app.on_callback_query(filters.regex(r"^clear_custom_words"))
async def clear_words(_, callback: CallbackQuery):
    if not await is_admin_nsfw(app, callback):
        await callback.answer("🔒 **ᴀᴅᴍɪɴs ᴏɴʟʏ!**", show_alert=True)
        return
    
    chat_id = callback.message.chat.id
    await nsfw_words_db.delete_one({"chat_id": chat_id})
    
    await callback.answer("✅ ᴄʟᴇᴀʀᴇᴅ!", show_alert=True)
    await custom_words_menu(_, callback)

LOGGER("Tune.handler.nsfw").info("✅ ᴀᴅᴠᴀɴᴄᴇᴅ ɴsғᴡ ғɪʟᴛᴇʀ ʟᴏᴀᴅᴇᴅ!")
