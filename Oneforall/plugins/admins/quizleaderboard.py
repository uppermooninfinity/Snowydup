import asyncio
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.enums import ParseMode
from Oneforall import app
from Oneforall.mongo import db

STATS_COLL = db.quiz_stats
CHATS_COLL = db.chats

LEADERBOARD_VIDEO = "https://files.catbox.moe/dtcr9p.mp4"
TROPHY_IMAGE = "https://files.catbox.moe/qplosp.jpg"


# ================= TRACK QUIZ RESULTS =================

@app.on_poll_voted()
async def track_quiz_results(client, poll):
    if not poll.quiz:
        return

    chat_id = poll.chat.id
    user_id = poll.user.id
    username = poll.user.first_name

    is_correct = poll.option_ids[0] == poll.correct_option_id

    await STATS_COLL.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$setOnInsert": {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "correct": 0,
                "wrong": 0,
                "attempts": 0
            },
            "$inc": {
                "correct": 1 if is_correct else 0,
                "wrong": 0 if is_correct else 1,
                "attempts": 1
            }
        },
        upsert=True
    )


# ================= GET ENABLED GROUPS =================

async def get_quiz_enabled_chats():
    cursor = CHATS_COLL.find({"quiz_enabled": True})
    return [doc["chat_id"] async for doc in cursor]


# ================= FETCH LEADERBOARD =================

async def get_quiz_leaderboard(chat_id: int, limit=10):
    cursor = (
        STATS_COLL
        .find({"chat_id": chat_id})
        .sort("correct", -1)
        .limit(limit)
    )
    return [doc async for doc in cursor]


# ================= SEND LEADERBOARD =================

async def send_leaderboard(chat_id: int, manual=False):
    top_users = await get_quiz_leaderboard(chat_id)

    if not top_users:
        return await app.send_message(
            chat_id,
            "› ɴᴏ ǫᴜɪᴢ sᴛᴀᴛs ʏᴇᴛ."
        )

    text = "<blockquote>🏆 ǫᴜɪᴢ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ (ᴛᴏᴘ 10)</blockquote>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top_users, 1):
        name = user.get("username", f"user {user['user_id']}")
        score = user.get("correct", 0)

        emoji = medals[i - 1] if i <= 3 else f"{i}."
        text += f"› {emoji} {name} → {score} ✅\n"

    try:
        msg = await app.send_video(
            chat_id,
            LEADERBOARD_VIDEO,
            caption=text,
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        msg = await app.send_photo(
            chat_id,
            photo=TROPHY_IMAGE,
            caption=text,
            parse_mode=ParseMode.MARKDOWN,
            has_spoiler=True
        )

    if not manual:
        try:
            await app.pin_chat_message(chat_id, msg.id, notify=False)
        except:
            pass

    return msg


# ================= PERSONAL LEADERBOARD =================

@app.on_message(filters.command(["lbpersonal", "mystats"]))
async def personal_lb(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    data = await STATS_COLL.find_one({
        "chat_id": chat_id,
        "user_id": user_id
    })

    if not data:
        return await message.reply(
            "› ʏᴏᴜ ʜᴀᴠᴇ ɴᴏ ǫᴜɪᴢ sᴛᴀᴛs ʏᴇᴛ."
        )

    correct = data.get("correct", 0)
    wrong = data.get("wrong", 0)
    attempts = data.get("attempts", 0)

    accuracy = round((correct / attempts) * 100, 2) if attempts else 0

    text = (
        "<blockquote> 📊 ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ǫᴜɪᴢ sᴛᴀᴛs\n>\n"
        f"› ✅ ᴄᴏʀʀᴇᴄᴛ : {correct}\n"
        f"› ❌ ᴡʀᴏɴɢ : {wrong}\n"
        f"› 🎯 ᴀᴛᴛᴇᴍᴘᴛs : {attempts}\n"
        f"› 📈 ᴀᴄᴄᴜʀᴀᴄʏ : {accuracy}%</blockquote>"
    )

    await message.reply(text, parse_mode=ParseMode.MARKDOWN)


# ================= MANUAL LEADERBOARD =================

@app.on_message(filters.command(["quizlead", "leaderboard", "lb"]))
async def quizlead_cmd(client, message):
    await message.reply("› ʟᴏᴀᴅɪɴɢ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ...")
    await send_leaderboard(message.chat.id, manual=True)
    await message.delete()


# ================= AUTO LOOP =================

async def auto_leaderboard_loop():
    while True:
        now = datetime.now()

        targets = [
            now.replace(hour=15, minute=0, second=0, microsecond=0),
            now.replace(hour=21, minute=0, second=0, microsecond=0)
        ]

        future = [t for t in targets if t > now]

        if not future:
            next_time = (now + timedelta(days=1)).replace(
                hour=15, minute=0, second=0, microsecond=0
            )
        else:
            next_time = min(future)

        await asyncio.sleep((next_time - now).total_seconds())

        chats = await get_quiz_enabled_chats()

        for chat_id in chats:
            try:
                await send_leaderboard(chat_id)
            except Exception as e:
                print(f"lb error {chat_id}: {e}")


@app.on_startup()
async def startup():
    asyncio.create_task(auto_leaderboard_loop())
    print("📊 quiz leaderboard system loaded")
