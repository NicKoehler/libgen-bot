from libgen_api import Libgen
from libgen_api.book import Book
from datetime import datetime, timedelta


book_cache = {}


def retrive_cache_data(format: str, query: str) -> dict[int, Book]:
    """
    Retrive the cached data for the query.
    """
    date_now = datetime.now()

    # save the search results in the cache if not already there or if the cache is expired
    if format not in book_cache:
        book_cache[format] = {}
    if query not in book_cache[format] or book_cache[format][query]["expires"] < date_now:
        book_cache[format][query] = {}
        book_cache[format][query]["expires"] = date_now + timedelta(hours=1)
        book_cache[format][query]["data"] = {
            k + 1: {"book": v, "download_url": None, "cover_url": None}
            for k, v in enumerate(
                Libgen.search_title(query, {"extension": format} if format != "all" else {})
            )
        }
    return book_cache[format][query].get("data")
