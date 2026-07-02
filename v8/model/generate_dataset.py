"""
IBS - Índice de Bioactividad del Suelo
Generador de Dataset Sintético
"""

import numpy as np
import pandas as pd
import os

RANGOS = {
    "co2_mg_kg_dia": {
        "min": 30, 
        "max": 600, 
        "optimo": 400
    },
    "mo_porcentaje": {
        "min": 0.3, 
        "max": 6.0, 
        "optimo": 4.0
    },
    "ph": {
        "min": 4.5, 
        "max": 9.0, 
        "optimo": 6.5
    },
    "temp_celsius": {
        "min": 5.0, 
        "max": 40.0, 
        "optimo": 22.0
    },
    "enz_beta_glucosidasa": {
        "min": 0.0, 
        "max": 10.0, 
        "optimo": 10.0
    },
    "enz_fosfatasa": {
        "min": 0.0, 
        "max": 10.0, 
        "optimo": 10.0
    },
    "enz_arilsulfatasa": {
        "min": 0.0, 
        "max": 10.0, 
        "optimo": 10.0
    },
    "enz_ureasa": {
        "min": 0.0, 
        "max": 10.0, 
        "optimo": 5.0
    },
}

PESOS = {
    "co2": 0.35,
    "mo": 0.25,
    "ph": 0.15,
    "temp": 0.10,
    "enz_beta_glucosidasa": 0.0375,
    "enz_fosfatasa": 0.0375,
    "enz_arilsulfatasa": 0.0375,
    "enz_ureasa": 0.0375
}


def normalizar(valor: float, minimo: float, maximo: float) -> float:
    return max(0.0, min(1.0, (valor - minimo) / (maximo - minimo)))


def score_ph(ph: float) -> float:
    return float(np.exp(-0.5 * ((ph - 6.5) / 1.2) ** 2))


def score_temp(temp: float) -> float:
    return float(np.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2))


def score_ureasa(ureasa: float) -> float:
    # Óptimo en 5.0, campana de Gauss para penalizar excesos
    return float(np.exp(-0.5 * ((ureasa - 5.0) / 2.5) ** 2))


def calcular_ibs(co2: float,
                 mo: float,
                 ph: float,
                 temp: float,
                 beta_glucosidasa: float,
                 fosfatasa: float,
                 arilsulfatasa: float,
                 ureasa: float) -> float:
    co2_norm = normalizar(co2, RANGOS["co2_mg_kg_dia"]["min"], RANGOS["co2_mg_kg_dia"]["max"])
    mo_norm = normalizar(mo, RANGOS["mo_porcentaje"]["min"], RANGOS["mo_porcentaje"]["max"])
    ph_sc = score_ph(ph)
    temp_sc = score_temp(temp)

    beta_norm = normalizar(beta_glucosidasa, RANGOS["enz_beta_glucosidasa"]["min"], RANGOS["enz_beta_glucosidasa"]["max"])
    fosf_norm = normalizar(fosfatasa, RANGOS["enz_fosfatasa"]["min"], RANGOS["enz_fosfatasa"]["max"])
    aril_norm = normalizar(arilsulfatasa, RANGOS["enz_arilsulfatasa"]["min"], RANGOS["enz_arilsulfatasa"]["max"])
    urea_sc = score_ureasa(ureasa)

    ibs = (
        (co2_norm * PESOS["co2"]) +
        (mo_norm * PESOS["mo"]) +
        (ph_sc * PESOS["ph"]) +
        (temp_sc * PESOS["temp"]) +
        (beta_norm * PESOS["enz_beta_glucosidasa"]) +
        (fosf_norm * PESOS["enz_fosfatasa"]) +
        (aril_norm * PESOS["enz_arilsulfatasa"]) +
        (urea_sc * PESOS["enz_ureasa"])
    )
    return round(ibs * 100, 2)


def _muestrar_enzima_correlacionada(rng: np.random.Generator,
                                    factor_modulador: float,
                                    ruido_sigma: float = 2.0) -> float:
    """
    Genera un valor de enzima (0-10) modulado por un factor [0, 1].
    El factor empuja la media hacia 10*factor; el ruido gaussiano agrega
    variabilidad realista. Simula que el pH (u otro modulador) condiciona
    la actividad enzimática sin determinarla completamente.
    """
    media = 10.0 * factor_modulador
    valor = float(rng.normal(media, ruido_sigma))
    return round(max(0.0, min(10.0, valor)), 2)


def generar_dataset(n_registros: int = 3000, semilla: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    registros = []

    for _ in range(n_registros):
        # Variables independientes
        co2 = round(float(rng.uniform(RANGOS["co2_mg_kg_dia"]["min"], RANGOS["co2_mg_kg_dia"]["max"])), 2)
        mo = round(float(rng.uniform(RANGOS["mo_porcentaje"]["min"], RANGOS["mo_porcentaje"]["max"])), 2)
        ph = round(float(rng.uniform(RANGOS["ph"]["min"], RANGOS["ph"]["max"])), 2)
        temp = round(float(rng.uniform(RANGOS["temp_celsius"]["min"], RANGOS["temp_celsius"]["max"])), 2)

        # Factor pH normalizado [0, 1], modula todas las enzimas
        # A pH extremo la actividad enzimática cae
        factor_ph = score_ph(ph)

        # Factor MO normalizado [0, 1], modula enzimas ligadas a descomposición
        factor_mo = normalizar(mo, RANGOS["mo_porcentaje"]["min"], RANGOS["mo_porcentaje"]["max"])

        # Beta-glucosidasa depende del pH Y de la MO disponible (sustrato)
        beta_glucosidasa = _muestrar_enzima_correlacionada(rng, factor_ph * factor_mo)

        # Fosfatasa y arilsulfatasa dependen principalmente del pH
        fosfatasa = _muestrar_enzima_correlacionada(rng, factor_ph)
        arilsulfatasa = _muestrar_enzima_correlacionada(rng, factor_ph)

        # Ureasa es óptima en pH neutro, modulada por pH
        ureasa_base = float(rng.uniform(RANGOS["enz_ureasa"]["min"], RANGOS["enz_ureasa"]["max"]))
        ureasa = round(max(0.0, min(10.0, ureasa_base * (0.5 + 0.5 * factor_ph))), 2)

        ibs_base = calcular_ibs(co2, mo, ph, temp, beta_glucosidasa, fosfatasa, arilsulfatasa, ureasa)

        ruido = float(rng.normal(0, 3.0))
        ibs_final = round(max(0.0, min(100.0, ibs_base + ruido)), 2)

        registros.append({
            "co2_mg_kg_dia": co2,
            "mo_porcentaje": mo,
            "ph": ph,
            "temp_celsius": temp,
            "enz_beta_glucosidasa": beta_glucosidasa,
            "enz_fosfatasa": fosfatasa,
            "enz_arilsulfatasa": arilsulfatasa,
            "enz_ureasa": ureasa,
            "ibs_score": ibs_final,
            "es_ruido": 1
        })

    dataframe = pd.DataFrame(registros)
    return dataframe


def exportar(dataframe: pd.DataFrame, carpeta: str = "output") -> str:
    os.makedirs(carpeta, exist_ok=True)

    ruta_csv = os.path.join(carpeta, "dataset_ibs.csv")
    dataframe.to_csv(ruta_csv, index=False)
    print(f"CSV exportado: {ruta_csv}")

    ruta_json = os.path.join(carpeta, "dataset_ibs.json")
    dataframe.to_json(ruta_json, orient="records", indent=2)
    print(f"JSON exportado: {ruta_json}")

    ruta_sql = os.path.join(carpeta, "dataset_ibs_inserts.sql")
    with open(ruta_sql, "w") as f:
        f.write("INSERT INTO dataset_sintetico (co2_mg_kg_dia, mo_porcentaje, ph, temp_celsius, enz_beta_glucosidasa, enz_fosfatasa, enz_arilsulfatasa, enz_ureasa, ibs_score, es_ruido) VALUES\n")
        filas = []
        for _, row in dataframe.iterrows():
            filas.append(
                f"({row['co2_mg_kg_dia']}, {row['mo_porcentaje']}, {row['ph']}, {row['temp_celsius']}, {row['enz_beta_glucosidasa']}, {row['enz_fosfatasa']}, {row['enz_arilsulfatasa']}, {row['enz_ureasa']}, {row['ibs_score']}, {int(row['es_ruido'])})"
            )
        f.write(",\n".join(filas) + ";\n")
    print(f"SQL exportado: {ruta_sql}")

    return ruta_csv


def mostrar_resumen(dataframe: pd.DataFrame) -> None:
    resumen = f"""\n── RESUMEN DEL DATASET ──────────────────
    Total registros: {len(dataframe)}
    IBS promedio: {dataframe['ibs_score'].mean():.2f}
    IBS mínimo: {dataframe['ibs_score'].min():.2f}"
    IBS máximo: {dataframe['ibs_score'].max():.2f}\n\n
    """

    bins = [0, 30, 50, 70, 85, 100]
    labels = ["critico", "bajo", "medio", "bueno", "excelente"]
    dataframe["estado"] = pd.cut(dataframe["ibs_score"], bins=bins, labels=labels, include_lowest=True)

    distribucion = f"""Distribución por estado:
    {dataframe["estado"].value_counts().sort_index().to_string()}
    ─────────────────────────────────────────
    
    """
    resumen += "\n" + distribucion
    print(resumen)


if __name__ == "__main__":
    print("Generando dataset sintético IBS...")
    df = generar_dataset(n_registros=3000)
    mostrar_resumen(df)
    exportar(df, carpeta="output")
    print("Listo.")
