from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.routers.prediction_router import router as prediction_router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"},
    swagger_ui_version="5.0.0"  # fuerza versión más reciente
)

app.include_router(prediction_router)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")
