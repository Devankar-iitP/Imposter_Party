"""
    Telethon is used to send messages on Telegram using only on username. 
--> open-source library built by community on top of Telegram's MTProto protocol (same protocol official app uses)
--> safe as everything goes directly to Telegram's servers
--> since use MTProto (persistent TCP connection to Telegram's servers) 
    This is NOT HTTP polling and already event-driven + connection-based

NOTE - Telegram aggressively detects and bans accounts that mass-message users
       Sending messages to same user --> 1 msg/second
       Sending to different users --> 30 msg/second

Telegram uses a dynamic flood wait system --> If you hit limit => send back FloodWaitError with wait time in seconds
NOTE - FloodWaitError is not failure -> means "wait, then you're fine" 
       During bulk send, may possible that you need to run "send_message" fxn finite multiple times

"""

import asyncio
import os
import random
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError
from telethon.sessions import StringSession
from dotenv import load_dotenv
import logic

load_dotenv()  # Loads variables from .env file

API_ID   = int(os.getenv("API_ID"))     # Convert to int (required by Telethon)
API_HASH = os.getenv("API_HASH")
TOKEN    = os.getenv("TOKEN")

client = TelegramClient("", API_ID, API_HASH)   # No authentication --> so bot can login


async def get_name(username: str):
    try:
        user = await client.get_entity(username)
        if user.first_name:
            return f"{user.first_name} {user.last_name or ''}".strip()
        return username

    except Exception as e:
        print(f"❌ Could not fetch user to get_name: {e}", flush=True)
        return "Not Found"


async def send_message(username: str, text: str):
    # can get FloodWaitError again after waiting for e seconds --> retry finite times
    name = await get_name(username)
    while True:
        try:
            await client.send_message(username, text)
            print(f"✅ Message sent to {name}", flush=True)
            break

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

        except UserPrivacyRestrictedError:
            print(f"🔒 {username} has restricted who can message them.", flush=True)
            break
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
            break


async def send_messages_bulk(targets: list, text: str, delay: float = 2.0):
    tasks = [asyncio.create_task(send_message(username, text)) for username in targets]
    await asyncio.gather(*tasks, return_exceptions=True)


# user.bot returns True if username belongs to bot
# user.phone --> only if they are in your contacts
async def get_user_info(username: str):
    try:
        user = await client.get_entity(username)
        print(f"""
👤 User Info
───────────────────
ID       : {user.id}
Name     : {user.first_name} {user.last_name or ''}
Username : @{user.username}
Phone    : {user.phone or 'Hidden'}
Bot      : {user.bot}
        """)

    except Exception as e:
        print(f"❌ Could not fetch user: {e}")


async def send_file(username: str, file_path: str, caption: str = ""):
    name = await get_name(username)
    try:
        await client.send_file(username, file_path, caption=caption)
        print(f"✅ File sent to {name}")

    except Exception as e:
        print(f"❌ Error sending file: {e}")


async def get_recent_messages(username: str, limit: int = 10):
    print(f"\n📜 Last {limit} messages with {username}:\n")
    async for message in client.iter_messages(username, limit=limit):
        direction = "➡️ You" if message.out else "⬅️ Them"
        print(f"{direction}: {message.text}")


async def main():
    await client.start(bot_token=TOKEN)     # So, we get normal names and not from contacts
    print("✅ Logged in successfully!\n")

    # # Send a single message
    # await send_message("@GCSE_9693", "Hello from Telethon!")

    # Get user info
    await get_user_info("@GCSE_9693")

    # # Send to multiple users
    # targets = ["@user1", "@user2", "@user3"]
    # random.shuffle(targets)
    # imposter = targets[-1]
    # word, hint = logic.get_random_word()
    # await send_message(imposter, hint)

    # targets.pop()
    # await send_messages_bulk(targets, word)

    # # Send a file
    # await send_file("@GCSE_9693", r"E:\Downloads\Anime One Piece HD Wallpaper.jpeg", caption="Testing !")

    # # Read recent messages
    # await get_recent_messages("@someusername")

    await client.disconnect()       # cleanly disconnects before exiting

if __name__ == "__main__":
    asyncio.run(main())