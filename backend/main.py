from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.features import router as features_router
from routes.productos import router as productos_router
from routes.configuracion import router as configuracion_router

app = FastAPI(title="PC Configurador API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost", "http://localhost:80"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(features_router)
app.include_router(productos_router)
app.include_router(configuracion_router)


@app.get("/")
def root():
    return {"mensaje": "¡El Backend del TFG está funcionando!"}
