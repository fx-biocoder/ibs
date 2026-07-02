"""
IBS - Índice de Bioactividad del Suelo
Microservicio Flask — Puerto 5000
"""

from flask import Flask, request, jsonify, Response
from sys import stderr
from typing import Any
import pickle
import math
import numpy as np
import os

app = Flask(__name__)

BASE = os.path.dirname(__file__)
MODELO: Any = None
SCALER: Any = None


# La deshidrogenasa se eliminó: es redundante con CO₂ (ambas miden
# actividad microbiana general). Su peso (6%) se redistribuye a co2.
PESOS = {
    "co2": 0.31,
    "mo": 0.25,
    "ph": 0.10,
    "temp": 0.10,
    "enz_beta_glucosidasa": 0.06,
    "enz_fosfatasa": 0.06,
    "enz_arilsulfatasa": 0.06,
    "enz_ureasa": 0.06
}


def cargar_modelo() -> None:
    global MODELO, SCALER
    ruta_modelo = os.path.join(BASE, "../model/output/ibs_model.pkl")
    ruta_scaler = os.path.join(BASE, "../model/output/ibs_scaler.pkl")

    with open(ruta_modelo, "rb") as f:
        MODELO = pickle.load(f)
    with open(ruta_scaler, "rb") as f:
        SCALER = pickle.load(f)

    print("Modelo cargado correctamente.")


def _normalizar(v: float, mn: float, mx: float) -> float:
    return max(0.0, min(1.0, (v - mn) / (mx - mn)))


def formula_fallback(co2: float, mo: float, ph: float, temp: float,
                     beta_glucosidasa: float,
                     fosfatasa: float, arilsulfatasa: float, ureasa: float) -> float:
    co2_n = _normalizar(co2, 30, 600)
    mo_n = _normalizar(mo, 0.3, 6.0)
    ph_s = math.exp(-0.5 * ((ph - 6.5) / 1.2) ** 2)
    temp_s = math.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)

    beta_n = _normalizar(beta_glucosidasa, 0.0, 10.0)
    fosf_n = _normalizar(fosfatasa, 0.0, 10.0)
    aril_n = _normalizar(arilsulfatasa, 0.0, 10.0)
    urea_s = math.exp(-0.5 * ((ureasa - 5.0) / 2.5) ** 2)

    ibs = (
        co2_n * PESOS["co2"] +
        mo_n * PESOS["mo"] +
        ph_s * PESOS["ph"] +
        temp_s * PESOS["temp"] +
        beta_n * PESOS["enz_beta_glucosidasa"] +
        fosf_n * PESOS["enz_fosfatasa"] +
        aril_n * PESOS["enz_arilsulfatasa"] +
        urea_s * PESOS["enz_ureasa"]
    )
    return round(ibs * 100, 2)


def asignar_estado(ibs: float) -> str:
    if ibs <= 30: return "critico"
    if ibs <= 50: return "bajo"
    if ibs <= 70: return "medio"
    if ibs <= 85: return "bueno"
    return "excelente"


@app.route("/predecir", methods=["POST"])
def predecir() -> tuple[Response, int] | Response:
    datos = request.get_json()

    campos_requeridos = [
        "co2_mg_kg_dia", "mo_porcentaje", "ph", "temp_celsius",
        "enz_beta_glucosidasa", "enz_fosfatasa",
        "enz_arilsulfatasa", "enz_ureasa"
    ]
    for campo in campos_requeridos:
        if campo not in datos:
            return jsonify({"error": f"Falta el campo: {campo}"}), 400

    co2 = float(datos["co2_mg_kg_dia"])
    mo = float(datos["mo_porcentaje"])
    ph = float(datos["ph"])
    temp = float(datos["temp_celsius"])
    beta = float(datos["enz_beta_glucosidasa"])
    fosf = float(datos["enz_fosfatasa"])
    aril = float(datos["enz_arilsulfatasa"])
    urea = float(datos["enz_ureasa"])

    if MODELO and SCALER:
        entrada = np.array([[co2, mo, ph, temp, beta, fosf, aril, urea]])
        entrada_sc = SCALER.transform(entrada)
        ibs = round(float(MODELO.predict(entrada_sc)[0]), 2)
        ibs = max(0.0, min(100.0, ibs))
        fuente = "modelo_ml"
    else:
        ibs = formula_fallback(co2, mo, ph, temp, beta, fosf, aril, urea)
        fuente = "formula_fallback"

    estado = asignar_estado(ibs)

    return jsonify({
        "ibs_score": ibs,
        "estado": estado,
        "fuente": fuente,
        "input": {
            "co2_mg_kg_dia": co2,
            "mo_porcentaje": mo,
            "ph": ph,
            "temp_celsius": temp,
            "enz_beta_glucosidasa": beta,
            "enz_fosfatasa": fosf,
            "enz_arilsulfatasa": aril,
            "enz_ureasa": urea
        }
    })


@app.route("/health", methods=["GET"])
def health() -> Response:
    return jsonify({
        "status": "ok",
        "modelo_cargado": MODELO is not None
    })


if __name__ == "__main__":
    try:
        cargar_modelo()
    except Exception as e:
        print(f"Advertencia: no se pudo cargar el modelo ({e}). Usando fórmula fallback.", file=stderr)

    app.run(host="127.0.0.1", port=5000, debug=False)
