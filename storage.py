"""JSON-based persistent storage for bot data."""

import json
import os
import uuid
from typing import Any

from config import DATA_FILE


def _load() -> dict[str, Any]:
    """Load data from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {"categories": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict[str, Any]) -> None:
    """Save data to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _gen_id() -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:8]


# --------------- Categories ---------------

def get_categories() -> dict[str, Any]:
    """Return all categories: {cat_id: {name, channels: {...}}}."""
    data = _load()
    return data.get("categories", {})


def add_category(name: str) -> str:
    """Add a new category. Returns the category ID."""
    data = _load()
    cat_id = _gen_id()
    data.setdefault("categories", {})[cat_id] = {"name": name, "channels": {}}
    _save(data)
    return cat_id


def rename_category(cat_id: str, new_name: str) -> bool:
    """Rename a category. Returns True on success."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return False
    cat["name"] = new_name
    _save(data)
    return True


def delete_category(cat_id: str) -> bool:
    """Delete a category. Returns True on success."""
    data = _load()
    if cat_id in data.get("categories", {}):
        del data["categories"][cat_id]
        _save(data)
        return True
    return False


def get_category(cat_id: str) -> dict[str, Any] | None:
    """Get a single category by ID."""
    data = _load()
    return data.get("categories", {}).get(cat_id)


# --------------- Channels ---------------

def get_channels(cat_id: str) -> dict[str, Any]:
    """Return all channels in a category."""
    cat = get_category(cat_id)
    if cat is None:
        return {}
    return cat.get("channels", {})


def add_channel(
    cat_id: str,
    name: str,
    stream_link: str,
    picture_file_id: str,
    picture_url: str,
) -> str | None:
    """Add a channel to a category. Returns channel ID or None on failure."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return None
    ch_id = _gen_id()
    cat.setdefault("channels", {})[ch_id] = {
        "name": name,
        "stream_link": stream_link,
        "picture_file_id": picture_file_id,
        "picture_url": picture_url,
    }
    _save(data)
    return ch_id


def get_channel(cat_id: str, ch_id: str) -> dict[str, Any] | None:
    """Get a single channel."""
    cat = get_category(cat_id)
    if cat is None:
        return None
    return cat.get("channels", {}).get(ch_id)


def update_channel_stream(cat_id: str, ch_id: str, stream_link: str) -> bool:
    """Update a channel's stream link."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return False
    ch = cat.get("channels", {}).get(ch_id)
    if ch is None:
        return False
    ch["stream_link"] = stream_link
    _save(data)
    return True


def update_channel_picture(
    cat_id: str, ch_id: str, picture_file_id: str, picture_url: str
) -> bool:
    """Update a channel's picture."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return False
    ch = cat.get("channels", {}).get(ch_id)
    if ch is None:
        return False
    ch["picture_file_id"] = picture_file_id
    ch["picture_url"] = picture_url
    _save(data)
    return True


def update_channel_name(cat_id: str, ch_id: str, name: str) -> bool:
    """Update a channel's name."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return False
    ch = cat.get("channels", {}).get(ch_id)
    if ch is None:
        return False
    ch["name"] = name
    _save(data)
    return True


def delete_channel(cat_id: str, ch_id: str) -> bool:
    """Delete a channel from a category."""
    data = _load()
    cat = data.get("categories", {}).get(cat_id)
    if cat is None:
        return False
    if ch_id in cat.get("channels", {}):
        del cat["channels"][ch_id]
        _save(data)
        return True
    return False
