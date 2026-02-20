from pyrogram import filters
from Oneforall import app

@app.on_message(filters.command("stickid") & filters.reply)
async def stickid(_, message):

    reply = message.reply_to_message

    # Check if replied message has sticker
    if not reply or not reply.sticker:
        return await message.reply_text(
            "❌ Reply to a sticker with `/stickid`",
            parse_mode="markdown"
        )

    sticker = reply.sticker

    text = (
        "<blockquote>"
        "<b>🎯 sᴛɪᴄᴋᴇʀ ɪᴅ ғᴏᴜɴᴅ!</b>\n\n"
        "<b>📌 ғɪʟᴇ ɪᴅ:</b>\n"
        f"<code>{sticker.file_id}</code>\n\n"
        "<b>📦 ғɪʟᴇ ᴜɴɪǫᴜᴇ ɪᴅ:</b>\n"
        f"<code>{sticker.file_unique_id}</code>"
        "</blockquote>"
    )

    await message.reply_text(
        text,
        parse_mode="html",
        disable_web_page_preview=True
    )