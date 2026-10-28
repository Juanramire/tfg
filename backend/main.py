import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.configuracion import router as configuracion_router
from routes.features import router as features_router
from routes.productos import router as productos_router
from services.db import CatalogoNoDisponibleError

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


@app.exception_handler(CatalogoNoDisponibleError)
def catalogo_no_disponible_handler(request: Request, exc: CatalogoNoDisponibleError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(features_router)
app.include_router(productos_router)
app.include_router(configuracion_router)


@app.get("/")
def root():
    return {"mensaje": "¡El Backend del TFG está funcionando!"}
