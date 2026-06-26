"""
IBS - Índice de Bioactividad del Suelo
Microservicio Flask — Puerto 5000
"""

from flask import Flask, request, jsonify, Response
import pickle
import math
import numpy as np
import os

app = Flask(__name__)

BASE = os.path.dirname(__file__)
MODELO = None
SCALER = None

def cargar_modelo() -> None:
    global MODELO, SCALER
    ruta_modelo = os.path.join(BASE, "../model/output/ibs_model.pkl")
    ruta_scaler = os.path.join(BASE, "../model/output/ibs_scaler.pkl")

    with open(ruta_modelo, "rb") as f:
        MODELO = pickle.load(f)
    with open(ruta_scaler, "rb") as f:
        SCALER = pickle.load(f)

    print("Modelo cargado correctamente.")


def _normalizar(v, mn, mx) -> float:
    return max(0.0, min(1.0, (v - mn) / (mx - mn)))


def formula_fallback(co2: float, mo: float, ph: float, temp: float) -> float:
    co2_n = _normalizar(co2, 30, 600)
    mo_n = _normalizar(mo, 0.3, 6.0)
    ph_s = math.exp(-0.5 * ((ph - 6.5) / 1.2) ** 2)
    temp_s = math.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)

    return round((co2_n * 0.40 + mo_n * 0.30 + ph_s * 0.20 + temp_s * 0.10) * 100, 2)


def asignar_estado(ibs: float) -> str:
    if ibs <= 30: return "critico"
    if ibs <= 50: return "bajo"
    if ibs <= 70: return "medio"
    if ibs <= 85: return "bueno"
    return "excelente"


@app.route("/predecir", methods=["POST"])
def predecir() -> tuple[Response, int] | Response:
    datos = request.get_json()

    campos_requeridos = ["co2_mg_kg_dia", "mo_porcentaje", "ph", "temp_celsius"]
    for campo in campos_requeridos:
        if campo not in datos:
            return jsonify({"error": f"Falta el campo: {campo}"}), 400

    co2 = float(datos["co2_mg_kg_dia"])
    mo = float(datos["mo_porcentaje"])
    ph = float(datos["ph"])
    temp = float(datos["temp_celsius"])

    if MODELO and SCALER:
        entrada = np.array([[co2, mo, ph, temp]])
        entrada_sc = SCALER.transform(entrada)
        ibs = round(float(MODELO.predict(entrada_sc)[0]), 2)
        ibs = max(0.0, min(100.0, ibs))
        fuente = "modelo_ml"
    else:
        ibs = formula_fallback(co2, mo, ph, temp)
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
            "temp_celsius": temp
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
        print(f"Advertencia: no se pudo cargar el modelo ({e}). Usando fórmula fallback.")

    app.run(host="127.0.0.1", port=5000, debug=False)
