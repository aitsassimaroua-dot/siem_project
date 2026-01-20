# soar.py
import smtplib
import os
from email.mime.text import MIMEText
from elasticsearch import Elasticsearch

# ==========================================
# CONFIG
# ==========================================
ES_HOST = "http://localhost:9200"

# --- CONFIG EMAIL GMAIL ---
ADMIN_EMAIL = "maroua.aitsassi@gmail.com"
FROM_EMAIL = "maroua.aitsassi@gmail.com"
APP_PASSWORD = "iqyscmuhyuswnapu"  # sans espaces


# ==========================================
# 1) NOTIFICATION EMAIL
# ==========================================
def notify_admin(log):
    """Envoie un email pour une alerte HIGH."""
    msg = MIMEText(
        f"🚨 ALERTE CRITIQUE DÉTECTÉE PAR LE SIEM\n\n"
        f"Utilisateur : {log.get('user')}\n"
        f"IP Source : {log.get('ip')}\n"
        f"Raison : {log.get('reason')}\n"
        f"Score de risque : {log.get('final_risk_score')}\n\n"
        f"Action SOAR : Notification + tentative de blocage IP."
    )

    msg["Subject"] = "🚨 Alerte HIGH détectée - SIEM"
    msg["From"] = FROM_EMAIL
    msg["To"] = ADMIN_EMAIL

    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login(FROM_EMAIL, APP_PASSWORD)
    s.send_message(msg)
    s.quit()

    print("📧 Email envoyé à l’administrateur.")


# ==========================================
# 2) BLOCAGE IP (SIMULÉ SUR MAC)
# ==========================================
def block_ip(ip):
    if not ip:
        return

    # Ignorer localhost et IP internes
    if ip.startswith(("127.", "192.168.", "10.", "172.")):
        print(f"⚠️ IP ignorée (interne) : {ip}")
        return

    print(f"🚫 Tentative de blocage IP : {ip}")
    cmd = f"sudo iptables -A INPUT -s {ip} -j DROP"
    result = os.system(cmd)

    if result == 0:
        print(f"✅ IP {ip} bloquée.")
    else:
        print("❌ Blocage non supporté sur cet OS (normal sur macOS).")


# ==========================================
# 3) TRAITEMENT SOAR
# ==========================================
def check_high_alerts():
    es = Elasticsearch(ES_HOST)

    # 🔑 FILTRE PRO : seulement les HIGH NON TRAITÉS
    results = es.search(
        index="auth-logs-final",
        size=50,
        query={
            "bool": {
                "must": [
                    {"match": {"final_alert_level": "HIGH"}}
                ],
                "must_not": [
                    {"exists": {"field": "soar_processed"}}
                ]
            }
        }
    )

    alerts = results["hits"]["hits"]
    print(f"🔍 {len(alerts)} nouvelles alertes HIGH à traiter.")

    for hit in alerts:
        log = hit["_source"]
        ip = log.get("ip")

        # Actions SOAR
        notify_admin(log)
        block_ip(ip)

        # Marquer comme traitée
        es.update(
            index="auth-logs-final",
            id=hit["_id"],
            body={"doc": {"soar_processed": True}}
        )

        print("✅ Alerte traitée et marquée.\n")


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    check_high_alerts()
