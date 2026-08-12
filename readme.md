# Discord Link Cleaner Bot

A Discord bot that automatically removes tracking parameters from URLs in messages to help protect user privacy. Uses `url-sanitize` for effective URL cleaning.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Setup on Ubuntu](#setup-on-ubuntu)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Features

- Automatically detects URLs in Discord messages
- Removes tracking parameters using url-sanitize
- Deletes original message and reposts with cleaned URLs
- Supports custom URL detection via regex
- Optional author mention when reposting

## Prerequisites

Before you begin, you'll need:

- A Discord application and bot token
- `url-sanitize` binary from https://github.com/antonio-orionus/url-sanitize/releases/latest
- For local setup: Python 3.7+ on Linux/Mac/Windows

## Quick Start with Docker

Docker Compose handles everything automatically:

1. Create `.env` file:
```env
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE
```

2. Run:
```bash
docker compose up --build
```

## Setup on Ubuntu

### 1. Install dependencies
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

### 2. Clone and setup
```bash
git clone https://github.com/StroepWafel/Discord-Link-Cleaner
cd Discord-Link-Cleaner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install url-sanitize binary
```bash
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/antonio-orionus/url-sanitize/releases/latest/download/url-sanitize-installer.sh | sh
```

Verify: `which url-sanitize`

### 4. Set up Discord bot
1. Go to https://discord.com/developers/applications
2. Click "New Application", give it a name
3. Go to "Bot" section, click "Add Bot"
4. Enable "Message Content Intent" (required)
5. Copy bot token
6. Go to "OAuth2" → "URL Generator"
   - Scopes: `bot`
   - Permissions: View Channels, Send Messages, Manage Messages, Read Message History
7. Copy generated URL and use it to invite bot to your server

### 5. Configure and run
```bash
python3 main.py
```

First run creates `config.json`. Edit it with your bot token:
```json
{
    "bot_token": "YOUR_DISCORD_BOT_TOKEN_HERE",
    "mention_reply_author": true,
    "regex_keys": "(?i)\\b((?:https?://|www\\.)[^\\s<>\"']+|(?:[a-z0-9-]+\\.)+[a-z]{2,}(?:/[^\\s<>\"']*)?)\\b"
}
```

Save and run `python3 main.py` again. Bot is now active!

## Usage

The bot automatically:
- Detects URLs in Discord messages
- Sanitizes them using url-sanitize
- Deletes the original message and reposts with cleaned URLs

**Example:**
- Original: `Check this out: https://example.com?utm_source=test&fbclid=123`
- Repost: `Your message has been reposted with cleaned URLs (trackers removed): https://example.com`

## Configuration

Edit `config.json` (auto-created on first run):

**`bot_token`** - Your Discord bot token (required)

**`mention_reply_author`** (boolean, default: `true`) - Whether to mention the original author when reposting

**`regex_keys`** (string) - URL detection regex pattern (defaults provided)

## Troubleshooting

**Bot doesn't respond to messages:**
- Verify bot is online and has proper permissions (View Channels, Send Messages, Manage Messages)
- Ensure "Message Content Intent" is enabled in Discord Developer Portal
- Check bot can find urls in messages using the regex pattern
- Try manually testing: `python3 main.py`

**Bot crashes on startup:**
- Check error message in terminal
- Verify `url-sanitize` binary is installed: `which url-sanitize`
- Ensure bot token is valid in `config.json`

**Permission errors:**
- Give bot "Manage Messages" permission to delete/repost messages
- Ensure bot has proper channel permissions

## Security

- **Never share your bot token** - Keep `config.json` private
- Regenerate token if accidentally exposed: https://discord.com/developers/applications
- Only give the bot the minimum permissions needed
- `config.json` is automatically excluded from git

## License

See LICENSE file for details.
