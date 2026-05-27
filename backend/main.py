import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.configuracion import router as configuracion_router
from routes.features import router as features_router
from routes.productos import router as productos_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = FastAPI(title="PC Configurador API", version="0.1.0")

_origins = ["http://localhost:5173", "http://localhost", "http://localhost:80"]
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(features_router)
app.include_router(productos_router)
app.include_router(configuracion_router)


@app.get("/")
def root():
    return {"mensaje": "¡El Backend del TFG está funcionando!"}
