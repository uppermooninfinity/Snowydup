import os
import random
import aiohttp
import aiofiles

from PIL import Image, ImageEnhance, ImageOps
from config import YOUTUBE_IMG_URL

# 🔥 Yaha apna Catbox direct image link daalo
CUSTOM_THUMB_URL = "https://files.catbox.moe/yourimage.png"

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


async def download_custom_thumb(videoid):
    """
    Download custom catbox image
    """
    path = f"{CACHE_DIR}/custom_{videoid}.png"

    if os.path.isfile(path):
        return path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CUSTOM_THUMB_URL) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path, mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                    return path
    except Exception as e:
        print(f"Thumbnail Download Error: {e}")

    return None


async def get_thumb(videoid):
    """
    Always use Custom Catbox Thumbnail
    """

    final_path = f"{CACHE_DIR}/{videoid}.png"

    if os.path.isfile(final_path):
        return final_path

    try:
        # 🔥 Download Custom Image
        thumb_path = await download_custom_thumb(videoid)

        if not thumb_path:
            return YOUTUBE_IMG_URL

        # 🎨 Open Image
        image = Image.open(thumb_path)

        # Resize
        image = changeImageSize(1280, 720, image)

        # Slight Brightness
        image = ImageEnhance.Brightness(image).enhance(1.1)

        # Slight Contrast
        image = ImageEnhance.Contrast(image).enhance(1.1)

        # Random Border Color
        colors = [
            "white", "red", "orange", "yellow",
            "green", "cyan", "blue",
            "violet", "magenta", "pink"
        ]
        border_color = random.choice(colors)

        image = ImageOps.expand(image, border=8, fill=border_color)

        # Save Final Image
        image.save(final_path)

        # Delete temp file
        try:
            os.remove(thumb_path)
        except:
            pass

        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
