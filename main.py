import json

import urllib3

from utils import get_tweets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import html
import logging
import traceback
from typing import Optional, Tuple

from telegram import Chat, ChatMember, ChatMemberUpdated, ParseMode, Update, user
from telegram.ext import CallbackContext, ChatMemberHandler, CommandHandler, Updater

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

"""Run bot."""
# Create the Updater and pass it your bot's token.
secrets = json.load(open("secrets.json"))
secrets = secrets["secrets"]
bot_token = secrets["BOT_API_TOKEN"]
updater = Updater(bot_token)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher


def post_tweets(context: CallbackContext) -> None:
    """check for new tweet"""
    job = context.job
    secrets = json.load(open("secrets.json", "r"))
    tweets = get_tweets(
        last_tweet_id=secrets["secrets"]["LAST_TWEET_ID"],
        bearer_token=secrets["secrets"]["BEARER_TOKEN"],
        for_user=secrets["secrets"]["TWITTER_ID"],
    )
    if "data" in tweets.keys():
        secrets["secrets"]["LAST_TWEET_ID"] = tweets["meta"]["newest_id"]
        json.dump(secrets, open("secrets.json", "w"), indent=4)
        for tweet in tweets["data"]:
            context.bot.send_message(job.context, text=tweet["text"])


# after every 30 seconds
dispatcher.job_queue.run_repeating(
    post_tweets, 30, context=secrets["CHAT_ID"], name=secrets["CHAT_ID"]
)


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get(
        "is_member", (None, None)
    )

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.CREATOR,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.CREATOR,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


def track_chats(update: Update, context: CallbackContext) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info(
                "%s removed the bot from the channel %s", cause_name, chat.title
            )
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


def show_chats(update: Update, context: CallbackContext) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(
        str(uid) for uid in context.bot_data.setdefault("user_ids", set())
    )
    group_ids = ", ".join(
        str(gid) for gid in context.bot_data.setdefault("group_ids", set())
    )
    channel_ids = ", ".join(
        str(cid) for cid in context.bot_data.setdefault("channel_ids", set())
    )
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    update.effective_message.reply_text(text)


def greet_chat_members(update: Update, _: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        update.effective_chat.send_message(
            f"{member_name} was added by {cause_name}. Welcome!\nPlease tell us a little about you.",
            parse_mode=ParseMode.HTML,
        )


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    context.bot.send_message(
        chat_id=secrets["DEV_USER"], text=message, parse_mode=ParseMode.HTML
    )


# on different commands - answer in Telegram
dispatcher.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
dispatcher.add_handler(
    CommandHandler(
        "show_chats",
        show_chats,
    )
)
dispatcher.add_handler(
    ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER)
)
dispatcher.add_error_handler(error_handler)
# Start the Bot
updater.start_polling(
    allowed_updates=[Update.MESSAGE, Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER]
)

# Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
# SIGABRT. This should be used most of the time, since start_polling() is
# non-blocking and will stop the bot gracefully.
updater.idle()
