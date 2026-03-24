"""GitHub-based persistent storage for channels.json in illyassvvv/G repo.

Data format:
{
  "categories": [
    {
      "name": "beIN Sports",
      "icon": "sports_soccer",
      "channels": [
        {"id": 1, "name": "beIN Sports 1", "number": "01", "logo": "...", "stream": "..."}
      ]
    }
  ]
}

Categories are identified by their list index (cat_idx).
Channels are identified by their "id" field (ch_id).
"""

import base64
import json
import logging
from typing import Any

import httpx

from config import GITHUB_BRANCH, GITHUB_FILE_PATH, GITHUB_REPO, GITHUB_TOKEN

logger = logging.getLogger(__name__)

_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def _fetch() -> tuple[dict[str, Any], str]:
    """Fetch channels.json from GitHub. Returns (data, sha)."""
    resp = httpx.get(_API_BASE, headers=_HEADERS, params={"ref": GITHUB_BRANCH})
    resp.raise_for_status()
    info = resp.json()
    content = base64.b64decode(info["content"]).decode("utf-8")
    return json.loads(content), info["sha"]


def _push(data: dict[str, Any], sha: str, message: str) -> None:
    """Push updated channels.json to GitHub."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    body = {
        "message": message,
        "content": encoded,
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }
    resp = httpx.put(_API_BASE, headers=_HEADERS, json=body)
    resp.raise_for_status()


# --------------- Categories ---------------


def get_categories() -> list[dict[str, Any]]:
    """Return all categories as a list."""
    data, _ = _fetch()
    return data.get("categories", [])


def get_category(cat_idx: int) -> dict[str, Any] | None:
    """Get a single category by index."""
    cats = get_categories()
    if 0 <= cat_idx < len(cats):
        return cats[cat_idx]
    return None


def add_category(name: str, icon: str = "tv") -> int:
    """Add a new category. Returns the category index."""
    data, sha = _fetch()
    cats = data.setdefault("categories", [])
    cats.append({"name": name, "icon": icon, "channels": []})
    _push(data, sha, f"Add category: {name}")
    return len(cats) - 1


def rename_category(cat_idx: int, new_name: str) -> bool:
    """Rename a category."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    cats[cat_idx]["name"] = new_name
    _push(data, sha, f"Rename category to: {new_name}")
    return True


def update_category_icon(cat_idx: int, new_icon: str) -> bool:
    """Update a category's icon."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    cats[cat_idx]["icon"] = new_icon
    _push(data, sha, f"Update icon for: {cats[cat_idx]['name']}")
    return True


def delete_category(cat_idx: int) -> bool:
    """Delete a category."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    removed = cats.pop(cat_idx)
    _push(data, sha, f"Delete category: {removed['name']}")
    return True


# --------------- Channels ---------------


def _next_channel_id(data: dict[str, Any]) -> int:
    """Find the next available channel ID across all categories."""
    max_id = 0
    for cat in data.get("categories", []):
        for ch in cat.get("channels", []):
            if ch.get("id", 0) > max_id:
                max_id = ch["id"]
    return max_id + 1


def get_channels(cat_idx: int) -> list[dict[str, Any]]:
    """Return all channels in a category."""
    cat = get_category(cat_idx)
    if cat is None:
        return []
    return cat.get("channels", [])


def get_channel(cat_idx: int, ch_id: int) -> dict[str, Any] | None:
    """Get a single channel by category index and channel id."""
    channels = get_channels(cat_idx)
    for ch in channels:
        if ch.get("id") == ch_id:
            return ch
    return None


def add_channel(
    cat_idx: int,
    name: str,
    number: str,
    logo: str,
    stream: str,
) -> int | None:
    """Add a channel to a category. Returns channel ID or None on failure."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return None
    ch_id = _next_channel_id(data)
    cats[cat_idx].setdefault("channels", []).append({
        "id": ch_id,
        "name": name,
        "number": number,
        "logo": logo,
        "stream": stream,
    })
    _push(data, sha, f"Add channel: {name}")
    return ch_id


def update_channel_stream(cat_idx: int, ch_id: int, stream: str) -> bool:
    """Update a channel's stream link."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    for ch in cats[cat_idx].get("channels", []):
        if ch.get("id") == ch_id:
            ch["stream"] = stream
            _push(data, sha, f"Update stream for: {ch['name']}")
            return True
    return False


def update_channel_logo(cat_idx: int, ch_id: int, logo: str) -> bool:
    """Update a channel's logo URL."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    for ch in cats[cat_idx].get("channels", []):
        if ch.get("id") == ch_id:
            ch["logo"] = logo
            _push(data, sha, f"Update logo for: {ch['name']}")
            return True
    return False


def update_channel_name(cat_idx: int, ch_id: int, name: str) -> bool:
    """Update a channel's name."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    for ch in cats[cat_idx].get("channels", []):
        if ch.get("id") == ch_id:
            ch["name"] = name
            _push(data, sha, f"Rename channel to: {name}")
            return True
    return False


def update_channel_number(cat_idx: int, ch_id: int, number: str) -> bool:
    """Update a channel's number."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    for ch in cats[cat_idx].get("channels", []):
        if ch.get("id") == ch_id:
            ch["number"] = number
            _push(data, sha, f"Update number for: {ch['name']}")
            return True
    return False


def delete_channel(cat_idx: int, ch_id: int) -> bool:
    """Delete a channel from a category."""
    data, sha = _fetch()
    cats = data.get("categories", [])
    if cat_idx < 0 or cat_idx >= len(cats):
        return False
    channels = cats[cat_idx].get("channels", [])
    for i, ch in enumerate(channels):
        if ch.get("id") == ch_id:
            channels.pop(i)
            _push(data, sha, f"Delete channel: {ch['name']}")
            return True
    return False
