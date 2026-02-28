import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from Oneforall import app
from Oneforall.mongo import db
from config import FED_LOG_CHANNEL, OWNER_ID, PING_IMG_URL

EDIT_COLL = db.edit_settings


# ================= DATABASE =================

async def set_edit_status(chat_id: int, status: bool):
    await EDIT_COLL.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )


async def get_edit_status(chat_id: int):
    data = await EDIT_COLL.find_one({"chat_id": chat_id})
    return data.get("enabled", False) if data else False


# ================= CONTROL PANEL =================

@app.on_message(filters.command("editmsg") & filters.group)
async def editmsg_panel(client, message):

    if not message.from_user:
        return

    member = await app.get_chat_member(message.chat.id, message.from_user.id)

    if not member.privileges or not member.privileges.can_delete_messages:
        return await message.reply("› ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.")

    status = await get_edit_status(message.chat.id)
    state = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"

    text = (
        "⚙️ ᴇᴅɪᴛ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴘᴀɴᴇʟ\n\n"
        f"❖ sᴛᴀᴛᴜs : {state}\n\n"
        "ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ 👇"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🟢 ᴏɴ", callback_data="edit_on"),
                InlineKeyboardButton("🔴 ᴏғғ", callback_data="edit_off"),
            ],
            [
                InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="edit_close")
            ]
        ]
    )

    await app.send_photo(
        chat_id=message.chat.id,
        photo=PING_IMG_URL,
        caption=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=buttons
    )


# ================= BUTTON HANDLER =================

@app.on_callback_query(filters.regex("^edit_"))
async def edit_buttons(client, callback):

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    member = await app.get_chat_member(chat_id, user_id)

    if not member.privileges or not member.privileges.can_delete_messages:
        return await callback.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.", show_alert=True)

    if callback.data == "edit_on":
        await set_edit_status(chat_id, True)
        await callback.answer("ᴇɴᴀʙʟᴇᴅ ✅")

    elif callback.data == "edit_off":
        await set_edit_status(chat_id, False)
        await callback.answer("ᴅɪsᴀʙʟᴇᴅ ❌")

    elif callback.data == "edit_close":
        return await callback.message.delete()

    status = await get_edit_status(chat_id)
    state = "ᴇɴᴀʙʟᴇᴅ ✅" if status else "ᴅɪsᴀʙʟᴇᴅ ❌"

    new_text = (
        "⚙️ ᴇᴅɪᴛ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴘᴀɴᴇʟ\n\n"
        f"❖ sᴛᴀᴛᴜs : {state}"
    )

    await callback.message.edit_caption(
        caption=new_text,
        parse_mode=ParseMode.MARKDOWN
    )


# ================= EDIT DETECTION =================

@app.on_edited_message(filters.group)
async def detect_edit(client, message):

    enabled = await get_edit_status(message.chat.id)
    if not enabled:
        return

    if not message.from_user:
        return

    try:
        await message.delete()
    except:
        return

    username = message.from_user.mention
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_title = message.chat.title
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # ========== GROUP WARNING IMAGE ==========

    group_text = (
        f"❖ ʜᴇʏ , {username}\n"
        "๏ ʏᴏᴜ ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ, sᴏ ɪ ᴅᴇʟᴇᴛᴇᴅ ɪᴛ !!\n\n"
        "❖ ᴏɴ|ᴏғғ ᴄᴍᴍɴᴅ : /editmsg"
    )

    group_buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", user_id=OWNER_ID),
                InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="edit_close")
            ]
        ]
    )

    warn_msg = await app.send_photo(
        chat_id=chat_id,
        photo=PING_IMG_URL,
        caption=group_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=group_buttons
    )

    await asyncio.sleep(10)
    try:
        await warn_msg.delete()
    except:
        pass

    # ========== LOG IMAGE ==========

    edited_content = message.text or message.caption or "ᴍᴇᴅɪᴀ ᴇᴅɪᴛᴇᴅ"

    log_text = (
        "📝 ᴍᴇssᴀɢᴇ ᴇᴅɪᴛᴇᴅ ᴀɴᴅ ᴅᴇʟᴇᴛᴇᴅ\n\n"
        f"❖ ᴄʜᴀᴛ : {chat_title}\n"
        f"❖ ᴄʜᴀᴛ ɪᴅ : `{chat_id}`\n"
        f"❖ ᴜsᴇʀ : {username}\n"
        f"❖ ᴜsᴇʀ ɪᴅ : `{user_id}`\n"
        f"❖ ᴛɪᴍᴇ : `{timestamp}`\n\n"
        f"❖ ᴇᴅɪᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ :\n`{edited_content}`"
    )

    log_buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", user_id=OWNER_ID)
            ]
        ]
    )

    await app.send_photo(
        chat_id=FED_LOG_CHANNEL,
        photo=PING_IMG_URL,
        caption=log_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=log_buttons
  )
