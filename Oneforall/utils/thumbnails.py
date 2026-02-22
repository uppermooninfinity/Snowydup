import os
from PIL import Image, ImageDraw, ImageFont
from youtubesearchpython.__future__ import VideosSearch

CACHE_DIR = "cache"
BASE_IMAGE = "assets/background.png"  # Apni custom background
FONT_PATH = "assets/font.ttf"        # Apna font file

os.makedirs(CACHE_DIR, exist_ok=True)


def format_duration(duration):
    return duration if duration else "0:00"


async def get_video_info(videoid):
    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        data = await results.next()
        for result in data["result"]:
            title = result.get("title", "Unknown Title")
            duration = result.get("duration", "0:00")
            return title, duration
    except Exception as e:
        print("Video Info Error:", e)

    return "Unknown Title", "0:00"


async def get_thumb(videoid):
    final_path = f"{CACHE_DIR}/{videoid}.png"

    if os.path.isfile(final_path):
        return final_path

    try:
        title, duration = await get_video_info(videoid)

        # Open background
        image = Image.open(BASE_IMAGE).convert("RGBA")
        width, height = image.size

        draw = ImageDraw.Draw(image)

        # Load font safely
        try:
            font_title = ImageFont.truetype(FONT_PATH, 55)
            font_small = ImageFont.truetype(FONT_PATH, 35)
        except:
            font_title = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Dark overlay bottom
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [(0, height - 250), (width, height)],
            fill=(0, 0, 0, 180),
        )
        image = Image.alpha_composite(image, overlay)

        draw = ImageDraw.Draw(image)

        # Title
        draw.text(
            (100, height - 210),
            f"🎧 {title[:40]}",
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

        # Progress bar
        bar_x = 100
        bar_y = height - 80
        bar_width = width - 200
        bar_height = 12

        draw.rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            fill=(100, 100, 100),
        )

        progress = int(bar_width * 0.3)
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + progress, bar_y + bar_height)],
            fill=(255, 60, 60),
        )

        image = image.convert("RGB")
        image.save(final_path)

        return final_path

    except Exception as e:
        print("Thumbnail Generation Error:", e)
        return BASE_IMAGE  # 🔥 Only custom fallback, NEVER YouTube
