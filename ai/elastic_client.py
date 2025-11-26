# ai/elastic_client.py

from elasticsearch import Elasticsearch, helpers
import pandas as pd
from typing import List, Dict, Optional
from config import ES_URL

es = Elasticsearch(ES_URL)

def fetch_index_as_dataframe(index: str, size: int = 10000, query: Optional[Dict] = None) -> pd.DataFrame:
    """
    Récupère jusqu'à 'size' documents d'un index Elasticsearch et les retourne en DataFrame.
    """
    if query is None:
        query = {"query": {"match_all": {}}}

    resp = es.search(index=index, body={**query, "size": size})
    hits = [h["_source"] for h in resp["hits"]["hits"]]
    if not hits:
        return pd.DataFrame()
    return pd.DataFrame(hits)

def bulk_index(index: str, docs: List[Dict], id_field: Optional[str] = None):
    """
    Indexation en bulk d'une liste de documents dans Elasticsearch.
    Optionnellement, utiliser 'id_field' pour l'_id.
    """
    actions = []
    for doc in docs:
        action = {
            "_index": index,
            "_source": doc,
        }
        if id_field and id_field in doc:
            action["_id"] = doc[id_field]
        actions.append(action)

    if not actions:
        print("[bulk_index] No documents to index.")
        return

    helpers.bulk(es, actions)
    print(f"[bulk_index] Indexed {len(actions)} docs into {index}")
