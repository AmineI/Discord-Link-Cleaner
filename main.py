# This bot requires the 'message_content' intent.

import json
import discord
from discord.ext import commands
import re
import os
from url_sanitize import sanitize

# Configuration
DATA_FOLDER = os.environ.get('DATA_DIR', os.path.dirname(__file__))
CONFIG_PATH = os.path.join(DATA_FOLDER, 'config.json')

# Default config
DEFAULT_CONFIG = {
    "bot_token": "",
    "mention_reply_author": True,
    "regex_keys": "(?i)\\b((?:https?://|www\\.)[^\\s<>\"']+|(?:[a-z0-9-]+\\.)+[a-z]{2,}(?:/[^\\s<>\"']*)?)\\b"
}

# Load or create config
try:
    with open(CONFIG_PATH, 'r', encoding="utf-8") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = DEFAULT_CONFIG
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding="utf-8") as f:
        json.dump(config, f, indent=4)

# Set configuration values
bot_token = os.environ.get("DISCORD_BOT_TOKEN", config.get("bot_token", ""))
mention_reply_author = config.get("mention_reply_author", True)
REGEX = re.compile(config.get("regex_keys", DEFAULT_CONFIG["regex_keys"]))

# Verify url-sanitize binary is available
try:
    sanitize("https://example.com")
except RuntimeError as e:
    if "url-sanitize binary not found" in str(e):
        print("ERROR: url-sanitize binary is not installed!")
        exit(1)
    raise

def clean_url(url):
    """Clean a URL using url-sanitize to remove trackers."""
    try:
        return sanitize(url)
    except Exception as e:
        print(f"Error cleaning URL: {e}")
        return url

intents = discord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    urls = re.findall(REGEX, message.content)
    if not urls:
        return

    sanitized_map = {}
    for url in urls:
        cleaned = clean_url(url)['url']
        if cleaned != url:
            sanitized_map[url] = cleaned
    
    if not sanitized_map:
        return

    try:
        reply = await message.reply(">>>")
        sanitized_message = message.content
        for original, cleaned in sanitized_map.items():
            sanitized_message = sanitized_message.replace(original, cleaned)

        author_mention = f"{message.author.mention} " if mention_reply_author else ""
        await reply.edit(content=f"{author_mention}Your message has been reposted with cleaned URLs (trackers removed):\n{sanitized_message}")
        await message.delete()
    except discord.Forbidden:
        print("Bot lacks permission to delete messages.")
    except Exception as e:
        print(f"Error handling message: {e}")


bot.run(bot_token)