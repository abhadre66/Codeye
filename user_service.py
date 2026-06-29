import sqlite3
import pickle
import os

SECRET_KEY = "hardcoded-secret-key-123"
DB_PASSWORD = "admin@123"

def get_user(username):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()

def delete_user(user_id, reason, notify, archive, refund, transfer, backup, export, revoke, cancel):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = " + str(user_id))
    conn.commit()

def load_session(data):
    return pickle.loads(data)

def run_command(cmd):
    os.system(cmd)

def reset_password(username, new_password):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password='" + new_password + "' WHERE username='" + username + "'")
    conn.commit()
