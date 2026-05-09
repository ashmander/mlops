from fastapi import FastAPI
from src.routers.prediction_router import router as prediction_router

app = FastAPI(
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"},
    swagger_ui_version="5.0.0"  # fuerza versión más reciente
)

app.include_router(prediction_router)
