# MLOps - Disease Prediction API

API REST para predecir diagnósticos médicos basados en síntomas del paciente.
Se creo la estructura del pipeline a implementar en un futuro. Se encuentra en la raiz del proyecto
y se llama pipeline_mlops_diagrama.md

## Descripción

Recibe un conjunto de síntomas pre-establecidos del paciente. De cada síntoma se evalúa:
- **Presencia** — si el síntoma está presente o no
- **Severidad** — leve, moderada o severa
- **Duración** — cantidad de días con el síntoma

Y retorna uno de los siguientes diagnósticos:
- 🟢 Healthy
- 🟡 Mild Disease
- 🔴 Acute Disease
- 🟠 Chronic Disease

## Tecnologías

- **FastAPI** — framework para la API REST
- **Pydantic** — validación de esquemas
- **uv** — manejador de dependencias y entornos
- **Docker** — contenedorización

## Estructura del proyecto

```
src/
├── routers/
│   └── prediction_router.py
├── schemas/
│   └── prediction_data_request.py
└── services/
    └── prediction_engine.py
main.py
pyproject.toml
Dockerfile
```

## Ejecución con Docker

1. Ubicarse en la carpeta raíz del proyecto
2. Construir la imagen:
```bash
docker build -t mlops-app .
```
3. Correr el contenedor:
```bash
docker run -p 8000:8000 mlops-app
```
4. Abrir Swagger en el navegador:
```
http://localhost:8000/docs
```
## Ejecución local

```bash
uv sync
uv run uvicorn main:app --reload
```

## Uso

El Swagger en `/docs` contiene 4 ejemplos listos para probar cada diagnóstico posible.
También se puede probar con curl:

```bash
curl -X POST http://localhost:8000/healthy-checker/predict \
  -H "Content-Type: application/json" \
  -d '{
    "fever": {"present": true, "severity": "severe", "duration_days": 3},
    "shortness_of_breath": {"present": true, "severity": "severe", "duration_days": 1}
  }'
```