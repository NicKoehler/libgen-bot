import logging
from libgen_api.book import Book
from libgen_api import search_books
from datetime import datetime, timedelta

book_cache = {}

logger = logging.getLogger("Libgen-Bot.Book-Cache")


async def retrive_cache_data(format: str, query: str) -> dict[int, Book]:
    """
    Retrive the cached data for the query.
    """
    date_now = datetime.now()

    # save the search results in the cache if not already there or if the cache is expired
    if format not in book_cache:
        book_cache[format] = {}
    if (
        query not in book_cache[format]
        or book_cache[format][query]["expires"] < date_now
    ):
        logger.info("Cache not present or expired, refetching..")
        book_cache[format][query] = {}
        book_cache[format][query]["expires"] = date_now + timedelta(hours=1)
        book_cache[format][query]["data"] = await search_books(
            query, ext=format if format != "all" else None
        )
    else:
        logger.info("Getting data from cache")

    return book_cache[format][query].get("data")
