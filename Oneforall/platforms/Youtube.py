# If You Are use This in another Repo Make Sure Change Module Name in Line Number 10 and 12 .

import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from Oneforall.utils.formatters import time_to_seconds
import aiohttp
from Oneforall import LOGGER

logger = LOGGER("Oneforall.platforms.Youtube")

# ---------------- SECURITY CONSTANTS ---------------- #

YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
)

DANGEROUS_KEYWORDS = [
    # adult
    "porn","xxx","sex","hentai","nude","naked","onlyfans","adult",

    # drugs
    "weed","marijuana","cocaine","heroin","meth","drug","lsd",

    # violent / dangerous
    "beheading","bomb","explosive","cartel","terrorist",

    # piracy / copyright bait
    "full movie","free movie","leaked","camrip","pirated"
]

YOUR_API_URL = None
FALLBACK_API_URL = "https://vercel.com/txkuzes-projects/admin-music-hub"


# ---------------- FILTER FUNCTIONS ---------------- #

def contains_dangerous(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    for word in DANGEROUS_KEYWORDS:
        if word in text:
            return True
    return False


def validate_youtube_url(link: str) -> bool:
    return bool(YOUTUBE_URL_PATTERN.search(link))


# ---------------- LOAD API ---------------- #

async def load_api_url():
    global YOUR_API_URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/rLsBhAQa",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info("API URL loaded")

                else:
                    YOUR_API_URL = FALLBACK_API_URL

    except Exception:
        YOUR_API_URL = FALLBACK_API_URL


try:
    loop = asyncio.get_event_loop()

    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())

except RuntimeError:
    pass


# ---------------- DOWNLOAD AUDIO ---------------- #

async def download_song(link: str) -> str:

    if not validate_youtube_url(link):
        return None

    global YOUR_API_URL

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split("v=")[-1].split("&")[0]

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    try:

        async with aiohttp.ClientSession() as session:

            params = {"url": video_id, "type": "audio"}

            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:

                if response.status != 200:
                    return None

                data = await response.json()

                token = data.get("download_token")

                if not token:
                    return None

                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=audio"

                async with session.get(
                    stream_url,
                    headers={"X-Download-Token": token},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as file_response:

                    if file_response.status != 200:
                        return None

                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)

                    return file_path

    except Exception as e:
        logger.error(f"Audio download error: {e}")
        return None


# ---------------- SAFE PLAYLIST FETCH ---------------- #

async def get_playlist_ids(link: str, limit: int):

    process = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-i",
        "--get-id",
        "--flat-playlist",
        "--playlist-end",
        str(limit),
        "--skip-download",
        link,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if stdout:
        return stdout.decode().splitlines()

    return []


# ---------------- MAIN CLASS ---------------- #

class YouTubeAPI:

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str):
        return validate_youtube_url(link)

    async def details(self, link: str):

        if "&" in link:
            link = link.split("&")[0]

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]
            duration = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]

            # -------- CONTENT FILTER -------- #

            if contains_dangerous(title) or contains_dangerous(thumbnail):

                raise Exception(
                    "❌ Cannot play this track.\n"
                    "Detected dangerous / adult / drug related content."
                )

            duration_sec = int(time_to_seconds(duration)) if duration else 0

            return title, duration, duration_sec, thumbnail, vidid


    async def playlist(self, link, limit, user_id):

        if "&" in link:
            link = link.split("&")[0]

        if not validate_youtube_url(link):
            return []

        ids = await get_playlist_ids(link, limit)

        return ids


    async def track(self, link: str):

        results = VideosSearch(link, limit=1)

        for result in (await results.next())["result"]:

            title = result["title"]
            duration = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]

            # -------- FILTER -------- #

            if contains_dangerous(title) or contains_dangerous(thumbnail):

                raise Exception(
                    "❌ Cannot play this track.\n"
                    "Detected dangerous / adult / drug related content."
                )

            return {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration,
                "thumb": thumbnail,
            }, vidid
