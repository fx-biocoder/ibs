"""
IBS - Índice de Bioactividad del Suelo
Entrenamiento del Modelo ML
"""

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler

FEATURES = ["co2_mg_kg_dia", "mo_porcentaje", "ph", "temp_celsius"]
TARGET = "ibs_score"
MODELO_VERSION = "rf_v1"



def cargar_datos(ruta_csv):
    df = pd.read_csv(ruta_csv)
    print(f"Dataset cargado: {len(df)} registros")
    return df



def entrenar(df):
    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = MinMaxScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    modelo = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    modelo.fit(X_train_sc, y_train)

    y_pred = modelo.predict(X_test_sc)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n── MÉTRICAS DEL MODELO ──────────────────")
    print(f"MAE (error promedio): {mae:.2f} puntos IBS")
    print(f"R² (ajuste): {r2:.4f}")
    print(f"─────────────────────────────────────────\n")

    return modelo, scaler, {"mae": round(mae, 4), "r2": round(r2, 4)}



def guardar(modelo, scaler, metricas, carpeta="output"):
    os.makedirs(carpeta, exist_ok=True)

    ruta_modelo = os.path.join(carpeta, "ibs_model.pkl")
    ruta_scaler = os.path.join(carpeta, "ibs_scaler.pkl")
    ruta_meta = os.path.join(carpeta, "model_meta.json")

    with open(ruta_modelo, "wb") as f:
        pickle.dump(modelo, f)

    with open(ruta_scaler, "wb") as f:
        pickle.dump(scaler, f)

    meta = {
        "version": MODELO_VERSION,
        "features": FEATURES,
        "target": TARGET,
        "metricas": metricas
    }
    with open(ruta_meta, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Modelo guardado: {ruta_modelo}")
    print(f"Scaler guardado: {ruta_scaler}")
    print(f"Metadata guardada: {ruta_meta}")


if __name__ == "__main__":
    ruta_csv = "output/dataset_ibs.csv"

    if not os.path.exists(ruta_csv):
        print(f"ERROR: No se encontró {ruta_csv}")
        print("Ejecutá primero: python generate_dataset.py")
        exit(1)

    df = cargar_datos(ruta_csv)
    modelo, scaler, metricas = entrenar(df)
    guardar(modelo, scaler, metricas, carpeta="output")
    print("Entrenamiento completo.")
