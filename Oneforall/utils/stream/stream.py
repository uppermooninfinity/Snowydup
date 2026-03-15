import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config import THUMB_VID_URL, YOUTUBE_IMG_URL
from Oneforall import Carbon, YouTube, app
from Oneforall.core.call import Hotty
from Oneforall.misc import db
from Oneforall.utils.database import add_active_video_chat, is_active_chat
from Oneforall.utils.exceptions import AssistantErr
from Oneforall.utils.inline import (
    aq_markup,
    close_markup,
    stream_markup,
    stream_markup2,
)
from Oneforall.utils.stream.queue import put_queue, put_queue_index

# ✅ Import your custom thumbnail generrators
from Oneforall.utils.thumbnail import gen_thumb


# Anti-spam tracking
user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5


# ✅ Custom thumbnail (NO YouTube thumbnail fetch)
async def get_thumb(title, user_name):
    try:
        return await gen_thumb(title, user_name)
    except Exception:
        return config.YOUTUBE_IMG_URL


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return

    if forceplay:
        await Hotty.force_stop_stream(chat_id)

    # ================= PLAYLIST =================
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0

        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue

            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"

            else:
                if not forceplay:
                    db[chat_id] = []

                status = True if video else None
                try:
                    stream_link = await YouTube.stream(vidid)
                    file_path = stream_link
                    direct = True
                except:
                    await mystic.edit_text(_["play_3"])
                    return

                await Hotty.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=config.THUMB_VID_URL,
                    image=config.YOUTUBE_IMG_URL,  # ❌ No YouTube thumbnail
                )

                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )

                img = await get_thumb(title, user_name)
                button = stream_markup(_, vidid, chat_id)

                run = await app.send_video(
                    original_chat_id,
                    video=config.THUMB_VID_URL,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:18],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return
        else:
            link = await brandedBin(msg)
            lines = msg.count("\n")
            car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
            carbon = await Carbon.generate(car, randint(100, 10000000))
            upl = close_markup(_)

            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["play_21"].format(position, link),
                reply_markup=upl,
            )

    # ================= YOUTUBE =================
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = result["duration_min"]
        status = True if video else None

        try:
            stream_link = await YouTube.stream(vidid)
            file_path = stream_link
            direct = True
        except:
            return await mystic.edit_text(_["play_3"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )

            img = await get_thumb(title, user_name)
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)

            await app.send_video(
                chat_id=original_chat_id,
                video=config.THUMB_VID_URL,
                caption=_["queue_4"].format(
                    position, title[:18], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

        else:
            if not forceplay:
                db[chat_id] = []

            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=config.THUMB_VID_URL,
                image=config.YOUTUBE_IMG_URL,  # CONFIG SE LEGA AB THUMBNAIL
            )

            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )

            img = await get_thumb(title, user_name)
            button = stream_markup(_, vidid, chat_id)

            run = await app.send_video(
                original_chat_id,
                video=config.THUMB_VID_URL,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:18],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    # ================= LIVE =================
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = "Live Track"
        status = True if video else None

        if not forceplay:
            db[chat_id] = []

        n, file_path = await YouTube.video(link)
        if n == 0:
            raise AssistantErr(_["str_3"])

        await Hotty.join_call(
            chat_id,
            original_chat_id,
            file_path,
            video=config.THUMB_VID_URL,
            image=config.YOUTUBE_IMG_URL,
        )

        await put_queue(
            chat_id,
            original_chat_id,
            f"live_{vidid}",
            title,
            duration_min,
            user_name,
            vidid,
            user_id,
            "video" if video else "audio",
            forceplay=forceplay,
        )

        img = await get_thumb(title, user_name)
        button = stream_markup2(_, chat_id)

        run = await app.send_video(
            original_chat_id,
            video=config.THUMB_VID_URL,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{vidid}",
                title[:23],
                duration_min,
                user_name,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )

        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
