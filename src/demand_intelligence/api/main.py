"""FastAPI entry point and web application shell."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import build_router

app = FastAPI(title="Demand Forecasting & Decision Intelligence API", version="0.1.0")
app.include_router(build_router())

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
