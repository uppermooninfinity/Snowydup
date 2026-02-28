import uuid
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError
from config import MONGO_URL, OWNER_ID
from yourbot import app

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.federation

feds_col = db.feds
users_col = db.fed_users
bans_col = db.fed_bans


# =====================================================
# Helper Functions
# =====================================================

async def get_fed(chat_id: int):
    return await feds_col.find_one({"chats": chat_id})


async def is_fed_admin(fed_id: str, user_id: int):
    fed = await feds_col.find_one({"fed_id": fed_id})
    if not fed:
        return False
    return user_id == fed["owner"] or user_id in fed.get("admins", [])


# =====================================================
# CREATE FEDERATION (PRIVATE)
# =====================================================

@app.on_message(filters.command("newfed") & filters.private)
async def new_fed(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /newfed Federation Name")

    fed_name = message.text.split(None, 1)[1]
    fed_id = str(uuid.uuid4())

    await feds_col.insert_one({
        "fed_id": fed_id,
        "name": fed_name,
        "owner": message.from_user.id,
        "admins": [],
        "chats": [],
        "created": int(time.time())
    })

    await message.reply_text(
        f"**Federation Created**\n\n"
        f"Name: {fed_name}\n"
        f"ID: `{fed_id}`\n\n"
        f"Use in group:\n`/joinfed {fed_id}`"
    )


# =====================================================
# JOIN FEDERATION
# =====================================================

@app.on_message(filters.command("joinfed") & filters.group)
async def join_fed(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Provide federation ID")

    fed_id = message.command[1]
    fed = await feds_col.find_one({"fed_id": fed_id})
    if not fed:
        return await message.reply_text("Invalid federation ID")

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status != "creator":
        return await message.reply_text("Only group creator can join federation")

    if message.chat.id in fed["chats"]:
        return await message.reply_text("Already joined")

    await feds_col.update_one(
        {"fed_id": fed_id},
        {"$push": {"chats": message.chat.id}}
    )

    await message.reply_text(f"Joined federation {fed['name']}")


# =====================================================
# LEAVE FEDERATION
# =====================================================

@app.on_message(filters.command("leavefed") & filters.group)
async def leave_fed(client: Client, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("Not in federation")

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status != "creator":
        return await message.reply_text("Only creator can leave")

    await feds_col.update_one(
        {"fed_id": fed["fed_id"]},
        {"$pull": {"chats": message.chat.id}}
    )

    await message.reply_text("Left federation")


# =====================================================
# FED INFO
# =====================================================

@app.on_message(filters.command("fedinfo") & filters.group)
async def fed_info(client: Client, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("This group is not in federation")

    owner = await client.get_users(fed["owner"])
    total_bans = await bans_col.count_documents({"fed_id": fed["fed_id"]})

    text = (
        f"**Federation Info**\n\n"
        f"Name: {fed['name']}\n"
        f"ID: `{fed['fed_id']}`\n"
        f"Owner: {owner.mention}\n"
        f"Admins: `{len(fed['admins'])}`\n"
        f"Groups: `{len(fed['chats'])}`\n"
        f"Banned Users: `{total_bans}`"
    )

    await message.reply_text(text)


# =====================================================
# PROMOTE FED ADMIN
# =====================================================

@app.on_message(filters.command("fpromote") & filters.group)
async def promote_fed(_, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("Not in federation")

    if message.from_user.id != fed["owner"]:
        return await message.reply_text("Only federation owner")

    if not message.reply_to_message:
        return await message.reply_text("Reply to user")

    user_id = message.reply_to_message.from_user.id

    await feds_col.update_one(
        {"fed_id": fed["fed_id"]},
        {"$addToSet": {"admins": user_id}}
    )

    await message.reply_text("Promoted to Fed Admin")


# =====================================================
# FED BAN
# =====================================================

@app.on_message(filters.command("fedban") & filters.group)
async def fedban(client: Client, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("Not in federation")

    if not await is_fed_admin(fed["fed_id"], message.from_user.id):
        return await message.reply_text("Only fed admins")

    if not message.reply_to_message:
        return await message.reply_text("Reply to user")

    target = message.reply_to_message.from_user
    reason = " ".join(message.command[1:]) or "No reason"

    if target.id == OWNER_ID:
        return await message.reply_text("Cannot ban owner")

    await bans_col.update_one(
        {"fed_id": fed["fed_id"], "user_id": target.id},
        {"$set": {
            "reason": reason,
            "time": int(time.time())
        }},
        upsert=True
    )

    for chat_id in fed["chats"]:
        try:
            await client.ban_chat_member(chat_id, target.id)
        except RPCError:
            pass

    await message.reply_text(
        f"FedBan applied\nUser: {target.mention}\nReason: {reason}"
    )


# =====================================================
# UNFEDBAN
# =====================================================

@app.on_message(filters.command("unfedban") & filters.group)
async def unfedban(client: Client, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("Not in federation")

    if not await is_fed_admin(fed["fed_id"], message.from_user.id):
        return await message.reply_text("Only fed admins")

    if not message.reply_to_message:
        return await message.reply_text("Reply to user")

    target = message.reply_to_message.from_user

    await bans_col.delete_one({
        "fed_id": fed["fed_id"],
        "user_id": target.id
    })

    for chat_id in fed["chats"]:
        try:
            await client.unban_chat_member(chat_id, target.id)
        except RPCError:
            pass

    await message.reply_text(f"{target.mention} UnFedBanned")


# =====================================================
# FED BAN LIST
# =====================================================

@app.on_message(filters.command("fedbans") & filters.group)
async def fedbans(_, message: Message):
    fed = await get_fed(message.chat.id)
    if not fed:
        return await message.reply_text("Not in federation")

    bans = bans_col.find({"fed_id": fed["fed_id"]})
    text = f"**Fed Ban List - {fed['name']}**\n\n"

    count = 0
    async for ban in bans:
        text += f"• `{ban['user_id']}` - {ban['reason']}\n"
        count += 1

    if count == 0:
        text += "No banned users"

    await message.reply_text(text)
