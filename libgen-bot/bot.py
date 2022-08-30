import dotenv
import logging
import query_utils
from os import environ
from db import Database
import message_handlers
from localization import Localization
from telethon import TelegramClient, Button, functions, events, types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("Libgen-Bot")

# load all the env variables from .env file
dotenv.load_dotenv()

API_ID = environ.get("API_ID")
API_HASH = environ.get("API_HASH")
BOT_TOKEN = environ.get("BOT_TOKEN")
OWNER = int(environ.get("OWNER_ID"))
DB_URL = environ.get("DATABASE_URL")

assert all((API_ID, API_HASH, BOT_TOKEN, OWNER)), "Please set all the env variables"

bot = TelegramClient(
    "libgen-bot",
    api_id=API_ID,
    api_hash=API_HASH,
).start(bot_token=BOT_TOKEN)


bot.parse_mode = "html"

db = Database(DB_URL, logger)
loc = Localization()
user_state = {}


def get_language_buttons(lang):
    return [
        [
            Button.inline(
                "🇺🇸 • English ✅" if lang == "en" else "🇺🇸 • English", data="lang-en"
            ),
            Button.inline(
                "🇮🇹 • Italiano ✅" if lang == "it" else "🇮🇹 • Italiano", data="lang-it"
            ),
        ],
        [Button.inline(loc.get_string("cancel", lang), data="cancel")],
    ]


def authorized_users(func):
    async def wrapper(event):
        if db.users.get(event.sender_id):
            await func(event)

    return wrapper


def owner_only(func):
    async def wrapper(event):
        user = db.users.get(event.sender_id)
        if user and user.get("owner"):
            await func(event)

    return wrapper


@bot.on(events.NewMessage(pattern="/start"))
@authorized_users
async def start(event):

    logger.info(f"{event.sender.first_name} - /start")

    async with bot.action(event.chat_id, "typing"):
        await event.reply(
            loc.get_string(
                "welcome", db.users[event.sender_id]["lang"], event.sender.first_name
            )
        )


@bot.on(events.NewMessage(pattern=r"^/(all|pdf|epub|mobi|azw3|djvu|doc)$|^([^\s/].+)$"))
@authorized_users
async def search(event):

    format = event.pattern_match.group(1)
    query = event.pattern_match.group(2)

    if format:
        user_state[event.sender_id] = format
        await event.reply(
            loc.get_string("search", db.users[event.sender_id]["lang"], format)
        )
    else:
        query = " ".join(query.split()).casefold()
        format = "all"
        if event.sender_id in user_state:
            format = user_state[event.sender_id]
            user_state[event.sender_id] = "all"

        logger.info(f"{event.sender.first_name} - /{format} {query}")

        async with bot.action(event.chat_id, "typing"):
            if len(query) < 3:
                await event.reply(
                    loc.get_string(
                        "too_short",
                        db.users[event.sender_id]["lang"],
                    )
                )

            elif len(query) > 100:
                await event.reply(
                    loc.get_string(
                        "too_long",
                        db.users[event.sender_id]["lang"],
                    )
                )

            else:
                await message_handlers.send_page_message(
                    format, query, 1, event, db, loc, first=True
                )


@bot.on(events.NewMessage(pattern=r"/language"))
@authorized_users
async def settings(event):

    logger.info(f"{event.sender.first_name} - /language")

    lang = db.users[event.sender_id]["lang"]
    await event.reply(
        loc.get_string(
            "language",
            lang,
        ),
        buttons=get_language_buttons(lang),
    )


@bot.on(events.NewMessage(pattern=r"/users"))
@owner_only
async def users(event):

    logger.info(f"{event.sender.first_name} - /users")

    users_list = [(await bot.get_entity(user)) for user in db.users]

    owner = None
    users = []

    for user in users_list:
        if user.id == OWNER:
            owner = f"• {user.first_name} - <code>{user.id}</code>"
        else:
            users.append(f"• {user.first_name} - <code>{user.id}</code>")

    await event.reply(
        loc.get_string(
            "users_list", db.users[event.sender_id]["lang"], owner, "\n".join(users)
        )
    )


@bot.on(events.NewMessage(pattern=r"/add_user (@.+)"))
@owner_only
async def add_user(event):

    username = event.pattern_match.group(1)
    user = await bot.get_entity(username)

    logger.info(f"{event.sender.first_name} - /add_user {user.id}")

    if user.id not in db.users:
        db.add_user(user.id, user.lang_code)
        await event.reply(
            loc.get_string(
                "add_user",
                db.users[event.sender_id]["lang"],
                user.first_name,
            )
        )

    else:
        await event.reply(
            loc.get_string(
                "user_exists",
                db.users[event.sender_id]["lang"],
                user.first_name,
            )
        )


@bot.on(events.NewMessage(pattern=r"/remove_user (@.+)"))
@owner_only
async def remove_user(event):

    username = event.pattern_match.group(1)
    user = await bot.get_entity(username)

    logger.info(f"{event.sender.first_name} - /remove_user {user.id}")

    if user.id == OWNER:
        await event.reply(
            loc.get_string(
                "remove_owner",
                db.users[event.sender_id]["lang"],
            )
        )

    elif user.id in db.users:
        db.remove_user(user.id)
        await event.reply(
            loc.get_string(
                "remove_user", db.users[event.sender_id]["lang"], user.first_name
            )
        )
    else:
        await event.reply(
            loc.get_string(
                "user_not_found", db.users[event.sender_id]["lang"], user.first_name
            )
        )


@bot.on(events.CallbackQuery(pattern=r"^(page|download)-\d+"))
@authorized_users
async def download_or_change_page(event):
    command, num = event.data.decode("utf-8").split("-")
    format, query = await query_utils.get_ext_and_query_from_message(event)
    num = int(num)

    if command == "download":
        logger.info(f"{event.sender.first_name} - is downloading...")
        await message_handlers.send_downloaded_book(format, query, num, event, db, loc)
        logger.info(f"{event.sender.first_name} - finished downloading")

    elif command == "page":
        await message_handlers.send_page_message(format, query, num, event, db, loc)


@bot.on(events.CallbackQuery(pattern="cancel"))
@authorized_users
async def cancel(event):
    await event.delete()


@bot.on(events.CallbackQuery(pattern=r"^lang-(.+)"))
@authorized_users
async def change_lang(event):

    button_lang = event.pattern_match.group(1).decode("utf-8")
    user_lang = db.users[event.sender_id]["lang"]

    if button_lang != user_lang:
        db.set_language(event.sender_id, button_lang)
        user_lang = db.users[event.sender_id]["lang"]
        await event.edit(
            loc.get_string(
                "language",
                user_lang,
            ),
            buttons=get_language_buttons(user_lang),
        )
    else:
        await event.answer(
            loc.get_string(
                "language_already_selected",
                user_lang,
            ),
            alert=True,
        )


async def setup():
    if not db.users:
        user = await bot.get_entity(OWNER)
        db.add_user(user.id, user.lang_code, owner=True)
        logger.info(f"First start adding the owner {user.id} to the database")

    for lang in loc.supported_languages:
        await bot(
            functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code=lang,
                commands=[
                    types.BotCommand(
                        command="start",
                        description=loc.get_string("start_description", lang),
                    ),
                    types.BotCommand(
                        command="pdf",
                        description=loc.get_string("pdf_description", lang),
                    ),
                    types.BotCommand(
                        command="epub",
                        description=loc.get_string("epub_description", lang),
                    ),
                    types.BotCommand(
                        command="mobi",
                        description=loc.get_string("mobi_description", lang),
                    ),
                    types.BotCommand(
                        command="azw3",
                        description=loc.get_string("azw3_description", lang),
                    ),
                    types.BotCommand(
                        command="djvu",
                        description=loc.get_string("djvu_description", lang),
                    ),
                    types.BotCommand(
                        command="doc",
                        description=loc.get_string("doc_description", lang),
                    ),
                    types.BotCommand(
                        command="language",
                        description=loc.get_string("language_description", lang),
                    ),
                ],
            )
        )


if __name__ == "__main__":
    bot.loop.create_task(setup())
    logger.info("Bot started")
    bot.run_until_disconnected()
    logger.info("Bot stopped")
