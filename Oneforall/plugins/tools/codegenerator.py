import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message


API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

BLACKBOX_API_URL = os.getenv(
    "BLACKBOX_API_URL",
    "https://api.blackbox.ai/v1/chat/completions"
)
BLACKBOX_API_KEY = os.getenv("BLACKBOX_API_KEY")
BLACKBOX_MODEL = os.getenv("BLACKBOX_MODEL", "gpt-3.5-turbo")

if not all([API_ID, API_HASH, BOT_TOKEN, BLACKBOX_API_KEY]):
    raise ValueError(
        "Please set API_ID, API_HASH, BOT_TOKEN, and BLACKBOX_API_KEY in environment variables."
    )


LANGUAGES = {
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "html": "html",
    "css": "css",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "sql": "sql",
    "php": "php",
}

app = Client(
    "code_generator_bot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


async def get_code_from_blackbox(language: str, prompt: str) -> str:

    full_prompt = (
        f"Write a {language} code for: {prompt}. "
        f"Only provide the code, no explanations."
    )

    payload = {
        "model": BLACKBOX_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BLACKBOX_API_KEY}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                BLACKBOX_API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            ) as response:

                data = await response.json()

                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]

                return str(data)

    except Exception as e:
        return f"Error: {str(e)}"


@app.on_message(filters.command("code") & (filters.private | filters.group))
async def handle_code_generation(client: Client, message: Message):

    if not message.text:
        return

    cmd = message.command[0]  
    lang_key = cmd.replace("code", "")

    if lang_key not in LANGUAGES:
        await message.reply(
            "❌ Invalid language.\n\n"
            "Example: /codepy create hello world\n\n"
            "Supported: py, js, html, cpp, java, go, rust, sql, php"
        )
        return

    prompt = message.text.replace(f"/{cmd}", "").strip()

    if not prompt:
        await message.reply("⚠️ Please provide a prompt.")
        return

    processing = await message.reply(
        f"⚙️ Generating {LANGUAGES[lang_key]} code..."
    )

    generated_code = await get_code_from_blackbox(
        LANGUAGES[lang_key], prompt
    )

    if generated_code.startswith("Error"):
        await processing.edit(generated_code)
        return

    file_ext = LANGUAGES[lang_key]
    file_name = f"generated_code.{file_ext}"

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(generated_code)

        await message.reply_document(
            file_name,
            caption=f"✅ Generated {LANGUAGES[lang_key].title()} Code\n"
                    f"📝 Prompt: `{prompt}`"
        )

        await processing.delete()

    except Exception as e:
        await processing.edit(f"❌ File error: {e}")

    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


print("🤖 Code Generator Bot Started...")
app.run()
