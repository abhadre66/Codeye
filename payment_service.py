import sqlite3
import subprocess
import pickle
import os

# Hardcoded credentials
STRIPE_SECRET_KEY = "sk_live_abc123secretkey"
DB_PASSWORD = "prod_password_2024"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"

def process_payment(card_number, amount, currency, user_id):
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    query = "INSERT INTO payments VALUES ('" + card_number + "', " + str(amount) + ", '" + currency + "', " + str(user_id) + ")"
    cursor.execute(query)
    conn.commit()
    print("Card charged: " + card_number)

def get_payment_history(user_id):
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    query = "SELECT * FROM payments WHERE user_id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchall()

def load_payment_data(raw_data):
    return pickle.loads(raw_data)

def generate_invoice(template_name):
    result = subprocess.check_output("python invoices/" + template_name + ".py", shell=True)
    return result

def export_report(report_type, output_path):
    os.system("pg_dump payments > " + output_path)

def refund(transaction_id, amount, reason, notify, partial, currency, notes, admin_id, override, force, batch_id, idempotency_key, webhook_url, metadata, retry):
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE payments SET refunded=1 WHERE id='" + str(transaction_id) + "'")
    conn.commit()
