import asyncio
import random
import html
import aiohttp

from pyrogram import filters
from pyrogram.enums import PollType
from pyrogram.types import Message

from Oneforall import app
from Oneforall.utils.database import db


# ================= CONFIG ================= #

QUIZ_INTERVAL = 3600  # 1 hour (change if needed)


# ================= DATABASE ================= #

async def add_chat(chat_id: int):
    await db.autoquiz_chats.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )


async def get_all_chats():
    chats = db.autoquiz_chats.find({})
    return [chat["chat_id"] async for chat in chats]


# ================= REGISTER GROUP ================= #

@app.on_message(filters.group & filters.incoming, group=10)
async def register_chat(_, message: Message):
    await add_chat(message.chat.id)


# ================= QUIZ FETCHER ================= #

async def fetch_quiz():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if not data.get("results"):
        return None

    result = data["results"][0]

    question = html.unescape(result["question"])
    correct = html.unescape(result["correct_answer"])
    incorrect = [html.unescape(i) for i in result["incorrect_answers"]]

    answers = incorrect + [correct]
    random.shuffle(answers)
    correct_id = answers.index(correct)

    return question, answers, correct_id


# ================= AUTO LOOP ================= #

async def auto_quiz_loop():

    await app.wait_until_ready()

    while True:
        try:
            chats = await get_all_chats()

            if not chats:
                await asyncio.sleep(QUIZ_INTERVAL)
                continue

            for chat_id in chats:

                quiz = await fetch_quiz()
                if not quiz:
                    continue

                question, answers, correct_id = quiz

                try:
                    await app.send_poll(
                        chat_id=chat_id,
                        question=f"🧠 AUTO QUIZ!\n\n{question}",
                        options=answers,
                        type=PollType.QUIZ,
                        correct_option_id=correct_id,
                        is_anonymous=False
                    )
                except Exception as e:
                    print(f"Quiz send failed in {chat_id}: {e}")

        except Exception as e:
            print("Auto Quiz Error:", e)

        await asyncio.sleep(QUIZ_INTERVAL)


# ================= START BACKGROUND TASK ================= #

app.loop.create_task(auto_quiz_loop())
