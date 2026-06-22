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
IBS = (CO2_norm × 0.40) + (MO_norm × 0.30) + (pH_score × 0.20) + (Temp_score × 0.10)
```

### Parámetros y pesos

| Parámetro | Medición | Peso | Método de normalización |
|---|---|---|---|
| CO₂ respiración basal | mg CO₂ / kg suelo / día | 40% | Lineal — rango 30–600 |
| Materia Orgánica | % | 30% | Lineal — rango 0.3–6.0 |
| pH del suelo | Escala 0–14 | 20% | Gaussiana — pico en 6.5 |
| Temperatura | °C a 10cm | 10% | Gaussiana — pico en 22°C |

### Normalización

**CO₂ y MO — normalización lineal:**
```python
valor_norm = (medicion - rango_min) / (rango_max - rango_min)
```

**pH y Temperatura — curva gaussiana:**
```python
# pH: óptimo biológico en 6.5
ph_score = exp(-0.5 * ((ph - 6.5) / 1.2) ** 2)

# Temperatura: óptimo en 22°C
temp_score = exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)
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
cd python/model
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
  -d '{"co2_mg_kg_dia": 280, "mo_porcentaje": 2.4, "ph": 6.5, "temp_celsius": 21}'
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

def ibs_calcular(co2, mo, ph, temp):
    co2_norm   = max(0, min(1, (co2  - 30)  / (600  - 30)))
    mo_norm    = max(0, min(1, (mo   - 0.3) / (6.0  - 0.3)))
    ph_score   = math.exp(-0.5 * ((ph   - 6.5) / 1.2) ** 2)
    temp_score = math.exp(-0.5 * ((temp - 22.0) / 8.0) ** 2)
    return round(((co2_norm * 0.40) + (mo_norm * 0.30) + (ph_score * 0.20) + (temp_score * 0.10)) * 100, 2)

print(ibs_calcular(280, 2.4, 6.5, 21))  # → ~63.4
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
