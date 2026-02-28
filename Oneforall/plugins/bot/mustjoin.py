from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from pyrogram.enums import ParseMode
from Oneforall import app

MUST_JOIN = "dark_musictm"  # Username or chat ID

@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(app: Client, msg: Message):
    if not MUST_JOIN:
        return

    try:
        try:
            await app.get_chat_member(MUST_JOIN, msg.from_user.id)

        except UserNotParticipant:
            if str(MUST_JOIN).startswith("@") or str(MUST_JOIN).isalpha():
                link = f"https://t.me/{MUST_JOIN.lstrip('@')}"
            else:
                chat_info = await app.get_chat(MUST_JOIN)
                link = chat_info.invite_link

            try:
                await msg.reply_photo(
                    photo="https://graph.org/file/b1cfad9f2f765e317efc0-b05c093f37918d1655.jpg",
                    caption=(
                        "❖ <b><u>ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ Jᴏɪɴᴇᴅ </u></b>"
                        "<b><a href='https://t.me/dark_musictm'>ᴏᴜʀ ᴄʜᴀɴɴᴇʟ</a></b> <b>yet.</b>\n"
                        "➥ <b>ғᴏʀ ᴜsɪɴɢ ᴍᴇ, ᴘʟᴇᴀsᴇ ɪᴏɪɴ</b> "
                        "<b><a href='https://t.me/snowy_hometown'>ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ᴀɴᴅ ᴛʀʏ ᴍᴇ ᴀɢᴀɪɴ</a></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "📢˹Jᴏɪɴ sᴜᴘᴘᴏʀᴛ˼",
                                    url="https://t.me/snowy_hometown"
                                ),
                                InlineKeyboardButton(
                                    "💬˹ɪɴꜰɪɴɪᴛʏ ✘ ɴᴇᴛᴡᴏʀᴋ˼ 🎧",
                                    url=link
                                )
                            ]
                        ]
                    ),
                    parse_mode=ParseMode.HTML
                )

                await msg.stop_propagation()

            except ChatWriteForbidden:
                pass

    except ChatAdminRequired:
        print(f"❖ Promote me as an admin in the MUST_JOIN chat: {MUST_JOIN}")
