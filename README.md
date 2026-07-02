# 🌱 IBS — Índice de Bioactividad del Suelo

> Sistema abierto de análisis y scoring de salud biológica del suelo.
> Fórmula ponderada + modelo ML + motor de recomendaciones agronómicas.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![PHP](https://img.shields.io/badge/PHP-8.1+-777BB4.svg)](https://php.net)
[![Status](https://img.shields.io/badge/status-MVP%20activo-brightgreen)]()

---

## ¿Qué es el IBS?

El **Índice de Bioactividad del Suelo** es una métrica compuesta (0–100) que evalúa la salud biológica del suelo a partir de parámetros medibles en laboratorio.

A diferencia de análisis convencionales que miden nutrientes de forma aislada, el IBS integra **actividad microbiana, materia orgánica, pH y temperatura** en un único valor accionable, con un motor de recomendaciones de manejo asociado.

---

## Fórmula base

```
IBS = (CO2_norm × 0.35) + (MO_norm × 0.25) + (pH_score × 0.15) + (Temp_score × 0.10) +
      (Enz_Desh_norm × 0.0375) + (Enz_Beta_norm × 0.0375) + (Enz_Fosf_norm × 0.0375) + 
      (Enz_Aril_norm × 0.0375) + (Enz_Urea_score × 0.0375)
```

> **Nota:** Los pesos están desacoplados de la ecuación y se pueden ajustar mediante configuración.

### Parámetros y pesos base

| Parámetro | Medición | Peso | Método de normalización |
|---|---|---|---|
| CO₂ respiración basal | mg CO₂ / kg suelo / día | 35% | Lineal — rango 30–600 |
| Materia Orgánica | % | 25% | Lineal — rango 0.3–6.0 |
| Deshidrogenasa | U / g | 3.75% | Lineal — rango 0.0–10.0 |
| Beta-glucosidasa | U / g | 3.75% | Lineal — rango 0.0–10.0 |
| Fosfatasa | U / g | 3.75% | Lineal — rango 0.0–10.0 |
| Arilsulfatasa | U / g | 3.75% | Lineal — rango 0.0–10.0 |
| Ureasa | U / g | 3.75% | Gaussiana — pico en 5.0 (penaliza exceso) |
| pH del suelo | Escala 0–14 | 15% | Gaussiana — pico en 6.5 |
| Temperatura | °C a 10cm | 10% | Gaussiana — pico en 22°C |

### Normalización

**CO₂, MO y mayoría de Enzimas — normalización lineal:**
```python
valor_norm = (medicion - rango_min) / (rango_max - rango_min)
```

**pH, Temperatura y Ureasa — curva gaussiana:**
```python
# pH: óptimo biológico en 6.5
ph_score = exp(-0.5 * ((ph - 6.5) / 1.2) ** 2)

# Temperatura: óptimo en 22°C
temp_score = exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)

# Ureasa: óptimo en 5.0, excesos penalizan (riesgo de lixiviación)
ureasa_score = exp(-0.5 * ((ureasa - 5.0) / 2.5) ** 2)
```

Todos los valores se clampean a [0, 1] antes de aplicar los pesos. El resultado se multiplica por 100.

---

## Tabla de decisión

| IBS | Estado | Color | Acción recomendada |
|---|---|---|---|
| 0 – 30 | Crítico | 🔴 | Enmienda orgánica urgente, evitar labranza |
| 31 – 50 | Bajo | 🟠 | Compost + rotación de cultivos |
| 51 – 70 | Moderado | 🟡 | Bioestimulante liviano, monitoreo |
| 71 – 85 | Bueno | 🟢 | Mantener manejo actual |
| 86 – 100 | Excelente | 🔵 | No intervenir, documentar como referencia |

---

## Modelo ML

Se entrena un **Random Forest Regressor** sobre el dataset sintético generado con la fórmula base más ruido gaussiano (σ = 3 puntos IBS) para simular variabilidad real de laboratorio.

```
Arquitectura : RandomForestRegressor
n_estimators : 200
max_depth    : 12
features     : [co2_mg_kg_dia, mo_porcentaje, ph, temp_celsius]
target       : ibs_score (0–100)
dataset      : 3.000 registros sintéticos + ruido gaussiano
```

**Métricas típicas sobre test set (20%):**

| Métrica | Valor esperado |
|---|---|
| MAE | < 3.5 puntos IBS |
| R² | > 0.97 |

---

## Stack

| Capa | Tecnología | Rol |
|---|---|---|
| ML / Dataset | Python 3.11 + scikit-learn | Generación, entrenamiento, inferencia |
| Microservicio | Flask | API interna HTTP en localhost:5000 |
| Backend | PHP 8.1 | Lógica de negocio, rutas, vistas |
| Base de datos | MySQL 8 | Muestras, historial, recomendaciones |
| Frontend | JavaScript + Chart.js | Gráficos, interactividad |

---

## Estructura del repo

```
ibs/
├── v8/
│   ├── model/
│   │   ├── generate_dataset.py   ← genera dataset sintético
│   │   ├── train_model.py        ← entrena y exporta el modelo
│   │   └── output/               ← ibs_model.pkl + ibs_scaler.pkl
│   ├── api/
│   │   └── app.py                ← microservicio Flask
│   └── requirements.txt
├── dashboard/
│   ├── helpers/
│   │   └── ibs_service.php       ← cálculo + fallback PHP
│   ├── phpfiles/
│   │   └── home.php              ← interfaz demo
│   └── assets/
├── sql/
│   └── schema.sql
├── README.md
└── .gitignore
```

---

## Instalación local

```bash
# 1. Clonar
git clone https://github.com/stndcx/ibs.git
cd ibs

# 2. Base de datos
mysql -u root -p < sql/schema.sql

# 3. Dataset y modelo
cd v8/model
pip install -r ../requirements.txt --user
python generate_dataset.py
python train_model.py

# 4. Microservicio
cd ../api
python app.py
# → escucha en http://127.0.0.1:5000

# 5. PHP — apuntar servidor web a dashboard/
```

### Verificar que el modelo responde

```bash
curl -X POST http://localhost:5000/predecir \
  -H "Content-Type: application/json" \
  -d '{"co2_mg_kg_dia": 280, "mo_porcentaje": 2.4, "ph": 6.5, "temp_celsius": 21, "enz_deshidrogenasa": 7.5, "enz_beta_glucosidasa": 6.0, "enz_fosfatasa": 5.5, "enz_arilsulfatasa": 6.8, "enz_ureasa": 4.5}'
```

Respuesta esperada:

```json
{
  "ibs_score": 63.4,
  "estado": "medio",
  "fuente": "modelo_ml"
}
```

---

## Ejemplo de cálculo manual

```python
import math

PESOS = {"co2": 0.25, "mo": 0.25, "ph": 0.10, "temp": 0.10, "enz_deshidrogenasa": 0.06, "enz_beta_glucosidasa": 0.06, "enz_fosfatasa": 0.06, "enz_arilsulfatasa": 0.06, "enz_ureasa": 0.06}

def ibs_calcular(co2, mo, ph, temp, desh, beta, fosf, aril, urea):
    co2_n   = max(0, min(1, (co2  - 30)  / (600  - 30)))
    mo_n    = max(0, min(1, (mo   - 0.3) / (6.0  - 0.3)))
    ph_s   = math.exp(-0.5 * ((ph   - 6.5) / 1.2) ** 2)
    temp_s = math.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)
    
    desh_n = max(0, min(1, (desh - 0.0) / (10.0 - 0.0)))
    beta_n = max(0, min(1, (beta - 0.0) / (10.0 - 0.0)))
    fosf_n = max(0, min(1, (fosf - 0.0) / (10.0 - 0.0)))
    aril_n = max(0, min(1, (aril - 0.0) / (10.0 - 0.0)))
    urea_s = math.exp(-0.5 * ((urea - 5.0) / 2.5) ** 2)
    
    score = (
        co2_n * PESOS["co2"] + mo_n * PESOS["mo"] + ph_s * PESOS["ph"] + temp_s * PESOS["temp"] +
        desh_n * PESOS["enz_deshidrogenasa"] + beta_n * PESOS["enz_beta_glucosidasa"] +
        fosf_n * PESOS["enz_fosfatasa"] + aril_n * PESOS["enz_arilsulfatasa"] + urea_s * PESOS["enz_ureasa"]
    )
    return round(score * 100, 2)

print(ibs_calcular(280, 2.4, 6.5, 21, 7.5, 6.0, 5.5, 6.8, 4.5))  # → ~68.1
```

---

## Dataset sintético

Rangos de referencia (región pampeana húmeda — ajustables por zona):

```python
RANGOS = {
    "co2_mg_kg_dia": {"min": 30,  "max": 600},
    "mo_porcentaje":  {"min": 0.3, "max": 6.0},
    "ph":             {"min": 4.5, "max": 9.0},
    "temp_celsius":   {"min": 5.0, "max": 40.0},
    "enz_deshidrogenasa": {"min": 0.0, "max": 10.0},
    "enz_beta_glucosidasa": {"min": 0.0, "max": 10.0},
    "enz_fosfatasa": {"min": 0.0, "max": 10.0},
    "enz_arilsulfatasa": {"min": 0.0, "max": 10.0},
    "enz_ureasa": {"min": 0.0, "max": 10.0},
}
```

Pull requests con rangos validados para otras regiones son bienvenidos.

---

## Hoja de ruta

[#15](https://github.com/stndcx/ibs/issues/15)

---

## Contribuir

Contribuciones más valiosas ahora:

- **Datos reales de campo** con parámetros medidos y diagnóstico agronómico validado
- **Revisión de pesos** para zonas áridas, tropicales o volcánicas
- **Parámetros adicionales** con respaldo bibliográfico
- **Traducciones** del README (inglés, portugués, chino)

Abrí un issue antes de un PR para discutir el cambio.

---

## Licencia

MIT — Libre para uso académico, comercial y derivados con atribución.

---

## Web y contacto

**Web:** [stndcx.github.io/ibs](https://stndcx.github.io/ibs)  
Para integraciones o consultas técnicas, contactar desde la web.
