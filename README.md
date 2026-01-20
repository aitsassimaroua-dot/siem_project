# Mini SIEM - Security Information and Event Management

Un système SIEM complet pour la surveillance et l'analyse des logs d'authentification, utilisant Flask, la stack ELK (Elasticsearch, Logstash, Kibana) et des techniques UEBA/SOAR.

## Objectif du Projet

Ce projet implémente un mini SIEM capable de :
- Collecter les logs d'authentification d'une application web
- Détecter les tentatives d'intrusion (SQL injection, brute force)
- Analyser les comportements utilisateurs (UEBA)
- Automatiser les réponses aux incidents (SOAR)
- Visualiser les données de sécurité via Kibana

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Flask App     │────▶│   Filebeat   │────▶│    Logstash     │
│   (Login)       │     │              │     │   (Parsing)     │
└─────────────────┘     └──────────────┘     └────────┬────────┘
        │                                             │
        ▼                                             ▼
┌─────────────────┐                         ┌─────────────────┐
│     MySQL       │                         │  Elasticsearch  │
│   (Users DB)    │                         │   (Indexing)    │
└─────────────────┘                         └────────┬────────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    │                                │                                │
                    ▼                                ▼                                ▼
           ┌──────────────┐                ┌──────────────┐                 ┌──────────────┐
           │    Kibana    │                │  UEBA Script │                 │     SOAR     │
           │ (Dashboard)  │                │ (Risk Score) │                 │   (Alerts)   │
           └──────────────┘                └──────────────┘                 └──────────────┘
```

## Fonctionnalités

### 1. Application d'Authentification (Flask)
- Interface de connexion web
- Validation des credentials via MySQL
- Détection des tentatives d'injection SQL
- Journalisation de toutes les tentatives (succès/échec)

### 2. Pipeline ELK
- **Filebeat** : Collecte les logs depuis `auth_app.log`
- **Logstash** : Parse et enrichit les logs
  - Extraction des champs (timestamp, user, ip, status, reason)
  - Géolocalisation des IPs
  - Détection des IPs internes/externes
  - Calcul du score de risque ML
- **Elasticsearch** : Stockage et indexation
  - `auth-logs-clean` : Logs parsés
  - `auth-logs-enriched` : Logs avec UEBA
  - `auth-logs-final` : Logs avec score final
- **Kibana** : Visualisation et dashboards

### 3. UEBA (User and Entity Behavior Analytics)
Le module `ai/ueba_risk_score.py` analyse le comportement des utilisateurs :
- **IPs connues** : Détecte les connexions depuis de nouvelles IPs
- **Heures habituelles** : Identifie les connexions à des heures inhabituelles
- **Taux d'échec** : Surveille les utilisateurs avec beaucoup d'échecs
- **Comptes sensibles** : Attention particulière sur admin/root

Score de risque (0-100) :
| Facteur | Points |
|---------|--------|
| Échec de connexion | +30 |
| Heure inhabituelle | +25 |
| Nouvelle IP | +20 |
| Compte sensible | +15 |
| Taux d'échec élevé | +10 |

### 4. SOAR (Security Orchestration, Automation and Response)
Le module `app/soar.py` automatise les réponses :
- Détection des alertes HIGH non traitées
- Envoi d'email à l'administrateur
- Tentative de blocage IP (iptables)
- Marquage des alertes comme traitées

## Prérequis

- Python 3.12+
- Docker & Docker Compose
- Filebeat installé localement

## Installation

### 1. Cloner le repository
```bash
git clone https://github.com/aitsassimaroua-dot/siem_project.git
cd siem_project
```

### 2. Créer l'environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows
pip install flask mysql-connector-python werkzeug elasticsearch
```

### 3. Lancer les services Docker
```bash
cd elastic
docker-compose up -d
```

Cela démarre :
- Elasticsearch sur `localhost:9200`
- Kibana sur `localhost:5601`
- Logstash sur `localhost:5044`
- MySQL sur `localhost:3307`

### 4. Créer un utilisateur dans MySQL
```bash
python app/add_user.py
```

### 5. Lancer l'application Flask
```bash
cd app
python app.py
```
L'application s'ouvre automatiquement sur `http://127.0.0.1:5000`

### 6. Configurer Filebeat
```bash
# Modifier le chemin dans filebeat.yml si nécessaire
filebeat -e -c filebeat.yml
```

## Structure du Projet

```
DataSecurity-Project/
├── app/
│   ├── app.py              # Application Flask principale
│   ├── auth.py             # Logique d'authentification + logging
│   ├── users.py            # Gestion des utilisateurs MySQL
│   ├── add_user.py         # Script pour ajouter un utilisateur
│   ├── list_users.py       # Script pour lister les utilisateurs
│   ├── soar.py             # Module SOAR (alertes + réponses)
│   └── templates/
│       └── login.html      # Page de connexion
├── ai/
│   └── ueba_risk_score.py  # Analyse comportementale UEBA
├── elastic/
│   └── docker-compose.yml  # Configuration Docker ELK + MySQL
├── logstash/
│   └── logstash.conf       # Pipeline Logstash
├── logs/
│   └── auth_app.log        # Fichier de logs d'authentification
└── filebeat.yml            # Configuration Filebeat
```

## Format des Logs

Les logs sont au format suivant :
```
2024-12-09T21:30:00Z;user=john;ip=192.168.1.100;status=SUCCESS;reason=ok
2024-12-09T21:31:00Z;user=admin;ip=10.0.0.5;status=FAIL;reason=sql_injection_attempt
```

## Détection des Menaces

| Type de Menace | Détection | Niveau d'Alerte |
|----------------|-----------|-----------------|
| SQL Injection | Patterns dans username/password | HIGH |
| Brute Force | Échecs répétés | MEDIUM/HIGH |
| Compte inconnu | Username inexistant | LOW |
| Mauvais mot de passe | Password incorrect | LOW |
| Heure suspecte | Connexion hors heures habituelles | MEDIUM |
| Nouvelle IP | IP jamais vue pour cet utilisateur | MEDIUM |

## Visualisation Kibana

Accédez à Kibana sur `http://localhost:5601` pour :
- Créer des dashboards de sécurité
- Visualiser les tentatives de connexion en temps réel
- Analyser les scores de risque
- Filtrer par utilisateur, IP, statut

## Technologies Utilisées

- **Backend** : Python, Flask
- **Base de données** : MySQL 8.0
- **Stack ELK** : Elasticsearch, Logstash, Kibana 8.12.1
- **Collecte** : Filebeat
- **Sécurité** : Werkzeug (hashing), détection SQL injection
- **UEBA/SOAR** : Scripts Python personnalisés

## Auteurs

Projet réalisé dans le cadre du cours de Sécurité des Données.

## Licence

MIT License
