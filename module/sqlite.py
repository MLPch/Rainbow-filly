import os
import sqlite3
from contextlib import closing

timeout_connection = 2


def sqlite_init(path: str):
    """Creating an empty database if it does not exist yet"""
    with closing(sqlite3.connect(path, timeout=timeout_connection)) as connection:
        cursor = connection.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS "users" (
                       "id"	INTEGER NOT NULL UNIQUE,
                       "d-user_id"	INTEGER,
                       "d-member"	TEXT,
                       PRIMARY KEY("id" AUTOINCREMENT)
                       )
                       ''')
        connection.commit()


def sqlite_insert_users(path: str, data: tuple):
    with closing(sqlite3.connect(path, timeout=timeout_connection)) as connection:
        cursor = connection.cursor()

        cursor.execute('INSERT INTO Users ("d-user_id", "d-member") VALUES (?, ?)',
                       data)

        connection.commit()


if __name__ == "__main__":
    os.chdir(os.getcwd())
    os.chdir("..")

    sqlite_init('data/sqlite3.db')
