from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired
from pyrogram.enums import ChatMemberStatus

from Oneforall import app
from Oneforall.utils.database import get_antichannel, set_antichannel

OWNER_ID = 7651303468 # change if needed


# ------------------ TOGGLE COMMAND ------------------ #

@app.on_message(filters.command("antichannel") & filters.group)
async def toggle_antichannel(_, message: Message):

    if not message.from_user:
        return

    member = await app.get_chat_member(message.chat.id, message.from_user.id)

    if (
        member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        and message.from_user.id != OWNER_ID
    ):
        return await message.reply_text("Only admins can use this command.")

    data = await get_antichannel(message.chat.id)

    if data:
        await set_antichannel(message.chat.id, False)
        await message.reply_text("❌ Anti-Channel Disabled.")
    else:
        await set_antichannel(message.chat.id, True)
        await message.reply_text("✅ ᴀɴᴛɪ ᴄʜᴀɴɴᴇʟ / ᴄʜᴀɴɴᴇʟ ᴍsɢ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ.")


# ------------------ MAIN FILTER ------------------ #

@app.on_message(filters.group, group=5)
async def anti_channel_system(_, message: Message):

    if not message.sender_chat:
        return  # normal user message

    chat_id = message.chat.id
    channel_id = message.sender_chat.id

    enabled = await get_antichannel(chat_id)
    if not enabled:
        return

    # Skip if channel is linked
    if message.is_automatic_forward:
        return

    try:
        # Ban the channel
        await app.ban_chat_member(chat_id, channel_id)

        # Delete the message
        await message.delete()

        # Log message
        await app.send_message(
            chat_id,
            f"#ANTICHANNEL\n\n"
            f"❍ sᴇɴᴅᴇʀ ɪᴅ: `{channel_id}`\n"
            f"Action: DELETE + BAN",
            disable_web_page_preview=True,
        )

    except ChatAdminRequired:
        await app.send_message(chat_id, "I need ban & delete permissions.")
