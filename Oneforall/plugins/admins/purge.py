import time
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired, MessageDeleteForbidden

from Oneforall import app
from Oneforall.utils.database import get_admins  # agar tum already use karte ho

OWNER_ID = 7651303468  # change if needed


# -------------------- PURGE -------------------- #

@app.on_message(filters.command("purge") & filters.group)
async def purge_messages(_, message: Message):

    start = time.perf_counter()

    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # ✅ Admin Check (Mongo based)
    admins = await get_admins(chat_id)
    if user_id not in admins and user_id != OWNER_ID:
        return await message.reply_text("Only Admins are allowed to use this command")

    if not message.reply_to_message:
        return await message.reply_text(
            "Reply to a message to select where to start purging from."
        )

    try:
        delete_from = message.reply_to_message.id
        delete_to = message.id

        deleted = 0

        for msg_id in range(delete_from, delete_to + 1):
            try:
                await app.delete_messages(chat_id, msg_id)
                deleted += 1
            except:
                pass

        time_taken = time.perf_counter() - start

        await message.reply_text(
            f"ᴘᴜʀɢᴇᴅ {deleted} ᴍᴇssᴀɢᴇs ɪɴ {time_taken:0.2f}s 😎"
        )

    except ChatAdminRequired:
        await message.reply_text("I need delete permissions to purge messages.")
    except MessageDeleteForbidden:
        await message.reply_text("Can't delete some messages.")


# -------------------- DELETE -------------------- #

@app.on_message(filters.command("del") & filters.group)
async def delete_message(_, message: Message):

    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    admins = await get_admins(chat_id)
    if user_id not in admins and user_id != OWNER_ID:
        return await message.reply_text("Only Admins are allowed to use this command")

    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to delete it.")

    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        await message.reply_text("Can't delete this message.")


# -------------------- SILENT PURGE -------------------- #

@app.on_message(filters.command("spurge") & filters.group)
async def silent_purge(_, message: Message):

    if not message.reply_to_message:
        return

    delete_from = message.reply_to_message.id
    delete_to = message.id
    chat_id = message.chat.id

    for msg_id in range(delete_from, delete_to + 1):
        try:
            await app.delete_messages(chat_id, msg_id)
        except:
            pass
