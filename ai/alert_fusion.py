#!/usr/bin/env python3
"""
Alert Fusion Script

Reads documents from `auth-logs-enriched`, combines rule-based risk and
ML anomaly score into `final_risk_score` and `final_alert_level`, and
indexes results into `auth-logs-final`.
"""

from elasticsearch import Elasticsearch, helpers
import math

# -------------------------------------------------------------------
# 1. CONFIGURATION
# -------------------------------------------------------------------

ES_HOST = "http://localhost:9200"      # if you run this inside a container in the same network, use "http://elasticsearch:9200"
SOURCE_INDEX = "auth-logs-enriched"
TARGET_INDEX = "auth-logs-final"
BATCH_SIZE = 500

# -------------------------------------------------------------------
# 2. FUSION LOGIC
# -------------------------------------------------------------------

def compute_final_risk(doc_source: dict) -> tuple[float, str]:
    """Compute final_risk_score and final_alert_level from a document."""
    # Safely extract fields with defaults
    risk_score = doc_source.get("risk_score", 0) or 0
    ml_score = doc_source.get("ml_anomaly_score", 0.0) or 0.0
    status = (doc_source.get("status") or "").upper()
    is_internal_ip = doc_source.get("is_internal_ip")

    # Some pipelines store booleans as strings like "true"/"false"
    if isinstance(is_internal_ip, str):
        is_internal_ip_bool = is_internal_ip.lower() == "true"
    else:
        is_internal_ip_bool = bool(is_internal_ip)

    weekday = doc_source.get("weekday", "")

    # --- WEIGHTED COMPONENTS ---------------------------------------
    base = float(risk_score)

    # ML component (0-1) -> 0-40
    ml_component = float(ml_score) * 40.0

    # Extra risk if login failed
    fail_bonus = 20.0 if status == "FAIL" else 0.0

    # External IPs are more suspicious
    ext_ip_bonus = 0.0 if is_internal_ip_bool else 15.0

    # Week-end logins slightly more suspicious
    weekend_bonus = 10.0 if weekday in ("Saturday", "Sunday") else 0.0

    final_score = base + ml_component + fail_bonus + ext_ip_bonus + weekend_bonus

    # Clip to [0, 100]
    final_score = max(0.0, min(100.0, final_score))

    # Map to alert level
    if final_score < 30:
        level = "LOW"
    elif final_score < 60:
        level = "MEDIUM"
    elif final_score < 80:
        level = "HIGH"
    else:
        level = "CRITICAL"

    # Optional: round to 1 decimal
    final_score = round(final_score, 1)

    return final_score, level

# -------------------------------------------------------------------
# 3. MAIN PIPELINE
# -------------------------------------------------------------------

def main():
    es = Elasticsearch(ES_HOST)

    # Create target index if it does not exist (simple dynamic mapping)
    if not es.indices.exists(index=TARGET_INDEX):
        es.indices.create(index=TARGET_INDEX, ignore=400)

    # Scroll through source index
    query = {"query": {"match_all": {}}}

    print(f"Reading from index [{SOURCE_INDEX}] and writing into [{TARGET_INDEX}]...")

    # Use helpers.scan for efficient scrolling
    docs = helpers.scan(
        es,
        index=SOURCE_INDEX,
        query=query,
        size=BATCH_SIZE,
        preserve_order=False
    )

    actions = []
    count = 0

    for doc in docs:
        source = doc["_source"]

        final_score, level = compute_final_risk(source)

        # Build new document – we copy everything and add two new fields
        new_source = dict(source)
        new_source["final_risk_score"] = final_score
        new_source["final_alert_level"] = level

        action = {
            "_index": TARGET_INDEX,
            "_id": doc["_id"],   # reuse same id, or omit this line to let ES generate new IDs
            "_source": new_source,
        }
        actions.append(action)
        count += 1

        # Bulk index in batches
        if len(actions) >= BATCH_SIZE:
            helpers.bulk(es, actions)
            print(f"Indexed {count} documents...")
            actions = []

    # Flush remaining docs
    if actions:
        helpers.bulk(es, actions)
        print(f"Indexed {count} documents (final batch).")

    print("Done. You can now create a data view on index 'auth-logs-final' in Kibana.")

if __name__ == "__main__":
    main()
