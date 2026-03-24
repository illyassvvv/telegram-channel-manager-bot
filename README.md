# Telegram Channel Manager Bot

A Telegram bot for managing channel categories with stream links and pictures.

## Features

- **Categories**: Create, rename, and delete categories (e.g., "News Channels", "Sports Channels")
- **Channels**: Add channels within categories, each with:
  - Channel name
  - Stream link (URL)
  - Picture (image)
- **Edit**: Update stream links, pictures, and channel names at any time
- **Raw Picture URL**: Get the raw Telegram file URL for any channel's picture
- **Admin Only**: Only the configured admin user can interact with the bot

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables (optional, defaults are in `config.py`):

```bash
export BOT_TOKEN="your-bot-token"
export ADMIN_ID="your-telegram-user-id"
```

3. Run the bot:

```bash
python bot.py
```

## Bot Commands

- `/start` - Open the main menu
- `/cancel` - Cancel the current operation

## How to Use

1. Send `/start` to the bot
2. Use **Categories** to view existing categories or **Add Category** to create a new one
3. Inside a category, you can:
   - View and manage channels
   - Add new channels (name + stream link + picture)
   - Rename or delete the category
4. Inside a channel, you can:
   - Edit the stream link
   - Edit the picture
   - Edit the channel name
   - Get the raw picture URL
   - Delete the channel

## Data Storage

All data is stored locally in a `data.json` file. The bot creates this file automatically on first use.
