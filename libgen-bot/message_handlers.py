import book_cache
from time import time
from io import BytesIO
from db import Database
from telethon import Button
from aiohttp import ClientSession
from telethon.tl.types import Message
from localization import Localization


async def send_page_message(
    format: str,
    query: str,
    num: int,
    event: Message,
    db: Database,
    loc: Localization,
    first: bool = False,
) -> None:
    user_lang = db.users[event.sender_id]["lang"]

    try:
        books = await book_cache.retrive_cache_data(format, query)
    except Exception as e:
        await event.reply(
            f"{loc.get_string('search_error', db.users[event.sender_id]['lang'])}\n\n<code>{e}</code>"
        )
        return

    if not books:
        await event.reply(
            loc.get_string(
                "no_results",
                user_lang,
            )
        )
        return

    book = books[num - 1]
    loc_unknown = loc.get_string("unknown", user_lang)
    message = loc.get_string(
        "book_message",
        user_lang,
        book.title,
        book.author or loc_unknown,
        book.publisher or loc_unknown,
        book.language,
        book.year,
        book.size,
        book.ext,
        format,
        query,
        num,
        len(books),
    )

    cancel_str = loc.get_string("cancel", user_lang)
    download_str = loc.get_string("download", user_lang)

    buttons = [[], [Button.inline(cancel_str, data="cancel")]]

    if num > 1:
        buttons[0].append(Button.inline("◀️", data=f"page-{num-1}"))

    buttons[0].append(Button.inline(download_str, data=f"download-{num}"))

    if num < len(books):
        buttons[0].append(Button.inline("▶️", data=f"page-{num+1}"))

    cover_url = books[num - 1].cover_url

    async with ClientSession() as session:
        async with session.get(cover_url) as resp:
            assert resp.status == 200
            photo = BytesIO(await resp.read())

    try:
        if first:
            await event.client.send_file(
                event.chat_id,
                file=photo,
                caption=message,
                buttons=buttons,
            )
        else:
            await event.client.edit_message(
                event.chat_id,
                event.message_id,
                message,
                file=photo,
                buttons=buttons,
            )
    except Exception as e:
        await event.reply(
            f"{loc.get_string('search_error', user_lang)}\n\n<code>{e}</code>"
        )
        return


async def send_downloaded_book(
    format: str,
    query: str,
    num: int,
    event: Message,
    db: Database,
    loc: Localization,
) -> None:

    user_lang = db.users[event.sender_id]["lang"]

    try:
        books = await book_cache.retrive_cache_data(format, query)
    except Exception as e:
        await event.reply(
            f"{loc.get_string('search_error', user_lang)}\n\n<code>{e}</code>"
        )
        return
    book = books[num - 1]

    msg = await event.reply(loc.get_string("wait_download", user_lang, book.title))

    try:
        data, filename = await book.download()

        await msg.edit(loc.get_string("sending_download", user_lang, book.title))

        async with event.client.action(event.chat_id, "file"):

            pdf_file = BytesIO(data)
            pdf_file.name = filename

            t1 = time()

            async def progress_bar(uploaded, total):
                nonlocal t1
                t2 = time()
                diff = t2 - t1

                if diff >= 2:
                    t1 = t2
                    total_mb = round(total / (1024**2), 2)
                    percentage = round(uploaded * 100 / total, 2)
                    mb = round(uploaded / (1024**2), 2)
                    await msg.edit(
                        loc.get_string(
                            "uploading",
                            user_lang,
                            percentage,
                            mb,
                            total_mb,
                        )
                    )

            await event.client.send_file(
                event.chat_id,
                file=pdf_file,
                progress_callback=progress_bar,
            )
            await msg.delete()

    except Exception as e:
        await msg.edit(
            loc.get_string(
                "download_failed",
                user_lang,
                "\n".join(book.mirrors),
            ),
        )
