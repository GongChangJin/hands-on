"""Parameterized SQL helpers."""


def find_user(cursor, username: str):
    return cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()


def find_order(cursor, order_id: str):
    return cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchall()
