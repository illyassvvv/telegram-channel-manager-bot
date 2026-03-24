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

# GitHub config for channels.json storage (required)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable is required.")
    sys.exit(1)
GITHUB_REPO = os.environ.get("GITHUB_REPO", "illyassvvv/G")
GITHUB_FILE_PATH = os.environ.get("GITHUB_FILE_PATH", "channels.json")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
