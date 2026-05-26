# MLOps — Disease Prediction API

API REST para predecir diagnósticos médicos basados en síntomas del paciente, con historial de predicciones y frontend web integrado.

## Diagnósticos posibles

| | Diagnóstico |
|---|---|
| 🟢 | No enfermo |
| 🟡 | Enfermedad leve |
| 🔵 | Enfermedad aguda |
| 🟠 | Enfermedad crónica |
| 🔴 | Enfermedad terminal |

## Tecnologías

- **FastAPI** — API REST
- **Pydantic** — validación de esquemas
- **uv** — manejo de dependencias
- **Docker** — contenedorización
- **GitHub Actions** — CI/CD

## Estructura

```
.github/workflows/
├── workflow.yaml       # CI/CD pipeline (PR + merge a main)
└── test.yaml           # Reusable workflow de tests
frontend/
├── index.html
├── styles.css
└── app.js
src/
├── routers/
│   └── prediction_router.py
├── schemas/
│   ├── prediction_data_request.py
│   └── prediction_data_response.py
└── services/
    ├── prediction_engine.py
    └── prediction_history.py
tests/
├── test_prediction.py  # Tests unitarios
└── test_integration.py # Tests de integración FastAPI
main.py
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/healthy-checker/predict` | Realiza una predicción |
| `GET` | `/healthy-checker/statistics` | Estadísticas e historial |

## Ejecución local

```bash
uv sync
uv run uvicorn main:app --reload
```

## Ejecución con Docker

```bash
docker build -t mlops-app .
docker run -p 8000:8000 mlops-app
```

## Ejemplo rápido

```bash
curl -X POST http://localhost:8000/healthy-checker/predict \
  -H "Content-Type: application/json" \
  -d '{
    "fever": {"present": true, "severity": "severe", "duration_days": 3},
    "shortness_of_breath": {"present": true, "severity": "severe", "duration_days": 1}
  }'
```

## Tests

```bash
uv run pytest tests/
```

## CI/CD

El pipeline corre automáticamente en GitHub Actions:

- **Pull Request → main** — comenta inicio, corre tests, comenta resultado
- **Merge → main** — corre tests y publica imagen Docker en GitHub Packages (`ghcr.io`)

La documentación interactiva está disponible en `http://localhost:8000/docs`.