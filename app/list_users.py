# list_users.py
import mysql.connector

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "authuser",
    "password": "authpass",
    "database": "authdb",
}

def main():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id, username, created_at FROM users ORDER BY id ASC")
    rows = cur.fetchall()

    if not rows:
        print("Aucun utilisateur trouvé dans la base.")
    else:
        print("=== Utilisateurs enregistrés ===\n")
        for row in rows:
            print(f"ID: {row['id']}")
            print(f"Username: {row['username']}")
            print(f"Created at: {row['created_at']}")
            print("-" * 40)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
