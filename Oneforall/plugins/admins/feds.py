import uuid
import time
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
from Oneforall import app
from Oneforall.utils.database import fedsdb, fedbansdb
from config import OWNER_ID


# ─────────────────────────────
# Small Caps
# ─────────────────────────────

SMALL = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
)

def sc(t): return t.translate(SMALL)


# ─────────────────────────────
# Helpers
# ─────────────────────────────

async def get_fed_by_chat(chat_id):
    return await fedsdb.find_one({"chats": chat_id})

async def get_fed_by_id(fed_id):
    return await fedsdb.find_one({"fed_id": fed_id})

async def is_owner(fed, user):
    return fed["owner"] == user

async def is_admin(fed, user):
    return user == fed["owner"] or user in fed.get("admins", [])


# ─────────────────────────────
# 1️⃣ NEW FED
# ─────────────────────────────

@app.on_message(filters.command("newfed") & filters.private)
async def new_fed(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("⚠️ ᴜꜱᴇ: /newfed ɴᴀᴍᴇ")

    fed_id = str(uuid.uuid4())[:8]
    name = m.text.split(None, 1)[1]

    await fedsdb.insert_one({
        "fed_id": fed_id,
        "name": name,
        "owner": m.from_user.id,
        "admins": [],
        "chats": [],
        "rules": "",
        "log_channel": None,
        "subscribers": [],
        "notifications": True,
        "created": int(time.time())
    })

    await m.reply(
        f"✨ **{sc('federation created')}**\n\n"
        f"🏷 {name}\n🆔 `{fed_id}`"
    )


# ─────────────────────────────
# 2️⃣ DELETE FED
# ─────────────────────────────

@app.on_message(filters.command("delfed") & filters.private)
async def delete_fed(_, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return await m.reply("❌ ɪɴᴠᴀʟɪᴅ ꜰᴇᴅ")

    if not await is_owner(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ")

    await fedsdb.delete_one({"fed_id": fed["fed_id"]})
    await fedbansdb.delete_many({"fed_id": fed["fed_id"]})

    await m.reply("🗑️ **ꜰᴇᴅᴇʀᴀᴛɪᴏɴ ᴅᴇʟᴇᴛᴇᴅ**")


# ─────────────────────────────
# 3️⃣ RENAME FED
# ─────────────────────────────

@app.on_message(filters.command("renamefed") & filters.private)
async def rename_fed(_, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return await m.reply("❌ ɪɴᴠᴀʟɪᴅ")

    if not await is_owner(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ")

    newname = m.text.split(None, 2)[2]
    await fedsdb.update_one({"fed_id": fed["fed_id"]},
                            {"$set": {"name": newname}})

    await m.reply(f"✏️ {sc('federation renamed')} → {newname}")


# ─────────────────────────────
# 4️⃣ PROMOTE / DEMOTE
# ─────────────────────────────

@app.on_message(filters.command("fpromote") & filters.group)
async def promote(_, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed: return await m.reply("❌ ɴᴏ ꜰᴇᴅ")

    if not await is_owner(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ")

    user = m.reply_to_message.from_user.id
    await fedsdb.update_one({"fed_id": fed["fed_id"]},
                            {"$addToSet": {"admins": user}})

    await m.reply("🛡️ ᴀᴅᴍɪɴ ᴘʀᴏᴍᴏᴛᴇᴅ")


@app.on_message(filters.command("fdemote") & filters.group)
async def demote(_, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed: return

    if not await is_owner(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ")

    user = m.reply_to_message.from_user.id
    await fedsdb.update_one({"fed_id": fed["fed_id"]},
                            {"$pull": {"admins": user}})

    await m.reply("🔻 ᴀᴅᴍɪɴ ᴅᴇᴍᴏᴛᴇᴅ")

# ─────────────────────────────
# 5️⃣ JOIN FED
# ─────────────────────────────

@app.on_message(filters.command("joinfed") & filters.group)
async def join_fed(client, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return await m.reply("❌ ɪɴᴠᴀʟɪᴅ ꜰᴇᴅ ɪᴅ")

    member = await client.get_chat_member(m.chat.id, m.from_user.id)
    if member.status != "creator":
        return await m.reply("⛔ ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ")

    await fedsdb.update_one(
        {"fed_id": fed["fed_id"]},
        {"$addToSet": {"chats": m.chat.id}}
    )

    await m.reply(f"🌍 {sc('group joined federation')}")


# ─────────────────────────────
# 6️⃣ LEAVE FED
# ─────────────────────────────

@app.on_message(filters.command("leavefed") & filters.group)
async def leave_fed(_, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed:
        return await m.reply("❌ ɴᴏ ꜰᴇᴅ")

    await fedsdb.update_one(
        {"fed_id": fed["fed_id"]},
        {"$pull": {"chats": m.chat.id}}
    )

    await m.reply("🚪 ɢʀᴏᴜᴘ ʟᴇꜰᴛ ꜰᴇᴅᴇʀᴀᴛɪᴏɴ")


# ─────────────────────────────
# 7️⃣ FED BAN
# ─────────────────────────────

@app.on_message(filters.command("fedban") & filters.group)
async def fedban(client, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed:
        return await m.reply("❌ ɴᴏ ꜰᴇᴅ")

    if not await is_admin(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ꜰᴇᴅ ᴀᴅᴍɪɴꜱ")

    if not m.reply_to_message:
        return await m.reply("⚠️ ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ")

    user = m.reply_to_message.from_user
    reason = " ".join(m.command[1:]) or "ɴᴏ ʀᴇᴀꜱᴏɴ"

    await fedbansdb.update_one(
        {"fed_id": fed["fed_id"], "user_id": user.id},
        {"$set": {"reason": reason, "time": int(time.time())}},
        upsert=True
    )

    for chat in fed["chats"]:
        try:
            await client.ban_chat_member(chat, user.id)
        except RPCError:
            pass

    await m.reply(
        f"🚫 {sc('federation ban applied')}\n\n"
        f"👤 {user.mention}\n📌 {reason}"
    )


# ─────────────────────────────
# 8️⃣ UNFEDBAN
# ─────────────────────────────

@app.on_message(filters.command("unfedban") & filters.group)
async def unfedban(client, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed:
        return

    if not await is_admin(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ꜰᴇᴅ ᴀᴅᴍɪɴꜱ")

    user = m.reply_to_message.from_user

    await fedbansdb.delete_one(
        {"fed_id": fed["fed_id"], "user_id": user.id}
    )

    for chat in fed["chats"]:
        try:
            await client.unban_chat_member(chat, user.id)
        except RPCError:
            pass

    await m.reply("✅ ᴜꜱᴇʀ ᴜɴꜰᴇᴅʙᴀɴɴᴇᴅ")


# ─────────────────────────────
# 9️⃣ FED BROADCAST
# ─────────────────────────────

@app.on_message(filters.command("fcast") & filters.private)
async def fed_broadcast(client, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return

    if not await is_owner(fed, m.from_user.id):
        return await m.reply("⛔ ᴏɴʟʏ ᴏᴡɴᴇʀ")

    msg = m.text.split(None, 2)[2]

    sent = 0
    for chat in fed["chats"]:
        try:
            await client.send_message(chat, f"📢 **ꜰᴇᴅ ʙʀᴏᴀᴅᴄᴀꜱᴛ**\n\n{msg}")
            sent += 1
        except:
            pass

    await m.reply(f"📤 ᴍᴇꜱꜱᴀɢᴇ ꜱᴇɴᴛ ᴛᴏ {sent} ɢʀᴏᴜᴘꜱ")


# ─────────────────────────────
# 🔟 SET / GET RULES
# ─────────────────────────────

@app.on_message(filters.command("setfedrules") & filters.private)
async def set_rules(_, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return

    if not await is_owner(fed, m.from_user.id):
        return

    rules = m.text.split(None, 2)[2]

    await fedsdb.update_one(
        {"fed_id": fed["fed_id"]},
        {"$set": {"rules": rules}}
    )

    await m.reply("📜 ꜰᴇᴅ ʀᴜʟᴇꜱ ꜱᴇᴛ")


@app.on_message(filters.command("fedrules") & filters.group)
async def get_rules(_, m: Message):
    fed = await get_fed_by_chat(m.chat.id)
    if not fed or not fed.get("rules"):
        return await m.reply("📭 ɴᴏ ʀᴜʟᴇꜱ ꜱᴇᴛ")

    await m.reply(f"📜 **ꜰᴇᴅ ʀᴜʟᴇꜱ**\n\n{fed['rules']}")

# ─────────────────────────────
# FED CHAT LIST
# ─────────────────────────────

@app.on_message(filters.command("fedchats") & filters.private)
async def fed_chats(_, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return

    text = "🌐 **ꜰᴇᴅ ᴄʜᴀᴛꜱ**\n\n"
    for c in fed["chats"]:
        text += f"• `{c}`\n"

    await m.reply(text)


# ─────────────────────────────
# FED ADMIN LIST
# ─────────────────────────────

@app.on_message(filters.command("fedadmins") & filters.private)
async def fed_admins(_, m: Message):
    fed = await get_fed_by_id(m.command[1])
    if not fed:
        return

    text = "🛡️ **ꜰᴇᴅ ᴀᴅᴍɪɴꜱ**\n\n"
    for a in fed["admins"]:
        text += f"• `{a}`\n"

    await m.reply(text)


# ─────────────────────────────
# USER FED STAT
# ─────────────────────────────

@app.on_message(filters.command("fedstat") & filters.private)
async def fed_stat(_, m: Message):
    bans = fedbansdb.find({"user_id": m.from_user.id})

    count = 0
    async for _ in bans:
        count += 1

    await m.reply(f"📊 {sc('you are banned in')} {count} ꜰᴇᴅꜱ")

@app.on_message(filters.command("fedownerhelp"))
async def owner_help(_, m: Message):
    await m.reply("👑 **ꜰᴇᴅ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅꜱ**\n/newfed\n/delfed\n/renamefed\n/fcast\n/setfedrules")

@app.on_message(filters.command("fedadminhelp"))
async def admin_help(_, m: Message):
    await m.reply("🛡️ **ꜰᴇᴅ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ**\n/fedban\n/unfedban")

@app.on_message(filters.command("feduserhelp"))
async def user_help(_, m: Message):
    await m.reply("👥 **ꜰᴇᴅ ᴜꜱᴇʀ ᴄᴏᴍᴍᴀɴᴅꜱ**\n/fedrules\n/fedinfo")
