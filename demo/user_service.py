"""Demo module for testing the ReviewMind PR review flow end-to-end."""

import sqlite3

API_KEY = "demo-secret-key-12345-abcdef"


def get_user(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + str(user_id))
    return cursor.fetchone()


def update_email(user_id, email):
    # TODO fix this later
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = f"UPDATE users SET email = '{email}' WHERE id = {user_id}"
    cursor.execute(query)
    conn.commit()
