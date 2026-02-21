import os

from PIL import Image, ImageDraw, ImageFont

from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
BASE_IMAGE = "assets/background.png"  # 🔥 Yaha apni image ka path daal do

os.makedirs(CACHE_DIR, exist_ok=True)


def format_duration(duration):
    if duration:
        return duration
    return "0:00"


async def get_video_info(videoid):
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = result.get("title", "Unknown Title")
            duration = result.get("duration", "0:00")
            return title, duration
    except:
        pass
    return "Unknown Title", "0:00"


async def get_thumb(videoid):
    final_path = f"{CACHE_DIR}/{videoid}.png"

    if os.path.isfile(final_path):
        return final_path

    try:
        title, duration = await get_video_info(videoid)

        # Open base background
        image = Image.open(BASE_IMAGE).convert("RGBA")
        draw = ImageDraw.Draw(image)

        width, height = image.size

        # Load fonts (apne font file daal sakte ho)
        font_title = ImageFont.truetype("assets/font.ttf", 55)
        font_small = ImageFont.truetype("assets/font.ttf", 35)

        # Dark gradient bottom box
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [(0, height - 250), (width, height)],
            fill=(0, 0, 0, 180),
        )
        image = Image.alpha_composite(image, overlay)

        draw = ImageDraw.Draw(image)

        # 🎧 Apple Music style Earbuds symbol
        earbuds_icon = "🎧"

        # Song Title
        draw.text(
            (100, height - 210),
            f"{earbuds_icon} {title[:40]}",
            font=font_title,
            fill="white",
        )

        # Duration
        draw.text(
            (100, height - 130),
            f"Duration: {format_duration(duration)}",
            font=font_small,
            fill="white",
        )

        # Progress bar (static style)
        bar_x = 100
        bar_y = height - 80
        bar_width = width - 200
        bar_height = 12

        # Background bar
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            fill=(100, 100, 100),
        )

        # Played part (random for style)
        progress = int(bar_width * 0.3)
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + progress, bar_y + bar_height)],
            fill=(255, 60, 60),
        )

        image = image.convert("RGB")
        image.save(final_path)

        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
