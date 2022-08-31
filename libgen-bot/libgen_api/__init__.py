import logging
from .book import Book
from bs4 import BeautifulSoup
from aiohttp import ClientSession

logger = logging.getLogger("Libgen-Api")

URL_BASE = "https://libgen.li"

URL_SEARCH = (
    URL_BASE + "/index.php?req={}"
    "&columns[]=t"
    "&columns[]=a"
    "&columns[]=s"
    "&columns[]=y"
    "&columns[]=p"
    "&columns[]=i"
    "&objects[]=f"
    "&objects[]=e"
    "&objects[]=s"
    "&objects[]=a"
    "&objects[]=p"
    "&objects[]=w"
    "&topics[]=l"
    "&topics[]=c"
    "&topics[]=f"
    "&topics[]=m"
    "&topics[]=s"
    "&res={}"
    "&covers=on"
    "&gmode=on"
    "&filesuns=all"
)


async def search_books(query: str, ext: str = None, limit=100) -> list[Book]:
    """
    Searchs for books in on libgen.li.

    returns a list of books or an empty list.

    limit can be 25, 50 or 100. It fallback to 25 otherwise.

    25 will be 26
    50 will be 51
    100 will be 101

    idk why

    this search includes an advanced search mode (Google mode), allows you to set more precise search terms:
    - Quotes: "" - search exactly for the phrase as it is written in the database
    - Mask: * (min 3 chars)- search by part of a word
    - Excluding words: - (minus) - does not display records containing this word, also, these conditions can be combined.
    """

    if ext is not None:
        query = f"{query} ext:{ext}"

    async with ClientSession() as session:
        async with session.get(URL_SEARCH.format(query, limit)) as resp:
            assert resp.status == 200
            html = await resp.text()

    soup = BeautifulSoup(html, features="lxml")
    books: list[Book] = []

    # tbody is the body of the table
    body = soup.find("tbody")

    if not body:
        logger.info("No book found")
        return books

    # every line is a tr tag
    raw_books = body.find_all("tr")

    for book in raw_books:
        book_attributes = book.find_all("td")

        # for now only the books with all column attributes
        # will be scraped, need fixes
        if len(book_attributes) != 10:
            logger.warning("Incomplete data, skipping")
            continue
        (
            cover,
            title,
            author,
            publisher,
            year,
            language,
            pages,
            size,
            ext,
            mirrors,
        ) = book_attributes

        cover_url = cover.find("img").attrs["src"]

        if cover_url:
            if not cover_url.startswith("http"):
                cover_url = URL_BASE + cover_url
            cover_url = cover_url.replace("_small", "")
        else:
            cover_url = "https://libgen.rocks/img/blank.png"

        t = title.find("b")
        if t:
            title = t.text
        else:
            title = title.find("a").text

        title = " ".join(title.split())

        # title = " ".join(title.text.split("\n")[0].split())
        author = author.text
        publisher = publisher.text
        year = year.text
        language = language.text
        pages = pages.text
        size = size.text
        ext = ext.text
        mirrors = [link["href"] for link in mirrors.find_all("a")]

        books.append(
            Book(
                title,
                author,
                publisher,
                year,
                language,
                pages,
                size,
                ext,
                mirrors,
                cover_url,
            )
        )

    logger.info("Found %d books", len(books))

    return books
