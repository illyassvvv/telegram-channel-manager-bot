"""Bot configuration."""

import os
import sys

# Bot token from BotFather (required)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is required.")
    sys.exit(1)

# Admin user ID (required)
_admin_id = os.environ.get("ADMIN_ID", "")
if not _admin_id:
    print("ERROR: ADMIN_ID environment variable is required.")
    sys.exit(1)
ADMIN_ID = int(_admin_id)

# Data file path
DATA_FILE = os.environ.get("DATA_FILE", "data.json")
