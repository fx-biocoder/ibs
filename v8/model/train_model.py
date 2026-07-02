"""
IBS - Índice de Bioactividad del Suelo
Entrenamiento del Modelo ML
"""

import pandas as pd
import pickle
import json
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from sys import stderr
from typing import Any

FEATURES = [
    "co2_mg_kg_dia", "mo_porcentaje", "ph", "temp_celsius",
    "enz_beta_glucosidasa", "enz_fosfatasa", "enz_arilsulfatasa", "enz_ureasa"
]
TARGET = "ibs_score"
MODELO_VERSION = "rf_v1"


def cargar_datos(ruta: str) -> pd.DataFrame:
    dataframe = pd.read_csv(ruta)
    print(f"Dataset cargado: {len(dataframe)} registros")
    return dataframe


def entrenar(dataframe: pd.DataFrame) -> tuple[RandomForestRegressor, MinMaxScaler, dict]:
    X = dataframe[FEATURES]
    y = dataframe[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    minmax_scaler = MinMaxScaler()
    X_train_sc = minmax_scaler.fit_transform(X_train)
    X_test_sc = minmax_scaler.transform(X_test)

    modelo_rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    modelo_rf.fit(X_train_sc, y_train)

    y_pred = modelo_rf.predict(X_test_sc)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    metricas_modelo = f"""── MÉTRICAS DEL MODELO ──────────────────
    MAE (error promedio): {mae:.2f} puntos IBS
    R² (ajuste): {r2:.4f}
    ─────────────────────────────────────────\n
    """
    print(metricas_modelo)

    return modelo_rf, minmax_scaler, {"mae": round(mae, 4), "r2": round(r2, 4)}


def guardar(modelo_rf: RandomForestRegressor,
            minmax_scaler: MinMaxScaler,
            metricas_meta: Any,
            carpeta: str = "output") -> None:
    os.makedirs(carpeta, exist_ok=True)

    ruta_modelo = os.path.join(carpeta, "ibs_model.pkl")
    ruta_scaler = os.path.join(carpeta, "ibs_scaler.pkl")
    ruta_meta = os.path.join(carpeta, "model_meta.json")

    with open(ruta_modelo, "wb") as f:
        pickle.dump(modelo_rf, f)       # Warning: Expected type 'SupportsWrite[bytes]', got 'BufferedWriter' instead

    with open(ruta_scaler, "wb") as f:
        pickle.dump(minmax_scaler, f)   # Warning: Expected type 'SupportsWrite[bytes]', got 'BufferedWriter' instead

    meta = {
        "version": MODELO_VERSION,
        "features": FEATURES,
        "target": TARGET,
        "metricas": metricas_meta
    }
    with open(ruta_meta, "w") as f:
        json.dump(meta, f, indent=2)

    info = f"""Modelo guardado: {ruta_modelo}
    Scaler guardado: {ruta_scaler}
    Metadata guardada: {ruta_meta}
    """
    print(info)


if __name__ == "__main__":
    ruta_csv = "output/dataset_ibs.csv"

    if not os.path.exists(ruta_csv):
        print(f"""ERROR: No se encontró {ruta_csv}
        Ejecutá primero: python generate_dataset.py
        """, file=stderr)
        exit(1)

    df = cargar_datos(ruta_csv)
    modelo, scaler, metricas = entrenar(df)
    guardar(modelo, scaler, metricas, carpeta="output")
    print("Entrenamiento completo.")
