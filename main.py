# This bot requires the 'message_content' intent.

import json
import discord
from discord.ext import commands
import re
import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from url_sanitize import sanitize

# Configuration
DATA_FOLDER = os.environ.get('DATA_DIR', os.path.dirname(__file__))
CONFIG_PATH = os.path.join(DATA_FOLDER, 'config.json')

# Default config; each key can be overridden by an environment variable of the same name, in caps
DEFAULT_CONFIG = {
    "bot_token": "",
    "repost_message": "Your message has been reposted with cleaned URLs (trackers removed):\n>>> {message}",
    "regex_keys": "(?i)\\b((?:https?://|www\\.)[^\\s<>\"']+|(?:[a-z0-9-]+\\.)+[a-z]{2,}(?:/[^\\s<>\"']*)?)\\b",
    # Additional query params to parse, not (yet) stripped by url-sanitize, e.g. Instagram's igsi
    "extra_tracking_params": ["igsi"]
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


def get_setting(key):
    """Resolve a setting: the <KEY> env var (if set) overrides config.json, which overrides the built-in default."""
    env_value = os.environ.get(key.upper(), "").strip()
    if env_value:
        return env_value
    return config.get(key, DEFAULT_CONFIG[key])


# Set configuration values
bot_token = get_setting("bot_token")
REGEX = re.compile(get_setting("regex_keys"))
extra_tracking_params = get_setting("extra_tracking_params")
#if extra_tracking_params is text, make it an array
if isinstance(extra_tracking_params, str):
    extra_tracking_params = [p.strip() for p in extra_tracking_params.split(",") if p.strip()]
EXTRA_TRACKING_PARAMS = {p.lower() for p in extra_tracking_params}
REPOST_MESSAGE = get_setting("repost_message")
if "{message}" not in REPOST_MESSAGE:
    REPOST_MESSAGE += "\n>>> {message}"

# Verify url-sanitize binary is available
try:
    sanitize("https://example.com")
except RuntimeError as e:
    if "url-sanitize binary not found" in str(e):
        print("ERROR: url-sanitize binary is not installed!")
        exit(1)
    raise

def strip_extra_params(url):
    """Remove tracking params not handled by url-sanitize."""
    if not EXTRA_TRACKING_PARAMS:
        return url
    parts = urlsplit(url)
    if not parts.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in EXTRA_TRACKING_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(kept)))

def clean_url(url):
    """Clean a URL using url-sanitize to remove trackers."""
    try:
        result = sanitize(url)
        result['url'] = strip_extra_params(result['url'])
        return result
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

        author_mention = f"{message.author.mention} "
        repost_message = REPOST_MESSAGE.format(message=sanitized_message)
        await reply.edit(content=f"{author_mention}{repost_message}")
        await message.delete()
    except discord.Forbidden:
        print("Bot lacks permission to delete messages.")
    except Exception as e:
        print(f"Error handling message: {e}")


bot.run(bot_token)