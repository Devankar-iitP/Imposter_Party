"""
update.message --> only contains data if user actually typed text message, sent photo or sent voice note.
If bot receives different interaction --> update.message will be None --> accessing it will instantly crash our bot

    Eg - user clicks an inline keyboard button attached to a message
        or user answers a poll your bot sent
        or system event happens (like a user joining or leaving the group)

update.effective_chat --> safely handles issue of update.message => When event happens, library automatically 
searches entire incoming data payload --> "I don't care if this is text message, button click, photo, or poll. 
I will hunt down whatever chat this event happened in and return it"

When an event happens, the library automatically searches the entire incoming data payload. Even if the event was a button click (which technically happens inside a CallbackQuery, not a Message), the library hunts down the chat ID where that button was clicked and safely hands it to you through update.effective_chat.id.
Inline mode --> feature where type bot's username + query into text box (e.g., @gif dog), but you don't hit send
                Instead of sending message to chat --> menu pops up above keyboard showing live results (
                Bot doesn't need to be member of group for this to work
                Eg - photo of dog => When tap result -> send that item directly into chat as if you sent it yourself


Currently no handlers in this code --> track live data 
Eg - MessageHandler --> for messages
     PollAnswerHandler --> for polls
"""

import asyncio
import os
import random
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, filters, ContextTypes
from dotenv import load_dotenv
import logic
import telegram_client

load_dotenv()

TOKEN = os.getenv("TOKEN")
BOT_USERNAME = '@Imposter_Party_33_Bot'
GROUP_FILTER = filters.ChatType.GROUPS


# Every handler in python-telegram-bot must have exactly 2 arguments — update and context 
# even if you don't use context in the code block
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ""
    if update.effective_chat.type in ["group", "supergroup"]:   # if inside group
        message = """🎭 Welcome to the game, where everyone knows the word... except one.
Trust wisely, speak cleverly, and find the imposter before it's too late!👁️

Type / to explore all commands.
"""
    else:   # If inside personal DMs
        message = """This bot works only in Group Chats. So, make Group with your friends and add this bot in that group.
Also, don't forget to give admin permissions to bot for smooth functioning of game.

Type /start to get started inside group.
"""
    await update.message.reply_text(message)



async def rule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message="""*🎭 Game Rules: Find the Imposter*

*👥 Players*
• Minimum *3 players* (best with 6-10)
• *1 Imposter*, rest are *Normal Players*.

*🎯 Objective*
• *Normal Players:* Identify and vote out the imposter.
• *Imposter:* Blend in, avoid getting caught till the end.

*🃏 Setup*
• *Normal Players:* All receive the *same word*.
• *Imposter:* Gets a vague *hint related to that word* (not the word itself)

*🔄 Gameplay (Round-Based)*

*🗣️ 1. Hint Round*
• Players take turns giving *one hint* about the word.
• Keep it *subtle*:
  ◦ Too obvious ➡️ helps imposter
  ◦ Too vague ➡️ makes you suspicious
• The *Imposter* must fake it using:
  ◦ Their given hint and clues from other players

*🗳️ 2. Voting*
• After everyone speaks, players *vote* for who they think is the imposter.
• Player with the *most votes is eliminated*.

*🧾 3. Reveal*
• The eliminated player's role is revealed:
  ◦ If *Imposter* ➡️ Game ends (Normal players win 🎉)
  ◦ If *Not Imposter* ➡️ Game continues

*🔁 Rounds Limit*
• If more than 4 players ➡️ Game continues for maximum of *3 rounds*
• Else Game continues for maximum of *rounds = number of players - 2* • Example ➡️ total 4 players ➡️ maximum of 2 rounds

*🏁 Winning Conditions*
• ✅ *Normal Players Win:* If imposter is voted out
• 😈 *Imposter Wins:* If smart enough to survive all rounds
"""
    await update.message.reply_text(message, parse_mode='Markdown')     # Only support bold and italics



async def send_dm(context, member, word, is_imposter = False):
    text = ""
    if is_imposter:
        text = f"😈Hey Imposter ! \nYour hint is : {word}"
    else:
        text = f"🎭 Hey @{member.username}! \nYour secret word is: {word}"
    try:
        await context.bot.send_message(chat_id=member.id, text=text)
    except Exception:
        return f"@{member.username}"
    return None


async def members_list(update: Update, chat_id):
    # For massive groups --> pass parameters like limit=1000
    all_members = await telegram_client.client.get_participants(chat_id)
    
    members = [member for member in all_members if not member.bot]
    if len(members) < 3:
        await update.message.reply_text("At least 3 players are needed to play this game.")
        return None
    
    return members


async def begin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    members = await members_list(update, update.effective_chat.id)
    if members is None:
        return
    
    message = """⏳ Get ready... the game is about to begin.
Think smart, speak subtle, and don't get exposed 👀

Check your DMs 🙃
"""
    await update.message.reply_text(message)
    

    random.shuffle(members)
    result = await send_dm(context, members[-1], logic.random_hint, True)
    members.pop()

    tasks = [asyncio.create_task(send_dm(context, member, logic.random_word)) for member in members]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    results.append(result)
    
    failed = [r for r in results if r is not None]
    if failed:
        await update.message.reply_text(
            f"⚠️ Couldn't DM these users (they need to /start the bot privately first):\n" + "\n".join(failed)
        )



async def vote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    members = await members_list(update, chat_id)
    if members is None:
        return

    if len(members) > 10:
        await update.message.reply_text("Voting can be done for maximum of 10 players. Do manual voting.")
        return

    await update.message.reply_text("Voting will last only for 5 seconds. Be quick !!")
    options = []
    for member in members:
        if member.first_name:
            options.append(f"{member.first_name} {member.last_name or ''}".strip())
        else:
            options.append(member.username)

    poll = await context.bot.send_poll(
        chat_id=chat_id,
        question="🕵️ Who do you think is the Imposter?",
        options=options,
        is_anonymous=False,   # False = you can see who voted for whom
        allows_multiple_answers=False
    )

    await asyncio.sleep(5)
    final_poll = await context.bot.stop_poll(chat_id=chat_id, message_id=poll.message_id)
    result = max(final_poll.options, key=lambda option: option.voter_count).text
    
    await update.message.reply_text(result)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'{update} caused error : {context.error}', flush=True)


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('rule', rule_command))

    app.add_handler(CommandHandler('begin', begin_command, filters=GROUP_FILTER))    # Allowed only from group chat
    app.add_handler(CommandHandler('vote', vote_command, filters=GROUP_FILTER))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)