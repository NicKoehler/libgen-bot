from base64 import urlsafe_b64encode, urlsafe_b64decode


async def get_ext_and_query_from_message(event) -> tuple[str]:
    """
    Get the query from the message.
    """
    text_msg = (await event.get_message()).raw_text.split("\n")[-2].split(" ")

    extension = text_msg[2]
    query = " ".join(text_msg[4:])

    return extension, query


def clean_query(query: str, split_char=None) -> str:
    """
    Cleans the query
    """

    return " ".join(query.split(split_char)).casefold()


def base64_encode(s: str) -> str:
    """
    Encode a string in base64
    """
    return str(urlsafe_b64encode(s.encode("utf-8")), "utf-8")


def base64_decode(s: str) -> str:
    """
    Decode a string in base64
    """
    return urlsafe_b64decode(s).decode("utf-8")
