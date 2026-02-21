from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatJoinRequest
)
from Oneforall import app


# ===============================
# 🔔 Detect Join Request
# ===============================

@app.on_chat_join_request()
async def join_request_handler(client, request: ChatJoinRequest):

    user = request.from_user
    chat = request.chat

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ ᴧᴄᴄєᴘᴛ",
                    callback_data=f"approve_{chat.id}_{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ ᴅєᴄʟɪηє",
                    callback_data=f"decline_{chat.id}_{user.id}"
                ),
            ]
        ]
    )

    await client.send_message(
        chat.id,
        f"<blockquote>📩 ηєᴡ ᴊσɪη ʀєǫᴜєꜱᴛ ✨\n\n"
        f"👤 ᴜꜱєʀ: {user.mention}\n"
        f"🆔 ɪᴅ: `{user.id}`\n\n"
        f"Choose an action:</blockquote>",
        reply_markup=buttons
    )


# ===============================
# 🔘 Button Handler
# ===============================

@app.on_callback_query(filters.regex("approve_|decline_"))
async def join_request_buttons(client, callback):

    data = callback.data.split("_")
    action = data[0]
    chat_id = int(data[1])
    user_id = int(data[2])

    try:
        if action == "approve":
            await client.approve_chat_join_request(chat_id, user_id)
            await callback.message.edit_text("✅ User Approved Successfully.")

        elif action == "decline":
            await client.decline_chat_join_request(chat_id, user_id)
            await callback.message.edit_text("❌ User Declined.")

    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)
