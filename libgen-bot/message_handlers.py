import book_cache
from time import time
from io import BytesIO
from telethon import Button
from libgen_api.book import Book
from aiohttp import ClientSession
from localization import Localization
from telethon.tl.types import InputWebDocument
from telethon.events import CallbackQuery, InlineQuery
from query_utils import base64_encode


async def send_page_message(
    format: str,
    query: str,
    num: int,
    event: CallbackQuery.Event,
    user_lang: str,
    loc: Localization,
    first: bool = False,
) -> None:

    async with event.client.action(event.chat_id, "typing"):
        try:
            books = await book_cache.retrive_cache_data(format, query)
        except Exception as e:
            await event.reply(
                f"{loc.get_string('search_error', user_lang)}\n\n<code>{e}</code>"
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
        unknown = loc.get_string("unknown", user_lang)
        message = loc.get_string(
            "book_message",
            user_lang,
            book.title,
            book.author or unknown,
            book.publisher or unknown,
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

        photo.name = "photo.jpg"

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
    event: CallbackQuery.Event,
    user_lang: str,
    loc: Localization,
) -> None:

    try:
        books = await book_cache.retrive_cache_data(format, query)
    except Exception as e:
        await event.reply(
            f"{loc.get_string('search_error', user_lang)}\n\n<code>{e}</code>"
        )
        return
    book = books[num - 1]

    msg = await event.client.send_message(
        event.sender_id, loc.get_string("wait_download", user_lang, book.title)
    )

    try:
        data, filename = await book.download()

        await msg.edit(loc.get_string("sending_download", user_lang, book.title))

        async with event.client.action(event.chat_id, "file"):

            downloaded_book = BytesIO(data)
            downloaded_book.name = filename

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
                            book.title,
                            percentage,
                            mb,
                            total_mb,
                        )
                    )

            await event.client.send_file(
                event.chat_id,
                file=downloaded_book,
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


async def send_articles_book(
    event: InlineQuery.Event,
    query: str,
    bot_username: str,
    user_lang: str,
    loc: Localization,
):

    builder = event.builder

    books: list[Book] = await book_cache.retrive_cache_data("all", query)

    # limit it to 50 results
    books = books[:50]

    unknown = loc.get_string("unknown", user_lang)
    if not books:
        text = loc.get_string(
            "no_results",
            user_lang,
        )

        await event.answer([builder.article(title=text, text=text)])
        return

    download_str = loc.get_string("download", user_lang)

    buttons = []

    for num in range(1, len(books) + 1):
        data = base64_encode(f"{query}_{num}")
        buttons.append(
            Button.url(download_str, url=f"https://t.me/{bot_username}?start={data}")
        )

    await event.answer(
        builder.article(
            title=data[0].title,
            description=f"· {data[0].language or unknown} · {data[0].ext or unknown}\n· {data[0].author or unknown}",
            thumb=InputWebDocument(
                data[0].cover_url_small,
                0,
                "image/jpg",
                [],
            ),
            text=loc.get_string(
                "book_message",
                user_lang,
                data[0].title,
                data[0].author or unknown,
                data[0].publisher or unknown,
                data[0].language,
                data[0].year,
                data[0].size,
                data[0].ext,
                "all",
                query,
                num,
                len(books),
            ),
            buttons=data[1],
        )
        for num, data in enumerate(zip(books, buttons), 1)
    )
