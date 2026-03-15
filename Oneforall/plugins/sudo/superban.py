import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from Oneforall import app
from Oneforall.utils.database import (
    add_banned_user,
    remove_banned_user,
    is_banned_user,
    get_served_chats
)
from Oneforall.utils import get_readable_time
from config import SUPERBAN_LOG_GC, SUPERBAN_CHANNEL, SUPERBAN_VIDEO, SUPERBAN_ADMINS

REQUESTS = {}

# -------- SMALL CAPS FUNCTION --------
SMALL_CAPS = {
    "a": "ᴀ","b": "ʙ","c": "ᴄ","d": "ᴅ","e": "ᴇ","f": "ғ","g": "ɢ","h": "ʜ",
    "i": "ɪ","j": "ᴊ","k": "ᴋ","l": "ʟ","m": "ᴍ","n": "ɴ","o": "ᴏ","p": "ᴘ",
    "q": "ǫ","r": "ʀ","s": "s","t": "ᴛ","u": "ᴜ","v": "ᴠ","w": "ᴡ","x": "x",
    "y": "ʏ","z": "ᴢ"
}

def sc(text: str):
    return "".join(SMALL_CAPS.get(c.lower(), c) for c in text)

# -------- USER EXTRACT --------
async def get_target_user(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id

    if len(message.command) < 2:
        return None

    user = await app.get_users(message.command[1])
    return user.id


# -------- SUPERBAN REQUEST --------
@app.on_message(filters.command("superban"))
async def superban_request(client, message: Message):

    user_id = await get_target_user(message)

    if not user_id:
        return await message.reply_text(sc("Reply to user or give username/id."))

    user = await app.get_users(user_id)

    req_id = int(time.time())

    REQUESTS[req_id] = {
        "type": "ban",
        "user_id": user_id,
        "user_name": user.mention,
        "chat_id": message.chat.id,
        "request_by": message.from_user.mention,
        "request_time": time.time()
    }

    buttons = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{req_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{req_id}")
        ]]
    )

    await app.send_message(
        SUPERBAN_LOG_GC,
        f"""
#SUPERBAN_REQUEST

USER : {user.mention}
USER ID : {user_id}

REQUEST BY : {message.from_user.mention}
""",
        reply_markup=buttons
    )

    await message.reply_text(sc("Superban request sent to admins."))


# -------- SUPERUNBAN REQUEST --------
@app.on_message(filters.command("superunban"))
async def superunban_request(client, message: Message):

    user_id = await get_target_user(message)

    if not user_id:
        return await message.reply_text(sc("Reply to user or give username/id."))

    user = await app.get_users(user_id)

    req_id = int(time.time())

    REQUESTS[req_id] = {
        "type": "unban",
        "user_id": user_id,
        "user_name": user.mention,
        "chat_id": message.chat.id,
        "request_by": message.from_user.mention,
        "request_time": time.time()
    }

    buttons = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{req_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{req_id}")
        ]]
    )

    await app.send_message(
        SUPERBAN_LOG_GC,
        f"""
#SUPERUNBAN_REQUEST

USER : {user.mention}
USER ID : {user_id}

REQUEST BY : {message.from_user.mention}
""",
        reply_markup=buttons
    )

    await message.reply_text(sc("Superunban request sent to admins."))


# -------- BUTTON HANDLER --------
@app.on_callback_query(filters.regex("(approve|reject)_"))
async def superban_buttons(client, query: CallbackQuery):

    if query.from_user.id not in SUPERBAN_ADMINS:
        return await query.answer("Not allowed", True)

    action, req_id = query.data.split("_")
    req_id = int(req_id)

    if req_id not in REQUESTS:
        return await query.answer("Already Processed", True)

    req = REQUESTS[req_id]
    user_id = req["user_id"]

    # -------- REJECT --------
    if action == "reject":

        await query.message.edit_text(
            sc(f"""
Request Rejected

User : {req['user_name']}

Rejected By : {query.from_user.mention}
""")
        )

        await app.send_message(
            req["chat_id"],
            sc(f"""
Request Rejected

User : {req['user_name']}

Rejected By : {query.from_user.mention}
""")
        )

        del REQUESTS[req_id]
        return

    # -------- LOCK MESSAGE --------
    await query.message.edit_text(sc("Processing request..."))

    # -------- ALREADY BANNED CHECK --------
    if req["type"] == "ban":
        if await is_banned_user(user_id):
            await query.message.edit_text(sc("User already superbanned"))
            del REQUESTS[req_id]
            return

    start = time.time()
    served_chats = await get_served_chats()

    success = 0
    failed = 0

    for chat in served_chats:

        chat_id = chat["chat_id"]

        try:

            if req["type"] == "ban":
                await app.ban_chat_member(chat_id, user_id)
            else:
                await app.unban_chat_member(chat_id, user_id)

            success += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except:
            failed += 1

    if req["type"] == "ban":
        await add_banned_user(user_id)
        action_text = "SuperBan"
    else:
        await remove_banned_user(user_id)
        action_text = "SuperUnBan"

    end = time.time()

    taken = get_readable_time(int(end - start))
    approve_delay = get_readable_time(int(end - req["request_time"]))

    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y/%m/%d %I:%M %p IST")

    total = success + failed

    report = f"""
#Is_{action_text}

USER : {req['user_name']}
USER ID : {req['user_id']}

TOTAL CHATS : {total}
SUCCESS : {success}
FAILED : {failed}

REQUEST BY : {req['request_by']}
APPROVED BY : {query.from_user.mention}

TIME TAKEN : {taken}
APPROVE DELAY : {approve_delay}

DATE & TIME : {now}

POWER : @Meowbans
"""

    try:
        await app.send_video(
            SUPERBAN_CHANNEL,
            SUPERBAN_VIDEO,
            caption=report
        )
    except:
        await app.send_message(
            SUPERBAN_CHANNEL,
            report
        )

    await query.message.edit_text(
        sc(f"""
{action_text} Approved

User : {req['user_name']}

Approved By : {query.from_user.mention}
""")
    )

    await app.send_message(
        req["chat_id"],
        sc(f"""
{action_text} Approved

User : {req['user_name']}

Approved By : {query.from_user.mention}
""")
    )

    try:
        await app.send_message(
            user_id,
            sc(f"""
You have been {action_text}

Approved By : {query.from_user.mention}
""")
        )
    except:
        pass

    del REQUESTS[req_id]
