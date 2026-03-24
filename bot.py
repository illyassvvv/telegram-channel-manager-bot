"""
Telegram Channel Manager Bot

Manage channel categories with stream links and logos.
Reads/writes channels.json in the illyassvvv/G GitHub repo.
Only the configured admin user can interact with this bot.
"""

import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import storage
from config import ADMIN_ID, BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
(
    MAIN_MENU,
    CAT_LIST,
    CAT_MENU,
    ADD_CAT_NAME,
    ADD_CAT_ICON,
    RENAME_CAT,
    EDIT_CAT_ICON,
    CH_LIST,
    CH_MENU,
    ADD_CH_NAME,
    ADD_CH_NUMBER,
    ADD_CH_STREAM,
    ADD_CH_LOGO,
    EDIT_CH_STREAM,
    EDIT_CH_LOGO,
    EDIT_CH_NAME,
    EDIT_CH_NUMBER,
    CONFIRM_DEL_CAT,
    CONFIRM_DEL_CH,
) = range(19)


# --------------- Helpers ---------------


def admin_only(func):
    """Decorator: only allow the admin user."""
    async def wrapper(update: Update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            if update.callback_query:
                await update.callback_query.answer("Access denied.", show_alert=True)
            else:
                await update.effective_message.reply_text("Access denied.")
            return ConversationHandler.END
        return await func(update, *args, **kwargs)
    return wrapper


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Categories", callback_data="categories")],
        [InlineKeyboardButton("➕ Add Category", callback_data="add_category")],
    ])


def categories_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard listing all categories."""
    cats = storage.get_categories()
    buttons = []
    for idx, cat in enumerate(cats):
        buttons.append([
            InlineKeyboardButton(
                f"📁 {cat['name']}",
                callback_data=f"cat:{idx}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def category_menu_keyboard(cat_idx: int) -> InlineKeyboardMarkup:
    """Build the menu for a single category."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Channels", callback_data=f"channels:{cat_idx}")],
        [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_idx}")],
        [InlineKeyboardButton("✏️ Rename Category", callback_data=f"rename_cat:{cat_idx}")],
        [InlineKeyboardButton("🎨 Edit Icon", callback_data=f"edit_icon:{cat_idx}")],
        [InlineKeyboardButton("🗑 Delete Category", callback_data=f"del_cat:{cat_idx}")],
        [InlineKeyboardButton("🔙 Back", callback_data="categories")],
    ])


def channels_keyboard(cat_idx: int) -> InlineKeyboardMarkup:
    """Build a keyboard listing all channels in a category."""
    channels = storage.get_channels(cat_idx)
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                f"📺 {ch['name']}",
                callback_data=f"ch:{cat_idx}:{ch['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_idx}")])
    return InlineKeyboardMarkup(buttons)


def channel_menu_keyboard(cat_idx: int, ch_id: int) -> InlineKeyboardMarkup:
    """Build the menu for a single channel."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Edit Stream Link", callback_data=f"edit_stream:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("🖼 Edit Logo URL", callback_data=f"edit_logo:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_chname:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("🔢 Edit Number", callback_data=f"edit_chnum:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("📋 Get Raw Logo URL", callback_data=f"raw_logo:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("🗑 Delete Channel", callback_data=f"del_ch:{cat_idx}:{ch_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"channels:{cat_idx}")],
    ])


def _channel_info_text(ch: dict) -> str:
    """Format channel info text."""
    return (
        f"📺 <b>{html.escape(ch['name'])}</b>\n\n"
        f"🔢 Number: {html.escape(ch.get('number', ''))}\n"
        f"🔗 Stream: {html.escape(ch.get('stream', ''))}\n"
        f"🖼 Logo: {html.escape(ch.get('logo', 'None'))}"
    )


async def send_or_edit(update: Update, text: str, reply_markup=None, parse_mode=None):
    """Edit the current message if from a callback, otherwise send a new one."""
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode,
            )
        except Exception:
            await update.effective_chat.send_message(
                text, reply_markup=reply_markup, parse_mode=parse_mode,
            )
    else:
        await update.effective_message.reply_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode,
        )


# --------------- /start ---------------


@admin_only
async def start(update: Update, context) -> int:
    """Handle /start command."""
    context.user_data.clear()
    await send_or_edit(
        update,
        "👋 <b>Channel Manager Bot</b>\n\n"
        "Manage your channel categories, stream links, and logos.\n"
        "Data is stored in your GitHub repo.\n\n"
        "Choose an option below:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    return MAIN_MENU


# --------------- Main Menu ---------------


@admin_only
async def main_menu_handler(update: Update, context) -> int:
    """Handle main menu button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "categories":
        cats = storage.get_categories()
        if not cats:
            await send_or_edit(
                update,
                "📂 <b>Categories</b>\n\nNo categories yet. Add one first!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Category", callback_data="add_category")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
                ]),
                parse_mode="HTML",
            )
            return CAT_LIST
        await send_or_edit(
            update,
            "📂 <b>Categories</b>\n\nSelect a category:",
            reply_markup=categories_keyboard(),
            parse_mode="HTML",
        )
        return CAT_LIST

    if data == "add_category":
        await send_or_edit(
            update,
            "➕ <b>Add Category</b>\n\nSend me the name for the new category:",
            parse_mode="HTML",
        )
        return ADD_CAT_NAME

    return MAIN_MENU


# --------------- Category List ---------------


@admin_only
async def cat_list_handler(update: Update, context) -> int:
    """Handle category list interactions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await send_or_edit(
            update,
            "👋 <b>Channel Manager Bot</b>\n\nChoose an option:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return MAIN_MENU

    if data == "add_category":
        await send_or_edit(
            update,
            "➕ <b>Add Category</b>\n\nSend me the name for the new category:",
            parse_mode="HTML",
        )
        return ADD_CAT_NAME

    if data.startswith("cat:"):
        cat_idx = int(data.split(":")[1])
        cat = storage.get_category(cat_idx)
        if cat is None:
            await send_or_edit(update, "Category not found.")
            return MAIN_MENU
        context.user_data["cat_idx"] = cat_idx
        channels = storage.get_channels(cat_idx)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n"
            f"🎨 Icon: {html.escape(cat.get('icon', ''))}\n"
            f"📺 Channels: {len(channels)}\n\n"
            "Choose an action:",
            reply_markup=category_menu_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CAT_MENU

    return CAT_LIST


# --------------- Add Category ---------------


@admin_only
async def add_cat_name(update: Update, context) -> int:
    """Receive category name."""
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return ADD_CAT_NAME
    context.user_data["new_cat_name"] = name
    await update.message.reply_text(
        f"Category: <b>{html.escape(name)}</b>\n\n"
        "Now send me the icon name (e.g. sports_soccer, tv, movie).\n"
        "Or send /skip to use default (tv):",
        parse_mode="HTML",
    )
    return ADD_CAT_ICON


@admin_only
async def add_cat_icon(update: Update, context) -> int:
    """Receive category icon and create it."""
    icon_text = update.message.text.strip()
    if icon_text == "/skip":
        icon = "tv"
    else:
        icon = icon_text

    name = context.user_data.pop("new_cat_name")
    cat_idx = storage.add_category(name, icon)
    context.user_data["cat_idx"] = cat_idx
    await update.message.reply_text(
        f"✅ Category <b>{html.escape(name)}</b> created!\n"
        f"🎨 Icon: {html.escape(icon)}",
        reply_markup=category_menu_keyboard(cat_idx),
        parse_mode="HTML",
    )
    return CAT_MENU


# --------------- Category Menu ---------------


@admin_only
async def cat_menu_handler(update: Update, context) -> int:
    """Handle category menu interactions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "categories":
        cats = storage.get_categories()
        if not cats:
            await send_or_edit(
                update,
                "📂 <b>Categories</b>\n\nNo categories yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Category", callback_data="add_category")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
                ]),
                parse_mode="HTML",
            )
            return CAT_LIST
        await send_or_edit(
            update,
            "📂 <b>Categories</b>\n\nSelect a category:",
            reply_markup=categories_keyboard(),
            parse_mode="HTML",
        )
        return CAT_LIST

    if data.startswith("channels:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        channels = storage.get_channels(cat_idx)
        cat = storage.get_category(cat_idx)
        if not channels:
            await send_or_edit(
                update,
                f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nNo channels yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_idx}")],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_idx}")],
                ]),
                parse_mode="HTML",
            )
            return CH_LIST
        await send_or_edit(
            update,
            f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nSelect a channel:",
            reply_markup=channels_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CH_LIST

    if data.startswith("add_ch:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        await send_or_edit(
            update,
            "➕ <b>Add Channel</b>\n\nSend me the channel name:",
            parse_mode="HTML",
        )
        return ADD_CH_NAME

    if data.startswith("rename_cat:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        await send_or_edit(
            update,
            "✏️ <b>Rename Category</b>\n\nSend me the new name:",
            parse_mode="HTML",
        )
        return RENAME_CAT

    if data.startswith("edit_icon:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        await send_or_edit(
            update,
            "🎨 <b>Edit Icon</b>\n\nSend me the new icon name (e.g. sports_soccer, tv, movie):",
            parse_mode="HTML",
        )
        return EDIT_CAT_ICON

    if data.startswith("del_cat:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        cat = storage.get_category(cat_idx)
        await send_or_edit(
            update,
            f"🗑 Are you sure you want to delete <b>{html.escape(cat['name'])}</b>?\n\n"
            "This will also delete all channels in this category.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Yes, delete", callback_data=f"confirm_del_cat:{cat_idx}"),
                    InlineKeyboardButton("Cancel", callback_data=f"cat:{cat_idx}"),
                ],
            ]),
            parse_mode="HTML",
        )
        return CONFIRM_DEL_CAT

    return CAT_MENU


# --------------- Rename Category ---------------


@admin_only
async def rename_cat(update: Update, context) -> int:
    """Receive new name for category."""
    cat_idx = context.user_data.get("cat_idx")
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return RENAME_CAT
    storage.rename_category(cat_idx, new_name)
    await update.message.reply_text(
        f"✅ Category renamed to <b>{html.escape(new_name)}</b>",
        reply_markup=category_menu_keyboard(cat_idx),
        parse_mode="HTML",
    )
    return CAT_MENU


# --------------- Edit Category Icon ---------------


@admin_only
async def edit_cat_icon(update: Update, context) -> int:
    """Receive new icon for category."""
    cat_idx = context.user_data.get("cat_idx")
    new_icon = update.message.text.strip()
    if not new_icon:
        await update.message.reply_text("Icon cannot be empty. Try again:")
        return EDIT_CAT_ICON
    storage.update_category_icon(cat_idx, new_icon)
    await update.message.reply_text(
        f"✅ Icon updated to <b>{html.escape(new_icon)}</b>",
        reply_markup=category_menu_keyboard(cat_idx),
        parse_mode="HTML",
    )
    return CAT_MENU


# --------------- Delete Category ---------------


@admin_only
async def confirm_del_cat(update: Update, context) -> int:
    """Handle category deletion confirmation."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_cat:"):
        cat_idx = int(data.split(":")[1])
        storage.delete_category(cat_idx)
        await send_or_edit(
            update,
            "✅ Category deleted.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    if data.startswith("cat:"):
        cat_idx = int(data.split(":")[1])
        cat = storage.get_category(cat_idx)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_idx"] = cat_idx
        channels = storage.get_channels(cat_idx)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CAT_MENU

    return MAIN_MENU


# --------------- Channel List ---------------


@admin_only
async def ch_list_handler(update: Update, context) -> int:
    """Handle channel list interactions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat:"):
        cat_idx = int(data.split(":")[1])
        cat = storage.get_category(cat_idx)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_idx"] = cat_idx
        channels = storage.get_channels(cat_idx)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CAT_MENU

    if data.startswith("add_ch:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        await send_or_edit(
            update,
            "➕ <b>Add Channel</b>\n\nSend me the channel name:",
            parse_mode="HTML",
        )
        return ADD_CH_NAME

    if data.startswith("ch:"):
        parts = data.split(":")
        cat_idx = int(parts[1])
        ch_id = int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_idx, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        await send_or_edit(
            update,
            _channel_info_text(ch),
            reply_markup=channel_menu_keyboard(cat_idx, ch_id),
            parse_mode="HTML",
        )
        return CH_MENU

    return CH_LIST


# --------------- Add Channel (multi-step) ---------------


@admin_only
async def add_ch_name(update: Update, context) -> int:
    """Step 1: receive channel name."""
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return ADD_CH_NAME
    context.user_data["new_ch_name"] = name
    await update.message.reply_text(
        f"Channel: <b>{html.escape(name)}</b>\n\n"
        "Now send me the channel number (e.g. 01, 02):",
        parse_mode="HTML",
    )
    return ADD_CH_NUMBER


@admin_only
async def add_ch_number(update: Update, context) -> int:
    """Step 2: receive channel number."""
    number = update.message.text.strip()
    if not number:
        await update.message.reply_text("Number cannot be empty. Try again:")
        return ADD_CH_NUMBER
    context.user_data["new_ch_number"] = number
    await update.message.reply_text(
        "Now send me the stream link (URL):"
    )
    return ADD_CH_STREAM


@admin_only
async def add_ch_stream(update: Update, context) -> int:
    """Step 3: receive stream link."""
    stream = update.message.text.strip()
    if not stream:
        await update.message.reply_text("Stream link cannot be empty. Try again:")
        return ADD_CH_STREAM
    context.user_data["new_ch_stream"] = stream
    await update.message.reply_text(
        "Now send me the logo URL (image link):"
    )
    return ADD_CH_LOGO


@admin_only
async def add_ch_logo(update: Update, context) -> int:
    """Step 4: receive logo URL and create the channel."""
    logo = update.message.text.strip()
    if not logo:
        await update.message.reply_text("Logo URL cannot be empty. Try again:")
        return ADD_CH_LOGO

    cat_idx = context.user_data["cat_idx"]
    name = context.user_data.pop("new_ch_name")
    number = context.user_data.pop("new_ch_number")
    stream = context.user_data.pop("new_ch_stream")

    ch_id = storage.add_channel(cat_idx, name, number, logo, stream)
    if ch_id is None:
        await update.message.reply_text(
            "Failed to add channel. Category may have been deleted.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    context.user_data["ch_id"] = ch_id

    await update.message.reply_text(
        f"✅ Channel <b>{html.escape(name)}</b> added!\n\n"
        f"🔢 Number: {html.escape(number)}\n"
        f"🔗 Stream: {html.escape(stream)}\n"
        f"🖼 Logo: <code>{html.escape(logo)}</code>",
        reply_markup=channel_menu_keyboard(cat_idx, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Channel Menu ---------------


@admin_only
async def ch_menu_handler(update: Update, context) -> int:
    """Handle channel menu interactions."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("channels:"):
        cat_idx = int(data.split(":")[1])
        context.user_data["cat_idx"] = cat_idx
        cat = storage.get_category(cat_idx)
        channels = storage.get_channels(cat_idx)
        if not channels:
            await send_or_edit(
                update,
                f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nNo channels.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_idx}")],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_idx}")],
                ]),
                parse_mode="HTML",
            )
            return CH_LIST
        await send_or_edit(
            update,
            f"📺 <b>Channels in {html.escape(cat['name'])}</b>",
            reply_markup=channels_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CH_LIST

    if data.startswith("edit_stream:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "🔗 <b>Edit Stream Link</b>\n\nSend me the new stream link:",
            parse_mode="HTML",
        )
        return EDIT_CH_STREAM

    if data.startswith("edit_logo:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "🖼 <b>Edit Logo</b>\n\nSend me the new logo URL:",
            parse_mode="HTML",
        )
        return EDIT_CH_LOGO

    if data.startswith("edit_chname:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "✏️ <b>Edit Channel Name</b>\n\nSend me the new name:",
            parse_mode="HTML",
        )
        return EDIT_CH_NAME

    if data.startswith("edit_chnum:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "🔢 <b>Edit Channel Number</b>\n\nSend me the new number:",
            parse_mode="HTML",
        )
        return EDIT_CH_NUMBER

    if data.startswith("raw_logo:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        ch = storage.get_channel(cat_idx, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        logo_url = ch.get("logo", "")
        if logo_url:
            await query.message.reply_text(
                f"🖼 <b>Raw Logo URL:</b>\n\n<code>{html.escape(logo_url)}</code>",
                parse_mode="HTML",
            )
        else:
            await query.message.reply_text("No logo set for this channel.")
        return CH_MENU

    if data.startswith("del_ch:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_idx, ch_id)
        await send_or_edit(
            update,
            f"🗑 Delete channel <b>{html.escape(ch['name'])}</b>?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Yes, delete", callback_data=f"confirm_del_ch:{cat_idx}:{ch_id}"),
                    InlineKeyboardButton("Cancel", callback_data=f"ch:{cat_idx}:{ch_id}"),
                ],
            ]),
            parse_mode="HTML",
        )
        return CONFIRM_DEL_CH

    # Handle navigating back to a specific channel
    if data.startswith("ch:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        context.user_data["cat_idx"] = cat_idx
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_idx, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        await send_or_edit(
            update,
            _channel_info_text(ch),
            reply_markup=channel_menu_keyboard(cat_idx, ch_id),
            parse_mode="HTML",
        )
        return CH_MENU

    # Handle navigating back to category
    if data.startswith("cat:"):
        cat_idx = int(data.split(":")[1])
        cat = storage.get_category(cat_idx)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_idx"] = cat_idx
        channels = storage.get_channels(cat_idx)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CAT_MENU

    return CH_MENU


# --------------- Edit Stream Link ---------------


@admin_only
async def edit_ch_stream(update: Update, context) -> int:
    """Receive new stream link."""
    cat_idx = context.user_data.get("cat_idx")
    ch_id = context.user_data.get("ch_id")
    new_link = update.message.text.strip()
    if not new_link:
        await update.message.reply_text("Link cannot be empty. Try again:")
        return EDIT_CH_STREAM
    storage.update_channel_stream(cat_idx, ch_id, new_link)
    await update.message.reply_text(
        f"✅ Stream link updated!\n\n🔗 {html.escape(new_link)}",
        reply_markup=channel_menu_keyboard(cat_idx, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Edit Logo ---------------


@admin_only
async def edit_ch_logo(update: Update, context) -> int:
    """Receive new logo URL."""
    cat_idx = context.user_data.get("cat_idx")
    ch_id = context.user_data.get("ch_id")
    new_logo = update.message.text.strip()
    if not new_logo:
        await update.message.reply_text("Logo URL cannot be empty. Try again:")
        return EDIT_CH_LOGO
    storage.update_channel_logo(cat_idx, ch_id, new_logo)
    await update.message.reply_text(
        f"✅ Logo updated!\n\n🖼 <code>{html.escape(new_logo)}</code>",
        reply_markup=channel_menu_keyboard(cat_idx, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Edit Channel Name ---------------


@admin_only
async def edit_ch_name(update: Update, context) -> int:
    """Receive new channel name."""
    cat_idx = context.user_data.get("cat_idx")
    ch_id = context.user_data.get("ch_id")
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return EDIT_CH_NAME
    storage.update_channel_name(cat_idx, ch_id, new_name)
    await update.message.reply_text(
        f"✅ Channel renamed to <b>{html.escape(new_name)}</b>",
        reply_markup=channel_menu_keyboard(cat_idx, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Edit Channel Number ---------------


@admin_only
async def edit_ch_number(update: Update, context) -> int:
    """Receive new channel number."""
    cat_idx = context.user_data.get("cat_idx")
    ch_id = context.user_data.get("ch_id")
    new_number = update.message.text.strip()
    if not new_number:
        await update.message.reply_text("Number cannot be empty. Try again:")
        return EDIT_CH_NUMBER
    storage.update_channel_number(cat_idx, ch_id, new_number)
    await update.message.reply_text(
        f"✅ Channel number updated to <b>{html.escape(new_number)}</b>",
        reply_markup=channel_menu_keyboard(cat_idx, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Delete Channel ---------------


@admin_only
async def confirm_del_ch(update: Update, context) -> int:
    """Handle channel deletion confirmation."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_del_ch:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        storage.delete_channel(cat_idx, ch_id)
        await send_or_edit(
            update,
            "✅ Channel deleted.",
        )
        cat = storage.get_category(cat_idx)
        if cat is None:
            await query.message.reply_text(
                "Category no longer exists.",
                reply_markup=main_menu_keyboard(),
            )
            return MAIN_MENU
        await query.message.reply_text(
            f"📁 <b>{html.escape(cat['name'])}</b>",
            reply_markup=category_menu_keyboard(cat_idx),
            parse_mode="HTML",
        )
        return CAT_MENU

    if data.startswith("ch:"):
        parts = data.split(":")
        cat_idx, ch_id = int(parts[1]), int(parts[2])
        ch = storage.get_channel(cat_idx, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        await send_or_edit(
            update,
            _channel_info_text(ch),
            reply_markup=channel_menu_keyboard(cat_idx, ch_id),
            parse_mode="HTML",
        )
        return CH_MENU

    return MAIN_MENU


# --------------- Cancel ---------------


async def cancel(update: Update, context) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Cancelled. Use /start to begin again.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


# --------------- Main ---------------


def main() -> None:
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler),
            ],
            CAT_LIST: [
                CallbackQueryHandler(cat_list_handler),
            ],
            CAT_MENU: [
                CallbackQueryHandler(cat_menu_handler),
            ],
            ADD_CAT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_cat_name),
            ],
            ADD_CAT_ICON: [
                MessageHandler(filters.TEXT, add_cat_icon),
            ],
            RENAME_CAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, rename_cat),
            ],
            EDIT_CAT_ICON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_cat_icon),
            ],
            CH_LIST: [
                CallbackQueryHandler(ch_list_handler),
            ],
            CH_MENU: [
                CallbackQueryHandler(ch_menu_handler),
            ],
            ADD_CH_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ch_name),
            ],
            ADD_CH_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ch_number),
            ],
            ADD_CH_STREAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ch_stream),
            ],
            ADD_CH_LOGO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ch_logo),
            ],
            EDIT_CH_STREAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_stream),
            ],
            EDIT_CH_LOGO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_logo),
            ],
            EDIT_CH_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_name),
            ],
            EDIT_CH_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_number),
            ],
            CONFIRM_DEL_CAT: [
                CallbackQueryHandler(confirm_del_cat),
            ],
            CONFIRM_DEL_CH: [
                CallbackQueryHandler(confirm_del_ch),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        per_message=False,
    )

    app.add_handler(conv)

    logger.info("Bot started polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
