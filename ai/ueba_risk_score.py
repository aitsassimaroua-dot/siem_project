from elasticsearch import Elasticsearch, helpers
import math

# =========================
# CONFIG
# =========================

ES_HOST = "http://localhost:9200"  # Docker exposes 9200 on host
SOURCE_INDEX = "auth-logs-clean"   # your cleaned logs from Logstash
TARGET_INDEX = "auth-logs-enriched"  # new index with UEBA fields


def get_es_client():
    """
    Create Elasticsearch client.
    Security is disabled in your docker-compose, so no auth needed.
    """
    es = Elasticsearch(ES_HOST)
    # Simple test
    if not es.ping():
        raise RuntimeError("Cannot connect to Elasticsearch at {}".format(ES_HOST))
    return es


# =========================
# STEP 1 – LOAD ALL EVENTS
# =========================

def load_all_events(es):
    """
    Load all docs from SOURCE_INDEX using the scroll API.
    For a school project, this is fine (we don't expect millions of docs).
    """
    all_hits = []

    page = es.search(
        index=SOURCE_INDEX,
        body={"query": {"match_all": {}}},
        size=1000,
        scroll="2m",
    )

    scroll_id = page["_scroll_id"]
    hits = page["hits"]["hits"]
    all_hits.extend(hits)

    while len(hits) > 0:
        page = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = page["_scroll_id"]
        hits = page["hits"]["hits"]
        all_hits.extend(hits)

    print(f"Loaded {len(all_hits)} events from index '{SOURCE_INDEX}'")
    return all_hits


# =========================
# STEP 2 – BUILD USER PROFILES
# =========================

def build_user_profiles(hits):
    """
    Build simple UEBA profiles per user:

    - known_ips
    - known_hours
    - fail_rate
    """

    profiles = {}  # user -> dict

    for h in hits:
        src = h["_source"]
        user = src.get("user") or "UNKNOWN"
        ip = src.get("ip") or "UNKNOWN_IP"
        hour = src.get("hour")
        status = src.get("status", "").upper()

        if user not in profiles:
            profiles[user] = {
                "ips": set(),
                "hours": set(),
                "total": 0,
                "fails": 0,
            }

        p = profiles[user]
        p["ips"].add(ip)

        # hour might be stored as string or number
        try:
            if hour is not None:
                p["hours"].add(int(hour))
        except ValueError:
            pass

        p["total"] += 1
        if status == "FAIL":
            p["fails"] += 1

    # Compute fail_rate
    for user, p in profiles.items():
        if p["total"] > 0:
            p["fail_rate"] = p["fails"] / p["total"]
        else:
            p["fail_rate"] = 0.0

    print("Built profiles for", len(profiles), "users")
    return profiles


# =========================
# STEP 3 – RISK SCORE LOGIC
# =========================

SENSITIVE_USERS = {"admin", "root", "administrator"}

def compute_risk_for_event(src, profiles):
    user = src.get("user") or "UNKNOWN"
    ip = src.get("ip") or "UNKNOWN_IP"
    hour = src.get("hour")
    status = src.get("status", "").upper()

    profile = profiles.get(user, {
        "ips": set(),
        "hours": set(),
        "fail_rate": 0.0,
    })

    risk = 0

    # 1) Failed login -> suspicious
    if status == "FAIL":
        risk += 30

    # 2) Unusual hour
    try:
        h = int(hour) if hour is not None else None
    except ValueError:
        h = None

    if h is not None and len(profile["hours"]) > 0:
        if h not in profile["hours"]:
            risk += 25

    # 3) New IP for this user
    if len(profile["ips"]) > 0 and ip not in profile["ips"]:
        risk += 20

    # 4) Sensitive account (admin/root etc.)
    if user.lower() in SENSITIVE_USERS:
        risk += 15

    # 5) High failure rate user
    fail_rate = profile.get("fail_rate", 0.0)
    if fail_rate > 0.5 and status == "FAIL":
        risk += 10

    # Cap risk between 0 and 100
    risk = max(0, min(100, risk))

    # Map to levels
    if risk < 30:
        level = "low"
    elif risk < 70:
        level = "medium"
    else:
        level = "high"

    return risk, level


# =========================
# STEP 4 – ENRICH EVENTS & WRITE TO NEW INDEX
# =========================

def enrich_and_index(es, hits, profiles):
    """
    For each event:

    - compute risk_score & risk_level
    - copy original _source
    - index into TARGET_INDEX
    """
    actions = []

    for h in hits:
        src = h["_source"].copy()

        risk_score, risk_level = compute_risk_for_event(src, profiles)
        src["risk_score"] = risk_score
        src["risk_level"] = risk_level

        action = {
            "_index": TARGET_INDEX,
            "_source": src,
        }

        # you *could* reuse the same _id to avoid duplicates:
        # action["_id"] = h["_id"]

        actions.append(action)

    if actions:
        helpers.bulk(es, actions)
        print(f"Indexed {len(actions)} enriched events into '{TARGET_INDEX}'")
    else:
        print("No events to index.")


def main():
    es = get_es_client()

    # load events
    hits = load_all_events(es)

    if not hits:
        print("No events found in source index.")
        return

    # build profiles
    profiles = build_user_profiles(hits)

    # enrich + write
    enrich_and_index(es, hits, profiles)

    print("UEBA enrichment done.")


if __name__ == "__main__":
    main()
