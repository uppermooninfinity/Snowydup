from config import YOUTUBE_IMG_URL


async def get_thumb(videoid):
    """
    Return default thumbnail only.
    No custom image.
    No YouTube thumbnail fetching.
    No image processing.
    """
    return YOUTUBE_IMG_URL
