"""
Telegram Channel Manager Bot

Manage channel categories with stream links and pictures.
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
    RENAME_CAT,
    CH_LIST,
    CH_MENU,
    ADD_CH_NAME,
    ADD_CH_STREAM,
    ADD_CH_PICTURE,
    EDIT_CH_STREAM,
    EDIT_CH_PICTURE,
    EDIT_CH_NAME,
    CONFIRM_DEL_CAT,
    CONFIRM_DEL_CH,
) = range(15)


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


def categories_keyboard(back: bool = True) -> InlineKeyboardMarkup:
    """Build a keyboard listing all categories."""
    cats = storage.get_categories()
    buttons = []
    for cat_id, cat in cats.items():
        buttons.append([
            InlineKeyboardButton(
                f"📁 {cat['name']}",
                callback_data=f"cat:{cat_id}",
            )
        ])
    if back:
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def category_menu_keyboard(cat_id: str) -> InlineKeyboardMarkup:
    """Build the menu for a single category."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Channels", callback_data=f"channels:{cat_id}")],
        [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_id}")],
        [InlineKeyboardButton("✏️ Rename Category", callback_data=f"rename_cat:{cat_id}")],
        [InlineKeyboardButton("🗑 Delete Category", callback_data=f"del_cat:{cat_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="categories")],
    ])


def channels_keyboard(cat_id: str) -> InlineKeyboardMarkup:
    """Build a keyboard listing all channels in a category."""
    channels = storage.get_channels(cat_id)
    buttons = []
    for ch_id, ch in channels.items():
        buttons.append([
            InlineKeyboardButton(
                f"📺 {ch['name']}",
                callback_data=f"ch:{cat_id}:{ch_id}",
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_id}")])
    return InlineKeyboardMarkup(buttons)


def channel_menu_keyboard(cat_id: str, ch_id: str) -> InlineKeyboardMarkup:
    """Build the menu for a single channel."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Edit Stream Link", callback_data=f"edit_stream:{cat_id}:{ch_id}")],
        [InlineKeyboardButton("🖼 Edit Picture", callback_data=f"edit_pic:{cat_id}:{ch_id}")],
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_chname:{cat_id}:{ch_id}")],
        [InlineKeyboardButton("📋 Get Raw Picture URL", callback_data=f"raw_pic:{cat_id}:{ch_id}")],
        [InlineKeyboardButton("🗑 Delete Channel", callback_data=f"del_ch:{cat_id}:{ch_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"channels:{cat_id}")],
    ])


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
        "Manage your channel categories, stream links, and pictures.\n\n"
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
        cat_id = data.split(":")[1]
        cat = storage.get_category(cat_id)
        if cat is None:
            await send_or_edit(update, "Category not found.")
            return MAIN_MENU
        context.user_data["cat_id"] = cat_id
        channels = storage.get_channels(cat_id)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\n"
            f"Channels: {len(channels)}\n\n"
            "Choose an action:",
            reply_markup=category_menu_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CAT_MENU

    return CAT_LIST


# --------------- Add Category ---------------


@admin_only
async def add_cat_name(update: Update, context) -> int:
    """Receive category name and create it."""
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return ADD_CAT_NAME
    cat_id = storage.add_category(name)
    context.user_data["cat_id"] = cat_id
    await update.message.reply_text(
        f"✅ Category <b>{html.escape(name)}</b> created!",
        reply_markup=category_menu_keyboard(cat_id),
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
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        channels = storage.get_channels(cat_id)
        cat = storage.get_category(cat_id)
        if not channels:
            await send_or_edit(
                update,
                f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nNo channels yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_id}")],
                ]),
                parse_mode="HTML",
            )
            return CH_LIST
        await send_or_edit(
            update,
            f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nSelect a channel:",
            reply_markup=channels_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CH_LIST

    if data.startswith("add_ch:"):
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        await send_or_edit(
            update,
            "➕ <b>Add Channel</b>\n\nSend me the channel name:",
            parse_mode="HTML",
        )
        return ADD_CH_NAME

    if data.startswith("rename_cat:"):
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        await send_or_edit(
            update,
            "✏️ <b>Rename Category</b>\n\nSend me the new name:",
            parse_mode="HTML",
        )
        return RENAME_CAT

    if data.startswith("del_cat:"):
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        cat = storage.get_category(cat_id)
        await send_or_edit(
            update,
            f"🗑 Are you sure you want to delete <b>{html.escape(cat['name'])}</b>?\n\n"
            "This will also delete all channels in this category.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Yes, delete", callback_data=f"confirm_del_cat:{cat_id}"),
                    InlineKeyboardButton("Cancel", callback_data=f"cat:{cat_id}"),
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
    cat_id = context.user_data.get("cat_id")
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return RENAME_CAT
    storage.rename_category(cat_id, new_name)
    await update.message.reply_text(
        f"✅ Category renamed to <b>{html.escape(new_name)}</b>",
        reply_markup=category_menu_keyboard(cat_id),
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
        cat_id = data.split(":")[1]
        storage.delete_category(cat_id)
        await send_or_edit(
            update,
            "✅ Category deleted.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    if data.startswith("cat:"):
        cat_id = data.split(":")[1]
        cat = storage.get_category(cat_id)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_id"] = cat_id
        channels = storage.get_channels(cat_id)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_id),
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
        cat_id = data.split(":")[1]
        cat = storage.get_category(cat_id)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_id"] = cat_id
        channels = storage.get_channels(cat_id)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CAT_MENU

    if data.startswith("add_ch:"):
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        await send_or_edit(
            update,
            "➕ <b>Add Channel</b>\n\nSend me the channel name:",
            parse_mode="HTML",
        )
        return ADD_CH_NAME

    if data.startswith("ch:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_id, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        text = (
            f"📺 <b>{html.escape(ch['name'])}</b>\n\n"
            f"🔗 Stream: {html.escape(ch['stream_link'])}\n"
            f"🖼 Picture: {'Yes' if ch.get('picture_file_id') else 'No'}"
        )
        await send_or_edit(
            update, text,
            reply_markup=channel_menu_keyboard(cat_id, ch_id),
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
        "Now send me the stream link (URL):",
        parse_mode="HTML",
    )
    return ADD_CH_STREAM


@admin_only
async def add_ch_stream(update: Update, context) -> int:
    """Step 2: receive stream link."""
    stream_link = update.message.text.strip()
    if not stream_link:
        await update.message.reply_text("Stream link cannot be empty. Try again:")
        return ADD_CH_STREAM
    context.user_data["new_ch_stream"] = stream_link
    await update.message.reply_text(
        "Now send me the channel picture (as a photo):"
    )
    return ADD_CH_PICTURE


@admin_only
async def add_ch_picture(update: Update, context) -> int:
    """Step 3: receive picture and create the channel."""
    if not update.message.photo:
        await update.message.reply_text("Please send a photo image. Try again:")
        return ADD_CH_PICTURE

    photo = update.message.photo[-1]  # highest resolution
    file = await photo.get_file()
    file_id = photo.file_id
    file_url = file.file_path  # Telegram file URL

    cat_id = context.user_data["cat_id"]
    name = context.user_data.pop("new_ch_name")
    stream_link = context.user_data.pop("new_ch_stream")

    ch_id = storage.add_channel(cat_id, name, stream_link, file_id, file_url)
    if ch_id is None:
        await update.message.reply_text(
            "Failed to add channel. Category may have been deleted.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    context.user_data["ch_id"] = ch_id

    await update.message.reply_text(
        f"✅ Channel <b>{html.escape(name)}</b> added!\n\n"
        f"🔗 Stream: {html.escape(stream_link)}\n"
        f"🖼 Raw picture URL:\n<code>{html.escape(file_url)}</code>",
        reply_markup=channel_menu_keyboard(cat_id, ch_id),
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
        cat_id = data.split(":")[1]
        context.user_data["cat_id"] = cat_id
        cat = storage.get_category(cat_id)
        channels = storage.get_channels(cat_id)
        if not channels:
            await send_or_edit(
                update,
                f"📺 <b>Channels in {html.escape(cat['name'])}</b>\n\nNo channels.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Channel", callback_data=f"add_ch:{cat_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"cat:{cat_id}")],
                ]),
                parse_mode="HTML",
            )
            return CH_LIST
        await send_or_edit(
            update,
            f"📺 <b>Channels in {html.escape(cat['name'])}</b>",
            reply_markup=channels_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CH_LIST

    if data.startswith("edit_stream:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "🔗 <b>Edit Stream Link</b>\n\nSend me the new stream link:",
            parse_mode="HTML",
        )
        return EDIT_CH_STREAM

    if data.startswith("edit_pic:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "🖼 <b>Edit Picture</b>\n\nSend me the new picture (as a photo):",
            parse_mode="HTML",
        )
        return EDIT_CH_PICTURE

    if data.startswith("edit_chname:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        await send_or_edit(
            update,
            "✏️ <b>Edit Channel Name</b>\n\nSend me the new name:",
            parse_mode="HTML",
        )
        return EDIT_CH_NAME

    if data.startswith("raw_pic:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        ch = storage.get_channel(cat_id, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        pic_url = ch.get("picture_url", "")
        if pic_url:
            await query.message.reply_text(
                f"🖼 <b>Raw Picture URL:</b>\n\n<code>{html.escape(pic_url)}</code>",
                parse_mode="HTML",
            )
        else:
            await query.message.reply_text("No picture set for this channel.")
        return CH_MENU

    if data.startswith("del_ch:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_id, ch_id)
        await send_or_edit(
            update,
            f"🗑 Delete channel <b>{html.escape(ch['name'])}</b>?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Yes, delete", callback_data=f"confirm_del_ch:{cat_id}:{ch_id}"),
                    InlineKeyboardButton("Cancel", callback_data=f"ch:{cat_id}:{ch_id}"),
                ],
            ]),
            parse_mode="HTML",
        )
        return CONFIRM_DEL_CH

    # Handle navigating back to a specific channel
    if data.startswith("ch:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        context.user_data["cat_id"] = cat_id
        context.user_data["ch_id"] = ch_id
        ch = storage.get_channel(cat_id, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        text = (
            f"📺 <b>{html.escape(ch['name'])}</b>\n\n"
            f"🔗 Stream: {html.escape(ch['stream_link'])}\n"
            f"🖼 Picture: {'Yes' if ch.get('picture_file_id') else 'No'}"
        )
        await send_or_edit(
            update, text,
            reply_markup=channel_menu_keyboard(cat_id, ch_id),
            parse_mode="HTML",
        )
        return CH_MENU

    # Handle navigating back to category
    if data.startswith("cat:"):
        cat_id = data.split(":")[1]
        cat = storage.get_category(cat_id)
        if cat is None:
            await send_or_edit(update, "Category not found.", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        context.user_data["cat_id"] = cat_id
        channels = storage.get_channels(cat_id)
        await send_or_edit(
            update,
            f"📁 <b>{html.escape(cat['name'])}</b>\n\nChannels: {len(channels)}",
            reply_markup=category_menu_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CAT_MENU

    return CH_MENU


# --------------- Edit Stream Link ---------------


@admin_only
async def edit_ch_stream(update: Update, context) -> int:
    """Receive new stream link."""
    cat_id = context.user_data.get("cat_id")
    ch_id = context.user_data.get("ch_id")
    new_link = update.message.text.strip()
    if not new_link:
        await update.message.reply_text("Link cannot be empty. Try again:")
        return EDIT_CH_STREAM
    storage.update_channel_stream(cat_id, ch_id, new_link)
    ch = storage.get_channel(cat_id, ch_id)
    await update.message.reply_text(
        f"✅ Stream link updated!\n\n🔗 {html.escape(new_link)}",
        reply_markup=channel_menu_keyboard(cat_id, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Edit Picture ---------------


@admin_only
async def edit_ch_picture(update: Update, context) -> int:
    """Receive new picture."""
    if not update.message.photo:
        await update.message.reply_text("Please send a photo. Try again:")
        return EDIT_CH_PICTURE

    cat_id = context.user_data.get("cat_id")
    ch_id = context.user_data.get("ch_id")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_id = photo.file_id
    file_url = file.file_path

    storage.update_channel_picture(cat_id, ch_id, file_id, file_url)
    await update.message.reply_text(
        f"✅ Picture updated!\n\n"
        f"🖼 Raw picture URL:\n<code>{html.escape(file_url)}</code>",
        reply_markup=channel_menu_keyboard(cat_id, ch_id),
        parse_mode="HTML",
    )
    return CH_MENU


# --------------- Edit Channel Name ---------------


@admin_only
async def edit_ch_name(update: Update, context) -> int:
    """Receive new channel name."""
    cat_id = context.user_data.get("cat_id")
    ch_id = context.user_data.get("ch_id")
    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("Name cannot be empty. Try again:")
        return EDIT_CH_NAME
    storage.update_channel_name(cat_id, ch_id, new_name)
    await update.message.reply_text(
        f"✅ Channel renamed to <b>{html.escape(new_name)}</b>",
        reply_markup=channel_menu_keyboard(cat_id, ch_id),
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
        cat_id, ch_id = parts[1], parts[2]
        storage.delete_channel(cat_id, ch_id)
        await send_or_edit(
            update,
            "✅ Channel deleted.",
        )
        cat = storage.get_category(cat_id)
        if cat is None:
            await query.message.reply_text(
                "Category no longer exists.",
                reply_markup=main_menu_keyboard(),
            )
            return MAIN_MENU
        await query.message.reply_text(
            f"📁 <b>{html.escape(cat['name'])}</b>",
            reply_markup=category_menu_keyboard(cat_id),
            parse_mode="HTML",
        )
        return CAT_MENU

    if data.startswith("ch:"):
        parts = data.split(":")
        cat_id, ch_id = parts[1], parts[2]
        ch = storage.get_channel(cat_id, ch_id)
        if ch is None:
            await send_or_edit(update, "Channel not found.")
            return CH_LIST
        text = (
            f"📺 <b>{html.escape(ch['name'])}</b>\n\n"
            f"🔗 Stream: {html.escape(ch['stream_link'])}\n"
            f"🖼 Picture: {'Yes' if ch.get('picture_file_id') else 'No'}"
        )
        await send_or_edit(
            update, text,
            reply_markup=channel_menu_keyboard(cat_id, ch_id),
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
            RENAME_CAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, rename_cat),
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
            ADD_CH_STREAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_ch_stream),
            ],
            ADD_CH_PICTURE: [
                MessageHandler(filters.PHOTO, add_ch_picture),
            ],
            EDIT_CH_STREAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_stream),
            ],
            EDIT_CH_PICTURE: [
                MessageHandler(filters.PHOTO, edit_ch_picture),
            ],
            EDIT_CH_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_ch_name),
            ],
            CONFIRM_DEL_CAT: [
                CallbackQueryHandler(confirm_del_cat),
            ],
            CONFIRM_DEL_CH: [
                CallbackQueryHandler(confirm_del_ch),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv)

    logger.info("Bot started polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
