# users.py
import json
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    """Charge les utilisateurs depuis users.json."""
    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users_dict):
    """Sauvegarde les utilisateurs dans users.json."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, indent=4, ensure_ascii=False)


def user_exists(username):
    """Vérifie si un utilisateur existe."""
    users = load_users()
    return username in users


def verify_password(username, password):
    """Vérifie si le mot de passe est correct."""
    users = load_users()
    return username in users and users[username] == password


def create_user(username, password):
    """Crée un nouvel utilisateur."""
    users = load_users()

    if username in users:
        return False  # utilisateur déjà existant

    users[username] = password
    save_users(users)
    return True