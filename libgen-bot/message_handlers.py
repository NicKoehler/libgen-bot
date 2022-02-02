import book_cache
from time import time
from io import BytesIO
from db import Database
from requests import get
from telethon import Button
from urllib.parse import unquote
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
    try:
        books = book_cache.retrive_cache_data(format, query)
    except Exception:
        await event.reply(
            loc.get_string("search_error", db.users[event.sender_id]["lang"])
        )
        return

    if not books:
        await event.reply(
            loc.get_string(
                "no_results",
                db.users[event.sender_id]["lang"],
            )
        )
        return

    book = books[num]["book"]
    if not books[num]["download_url"] or not books[num]["cover_url"]:
        book_links = book.get_download_links()
        books[num]["download_url"] = book_links.get("Cloudflare")
        books[num]["cover_url"] = book_links.get("cover")

    message = loc.get_string(
        "book_message",
        db.users[event.sender_id]["lang"],
        book.title,
        book.author,
        book.publisher or loc.get_string("unknown", db.users[event.sender_id]["lang"]),
        book.language,
        book.year,
        book.size,
        book.extension,
        format,
        query,
        num,
        len(books),
    )

    cancel_str = loc.get_string("cancel", db.users[event.sender_id]["lang"])
    download_str = loc.get_string("download", db.users[event.sender_id]["lang"])

    buttons = [[], [Button.inline(cancel_str, data="cancel")]]

    if num > 1:
        buttons[0].append(Button.inline("◀️", data=f"page-{num-1}"))

    buttons[0].append(Button.inline(download_str, data=f"download-{num}"))

    if num < len(books):
        buttons[0].append(Button.inline("▶️", data=f"page-{num+1}"))

    if first:
        await event.client.send_file(
            event.chat_id,
            file=books[num]["cover_url"] + "?_=.jpg",
            caption=message,
            buttons=buttons,
        )
    else:
        await event.client.edit_message(
            event.chat_id,
            event.message_id,
            message,
            file=books[num]["cover_url"] + "?_=.jpg",
            buttons=buttons,
        )


async def send_downloaded_book(
    format: str,
    query: str,
    num: int,
    event: Message,
    db: Database,
    loc: Localization,
) -> None:

    try:
        books = book_cache.retrive_cache_data(format, query)
    except Exception:
        await event.reply(
            loc.get_string("search_error", db.users[event.sender_id]["lang"])
        )
        return
    book = books[num]

    direct_link = books[num]["download_url"] or book["book"].get_download_links().get(
        "Cloudflare"
    )
    async with event.client.action(event.chat_id, "file"):

        try:
            await event.client.send_file(event.chat_id, file=direct_link)
        except Exception:
            msg = await event.client.send_message(
                event.chat_id,
                loc.get_string("too_big", db.users[event.sender_id]["lang"]),
            )

            r = get(direct_link)

            if r.status_code == 200:
                filename = unquote(
                    r.headers.get("content-disposition").split("filename*=UTF-8''")[1]
                )

                pdf_file = BytesIO(r.content)
                pdf_file.name = filename

                start_time = time()

                async def progress_bar(uploaded, total):
                    diff = start_time - time()
                    total_mb = round(total / (1024**2), 2)
                    if round(diff % 3) == 0:
                        percentage = round(uploaded * 100 / total, 2)
                        mb = round(uploaded / (1024**2), 2)
                        await msg.edit(
                            loc.get_string(
                                "uploading",
                                db.users[event.sender_id]["lang"],
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
                pdf_file.close()
                await msg.delete()

            else:
                await event.client.send_message(
                    event.chat_id,
                    loc.get_string(
                        "download_failed",
                        db.users[event.sender_id]["lang"],
                        direct_link,
                    ),
                )
