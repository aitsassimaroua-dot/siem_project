# ai/features.py

import numpy as np
import pandas as pd

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    return df

def add_basic_flags(df: pd.DataFrame) -> pd.DataFrame:
    df["is_fail"] = (df["status"] == "FAIL").astype(int)
    df["is_internal_ip"] = df["ip"].str.startswith(("192.168.", "10.")).astype(int)
    df["is_external_ip"] = 1 - df["is_internal_ip"]
    return df

def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit une matrice de features pour le modèle ML.
    Tu peux ajouter/enlever des features selon ton besoin.
    """
    # on part du df déjà enrichi (risk_score, hour, etc.)
    df = add_time_features(df.copy())
    df = add_basic_flags(df)

    features = pd.DataFrame(index=df.index)
    features["hour_sin"] = df["hour_sin"]
    features["hour_cos"] = df["hour_cos"]
    features["is_fail"] = df["is_fail"]
    features["is_internal_ip"] = df["is_internal_ip"]
    features["risk_score"] = df["risk_score"].fillna(0)

    # si tu veux, tu peux ajouter d'autres colonnes ici
    return features
