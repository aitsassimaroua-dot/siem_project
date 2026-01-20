# auth.py
from datetime import datetime
import os
from flask import request
import mysql.connector
from werkzeug.security import check_password_hash

# -----------------------------
# CONFIG MYSQL
# -----------------------------
MYSQL_CONFIG = {
    "host": "127.0.0.1",   # si MySQL est dans Docker (3307:3306)
    "port": 3307,
    "user": "authuser",
    "password": "authpass",
    "database": "authdb",
}

LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/auth_app.log")


# -----------------------------
# LOGGING
# -----------------------------
def log_attempt(username, status, reason):
    """Enregistre une tentative de connexion dans auth_app.log."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ip = request.remote_addr or "unknown"

    entry = f"{timestamp};user={username};ip={ip};status={status};reason={reason}\n"

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


# -----------------------------
# MYSQL HELPERS
# -----------------------------
def db_connect():
    """Retourne une connexion MySQL."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def get_password_hash(username):
    """Retourne le hash du mot de passe stocké en DB, ou None si l'utilisateur n'existe pas."""
    conn = db_connect()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        return row["password_hash"] if row else None
    finally:
        conn.close()


def user_exists(username):
    """Retourne True si l'utilisateur existe dans MySQL."""
    return get_password_hash(username) is not None


# -----------------------------
# SQL INJECTION CHECK
# -----------------------------
def looks_like_sql_injection(value: str) -> bool:
    if not value:
        return False

    patterns = ["'", "\"", ";", "--", "/*", "*/", " or ", " and ", "1=1","admin"]
    v = value.lower()
    return any(p in v for p in patterns)


# -----------------------------
# AUTHENTICATION
# -----------------------------
def authenticate(username, password):
    """
    Retourne (status, message, reason)
    """

    # 0) Détection SQL Injection
    if looks_like_sql_injection(username) or looks_like_sql_injection(password):
        log_attempt(username, "FAIL", "sql_injection_attempt")
        return "FAIL", "Tentative d'injection SQL détectée.", "sql_injection_attempt"

    # 1) Vérifier si l'utilisateur existe
    pw_hash = get_password_hash(username)
    if pw_hash is None:
        log_attempt(username, "FAIL", "unknown_user")
        return "FAIL", "Utilisateur inconnu.", "unknown_user"

    # 2) Vérifier le mot de passe
    if not check_password_hash(pw_hash, password):
        log_attempt(username, "FAIL", "bad_password")
        return "FAIL", "Mot de passe incorrect.", "bad_password"

    # 3) Succès
    log_attempt(username, "SUCCESS", "ok")
    return "SUCCESS", "Connexion réussie !", "ok"
