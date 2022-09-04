import logging
from os import path
from re import A, findall
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from urllib.parse import urlparse, unquote


logger = logging.getLogger("Libgen-Api.Book")


class Book:
    """
    Book object used to store data and some methods
    """

    def __init__(
        self,
        title: str,
        author: str,
        publisher: str,
        year: str,
        language: str,
        pages: str,
        size: str,
        ext: str,
        mirrors: list[str],
        cover_url: str,
        cover_url_small: str,
    ) -> None:
        """
        Creates a book object
        """
        self.title = title
        self.author = author
        self.publisher = publisher
        self.year = year
        self.language = language
        self.pages = pages
        self.size = size
        self.ext = ext
        self.mirrors = mirrors
        self.cover_url = cover_url
        self.cover_url_small = cover_url_small

    async def download(
        self, save_to_disk=False, output="."
    ) -> tuple[bytes, str] | tuple[None, None]:
        """
        Tries to download the book using the best link.
        returns the bytes downloaded and the filename.

        optinally you can save to disk directly with save_to_disk=True

        """

        for mirror in self.mirrors:
            if "get.php" in mirror:
                data = await self.__try_download_from_get_link(
                    mirror, save_to_disk, output
                )
                if data:
                    return data
            elif "ads.php" in mirror:
                data = await self.__try_download_from_ads_link(
                    mirror, save_to_disk, output
                )
                if data:
                    return data
            elif "library.lol" in mirror:
                data = await self.__try_download_from_lol_link(
                    mirror, save_to_disk, output
                )
                if data:
                    return data

        return None, None

    async def __try_download_from_get_link(
        self, mirror, save_to_disk, output
    ) -> tuple[bytes, str] | None:
        """
        Internal method, don't use.
        Returns the bytes of the book.

        This internal methods tries to download the file directly from get.php links,
        usually this will work.
        """

        logger.info("Downloading from get.php link")
        try:
            data, filename = await self.__get_all_bytes(mirror)
        except Exception as e:
            logger.error("Error downloading the book from get.php: %s", e)
            return None

        if save_to_disk:
            self.__save_to_disk(filename, data, output)

        return data, filename

    async def __try_download_from_ads_link(
        self, mirror, save_to_disk, output
    ) -> tuple[bytes, str] | None:
        """
        Internal method, don't use.
        Returns the bytes of the book.

        This internal methods tries to download the file directly from ads.php links,
        this will make a new request to get the direct file link
        """

        logger.info("Downloading from ads.php link")

        try:
            async with ClientSession() as session:
                async with session.get(mirror) as resp:
                    assert resp.status == 200
                    url = urlparse(mirror)
                    soup = BeautifulSoup(await resp.text(), features="lxml")
                    mirror = f"{url.scheme}://{url.netloc}/{soup.find('tr').find('a')['href']}"
                    data, filename = await self.__get_all_bytes(mirror)

        except Exception as e:
            logger.error("Error downloading the book from ads.php: %s", e)
            return None

        if save_to_disk:
            self.__save_to_disk(filename, data, output)

        return data, filename

    async def __try_download_from_lol_link(
        self, mirror, save_to_disk, output
    ) -> tuple[bytes, str] | None:
        """
        Internal method, don't use.
        Returns the bytes of the book.

        This internal methods tries to download the file directly from http://library.lol links,
        this will make a new request to get the direct file link.
        "cloudflare" link will be used.
        """

        logger.info("Downloading from http://library.lol mirrors")

        try:
            async with ClientSession() as session:
                async with session.get(mirror) as resp:
                    assert resp.status == 200
                    soup = BeautifulSoup(await resp.text(), features="lxml")
                    mirrors = [a["href"] for a in soup.find("ul").find_all("a")]
                    for mirror in mirrors:
                        try:
                            data, filename = await self.__get_all_bytes(mirror)
                            break
                        except Exception as e:
                            logger.error(
                                "Error downloading the book from %s link: %s", mirror, e
                            )
                            continue

        except Exception as e:
            logger.error(
                "Error downloading the book every http://library.lol mirrors: %s", e
            )
            return

        if not data or not filename:
            return

        if save_to_disk:
            self.__save_to_disk(filename, data, output)

        return data, filename

    def __save_to_disk(self, filename, data, output) -> None:
        """
        Internal method, don't use.
        Just writes the bytes to disk.
        """
        with open(path.join(output, filename), "wb") as f:
            f.write(data)

    async def __get_all_bytes(self, mirror) -> tuple[bytes, str | None]:
        """
        Internal method, don't use.
        Download the link and returns the bytes and the filename.
        """

        async with ClientSession() as session:
            async with session.get(mirror) as resp:
                assert resp.status == 200
                fname = findall(
                    r"(?:.*filename\*|filename)=(?:([^'\"]*)''|(\"))([^;]+)\2(?:[;`\n]|$)",
                    resp.headers.get("content-disposition"),
                )[0][2]
                data = await resp.read()

        return data, unquote(fname).strip()
