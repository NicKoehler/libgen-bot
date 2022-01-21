import logging
import sqlite3
import psycopg2
from urllib.parse import urlparse


class Connect:
    def __init__(self, database_url: str, logger) -> None:
        self.connect = None
        if database_url:
            logger.info("Using PostgreSQL database.")
            database = urlparse(database_url)
            self.connect = lambda: psycopg2.connect(
                dbname=database.path[1:],
                user=database.username,
                password=database.password,
                host=database.hostname,
                port=database.port,
            )
            self._val = "%s"
        else:
            logging.info("Using local SQLite database.")
            self.connect = lambda: sqlite3.connect("database.db")
            self._val = "?"


class Database(Connect):
    def __init__(self, host, logger) -> None:
        super().__init__(host, logger)
        self.logger = logger
        self.create_user_table()
        self.users = self.get_users()

    def execute(self, query: str, args: tuple = ()) -> None:
        data = None
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        if "SELECT" in query:
            data = cur.fetchall()
        conn.close()
        return data

    def create_user_table(self):
        self.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id BIGINT PRIMARY KEY, "
            "language_code TEXT, "
            "owner BOOLEAN DEFAULT FALSE);"
        )

    def get_users(self) -> dict:
        """
        return a dict of users
        """
        self.logger.info("Getting users from database.")
        users = self.execute("SELECT id, language_code, owner FROM users")
        if users:
            return {user[0]: {"lang": user[1], "owner": user[2]} for user in users}

        return dict()

    def add_user(self, user_id: int, lang_code: str, owner: bool = False) -> None:
        self.logger.info(f"Adding user {user_id} to database.")
        self.execute(
            "INSERT INTO users (id, language_code, owner ) "
            f"VALUES ({self._val}, {self._val}, {self._val} );",
            (
                user_id,
                lang_code,
                owner,
            ),
        )
        self.users[user_id] = {"lang": lang_code, "owner": owner}

    def remove_user(self, user_id: int) -> None:
        self.logger.info(f"Removing user {user_id} from database.")
        self.execute(f"DELETE FROM users WHERE id = {self._val}", (user_id,))
        self.users.pop(user_id)

    def set_language(self, user_id: int, lang_code: str) -> None:
        self.logger.info(f"Setting language for user {user_id} to {lang_code}.")
        self.execute(
            f"UPDATE users SET language_code = {self._val} WHERE id = {self._val}",
            (lang_code, user_id),
        )
        self.users[user_id]["lang"] = lang_code
