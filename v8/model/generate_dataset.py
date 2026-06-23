"""
IBS - Índice de Bioactividad del Suelo
Generador de Dataset Sintético
"""

import numpy as np
import pandas as pd
import json
import os



RANGOS = {
    "co2_mg_kg_dia": {"min": 30, "max": 600, "optimo": 400},
    "mo_porcentaje": {"min": 0.3, "max": 6.0, "optimo": 4.0},
    "ph": {"min": 4.5, "max": 9.0, "optimo": 6.5},
    "temp_celsius": {"min": 5.0, "max": 40.0, "optimo": 22.0},
}


def normalizar(valor, minimo, maximo):
    return max(0.0, min(1.0, (valor - minimo) / (maximo - minimo)))

def score_ph(ph):
    return float(np.exp(-0.5 * ((ph - 6.5) / 1.2) ** 2))

def score_temp(temp):
    return float(np.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2))


def calcular_ibs(co2, mo, ph, temp):
    co2_norm = normalizar(co2, RANGOS["co2_mg_kg_dia"]["min"], RANGOS["co2_mg_kg_dia"]["max"])
    mo_norm = normalizar(mo, RANGOS["mo_porcentaje"]["min"], RANGOS["mo_porcentaje"]["max"])
    ph_sc = score_ph(ph)
    temp_sc = score_temp(temp)

    ibs = (co2_norm * 0.40) + (mo_norm * 0.30) + (ph_sc * 0.20) + (temp_sc * 0.10)
    return round(ibs * 100, 2)


def generar_dataset(n_registros=3000, semilla=42):
    rng = np.random.default_rng(semilla)
    registros = []

    for _ in range(n_registros):
        co2 = round(float(rng.uniform(RANGOS["co2_mg_kg_dia"]["min"], RANGOS["co2_mg_kg_dia"]["max"])), 2)
        mo = round(float(rng.uniform(RANGOS["mo_porcentaje"]["min"], RANGOS["mo_porcentaje"]["max"])), 2)
        ph = round(float(rng.uniform(RANGOS["ph"]["min"], RANGOS["ph"]["max"])), 2)
        temp = round(float(rng.uniform(RANGOS["temp_celsius"]["min"], RANGOS["temp_celsius"]["max"])), 2)

        ibs_base = calcular_ibs(co2, mo, ph, temp)

        ruido = float(rng.normal(0, 3.0))
        ibs_final = round(max(0.0, min(100.0, ibs_base + ruido)), 2)

        registros.append({
            "co2_mg_kg_dia": co2,
            "mo_porcentaje": mo,
            "ph": ph,
            "temp_celsius": temp,
            "ibs_score": ibs_final,
            "es_ruido": 1
        })

    df = pd.DataFrame(registros)
    return df


def exportar(df, carpeta="output"):
    os.makedirs(carpeta, exist_ok=True)

    ruta_csv = os.path.join(carpeta, "dataset_ibs.csv")
    df.to_csv(ruta_csv, index=False)
    print(f"CSV exportado: {ruta_csv}")

    ruta_json = os.path.join(carpeta, "dataset_ibs.json")
    df.to_json(ruta_json, orient="records", indent=2)
    print(f"JSON exportado: {ruta_json}")

    ruta_sql = os.path.join(carpeta, "dataset_ibs_inserts.sql")
    with open(ruta_sql, "w") as f:
        f.write("INSERT INTO dataset_sintetico (co2_mg_kg_dia, mo_porcentaje, ph, temp_celsius, ibs_score, es_ruido) VALUES\n")
        filas = []
        for _, row in df.iterrows():
            filas.append(
                f"({row['co2_mg_kg_dia']}, {row['mo_porcentaje']}, {row['ph']}, {row['temp_celsius']}, {row['ibs_score']}, {int(row['es_ruido'])})"
            )
        f.write(",\n".join(filas) + ";\n")
    print(f"SQL exportado: {ruta_sql}")

    return ruta_csv


def mostrar_resumen(df):
    print("\n── RESUMEN DEL DATASET ──────────────────")
    print(f"Total registros: {len(df)}")
    print(f"IBS promedio: {df['ibs_score'].mean():.2f}")
    print(f"IBS mínimo: {df['ibs_score'].min():.2f}")
    print(f"IBS máximo: {df['ibs_score'].max():.2f}")
    print()
    print("Distribución por estado:")
    bins = [0, 30, 50, 70, 85, 100]
    labels = ["critico", "bajo", "medio", "bueno", "excelente"]
    df["estado"] = pd.cut(df["ibs_score"], bins=bins, labels=labels, include_lowest=True)
    print(df["estado"].value_counts().sort_index().to_string())
    print("─────────────────────────────────────────\n")


if __name__ == "__main__":
    print("Generando dataset sintético IBS...")
    df = generar_dataset(n_registros=3000)
    mostrar_resumen(df)
    exportar(df, carpeta="output")
    print("Listo.")
