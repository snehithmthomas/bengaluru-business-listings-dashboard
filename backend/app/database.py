from collections.abc import Iterator
from contextlib import contextmanager

import mysql.connector
from mysql.connector.connection import MySQLConnection

from .config import get_database_config


@contextmanager
def connection() -> Iterator[MySQLConnection]:
    conn = mysql.connector.connect(**get_database_config())
    try:
        yield conn
    finally:
        conn.close()
