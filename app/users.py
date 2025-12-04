from werkzeug.security import generate_password_hash, check_password_hash
import json, os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, indent=4, ensure_ascii=False)

def user_exists(username):
    users = load_users()
    return username in users

def verify_password(username, password):
    users = load_users()
    if username not in users:
        return False
    hashed_pw = users[username]
    return check_password_hash(hashed_pw, password)

def create_user(username, password):
    users = load_users()
    if username in users:
        return False
    hashed_pw = generate_password_hash(password)  # hash sécurisé
    users[username] = hashed_pw
    save_users(users)
    return True
