# auth.py
from datetime import datetime
import os
from flask import request
from users import verify_password, user_exists


LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/auth_app.log")


def log_attempt(username, status, reason):
    """Enregistre une tentative de connexion dans auth_app.log."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ip = request.remote_addr

    entry = f"{timestamp};user={username};ip={ip};status={status};reason={reason}\n"

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def authenticate(username, password):
    """Retourne (status, message, reason)"""

    if not user_exists(username):
        log_attempt(username, "FAIL", "unknown_user")
        return "FAIL", "Utilisateur inconnu.", "unknown_user"

    if not verify_password(username, password):
        log_attempt(username, "FAIL", "bad_password")
        return "FAIL", "Mot de passe incorrect.", "bad_password"

    # Succès
    log_attempt(username, "SUCCESS", "ok")
    return "SUCCESS", "Connexion réussie !", "ok"