# ai/config.py

ES_URL = "http://localhost:9200"

# Index utilisés dans Elasticsearch
INDEX_SRC_CLEAN = "weblogs"               # logs normalisés de Logstash (source)
INDEX_ENRICHED = "auth-logs-enriched"     # logs enrichis UEBA + ML
INDEX_ALERTS_ENRICHED = "alerts-enriched" # alertes fusionnées

# Chemins locaux pour le développement hors-Elasticsearch
DATA_DIR = "ai/data"
SAMPLE_LOGS = f"{DATA_DIR}/sample_logs.csv"
SAMPLE_LOGS_ENRICHED = f"{DATA_DIR}/sample_logs_enriched.csv"
SAMPLE_LOGS_ENRICHED_ML = f"{DATA_DIR}/sample_logs_enriched_ml.csv"
SAMPLE_ALERTS_SEVERITY = f"{DATA_DIR}/sample_alerts_with_severity.csv"

MODEL_DIR = "ai/models"
ISOFOREST_MODEL_PATH = f"{MODEL_DIR}/isolation_forest.joblib"

def run_pipeline_from_elastic():
    try:
        print(f"[PIPELINE] Fetching logs from index: {INDEX_SRC_CLEAN}")
        df = fetch_index_as_dataframe(INDEX_SRC_CLEAN, size=10000)
    except Exception as e:
        print(f"[WARNING] Could not fetch from Elasticsearch: {e}")
        print(f"[FALLBACK] Using sample logs from {SAMPLE_LOGS}")
        df = pd.read_csv(SAMPLE_LOGS)
    
    # ...rest of code...
