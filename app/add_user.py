# add_user.py
import mysql.connector
import getpass
from werkzeug.security import generate_password_hash

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "authuser",
    "password": "authpass",
    "database": "authdb",
}

def main():
    print("=== Ajouter un utilisateur MySQL ===")

    username = input("Nom d'utilisateur : ").strip()
    password = getpass.getpass("Mot de passe : ")

    # Hash SCrypt (compatible Flask)
    password_hash = generate_password_hash(password, method="scrypt")

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
        """, (username, password_hash))

        conn.commit()
        print(f"✅ Utilisateur '{username}' ajouté avec succès.")
        print(f"🔒 Hash stocké : {password_hash}")

    except mysql.connector.errors.IntegrityError:
        print("⚠️ Cet utilisateur existe déjà !")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
