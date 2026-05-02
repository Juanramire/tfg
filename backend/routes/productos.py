from fastapi import APIRouter, Query

from models.producto import Producto
from services.db import get_productos

router = APIRouter(prefix="/api/productos", tags=["productos"])


@router.get("/", response_model=dict[str, int | list[Producto]])
def listar_productos(
    categoria: str | None = Query(
        None,
        description="Filtrar por categoría: Procesador, PlacaBase, MemoriaRAM, etc.",
    ),
    features: str | None = Query(
        None, description="Features del modelo separadas por coma, ej: 'AMD,AM5,DDR5'"
    ),
):
    """List products, optionally filtered by category and/or feature model features."""
    feature_list = [f.strip() for f in features.split(",")] if features else None
    productos = get_productos(categoria=categoria, features=feature_list)
    return {"total": len(productos), "productos": productos}


@router.get("/categorias")
def listar_categorias():
    """List all available product categories."""
    productos = get_productos()
    categorias = sorted({p["categoria"] for p in productos})
    return {"categorias": categorias}
