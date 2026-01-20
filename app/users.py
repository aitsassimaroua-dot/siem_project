# users.py
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "authuser",
    "password": "authpass",
    "database": "authdb",
}

def db_connect():
    return mysql.connector.connect(**MYSQL_CONFIG)


# -----------------------------
# Vérifier si utilisateur existe
# -----------------------------
def user_exists(username):
    conn = db_connect()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


# -----------------------------
# Créer un utilisateur
# -----------------------------
def create_user(username, password):
    if user_exists(username):
        return False

    hashed_pw = generate_password_hash(password, method="scrypt")


    conn = db_connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed_pw),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# -----------------------------
# Vérifier le mot de passe
# -----------------------------
def verify_password(username, password):
    conn = db_connect()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return False
        return check_password_hash(row["password_hash"], password)
    finally:
        conn.close()
