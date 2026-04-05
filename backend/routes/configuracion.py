from fastapi import APIRouter, HTTPException

from models.schemas import PresupuestoRequest, PerfilRequest
from services.configurador_service import generar_por_presupuesto, generar_por_perfil

router = APIRouter(prefix="/api/configuracion", tags=["configuracion"])


@router.post("/presupuesto")
def configurar_por_presupuesto(request: PresupuestoRequest):
    """Generate a complete PC configuration based on a budget.

    Distributes the budget across categories using optimized percentages
    and selects the best compatible product for each category.
    """
    if request.presupuesto < 300:
        raise HTTPException(
            status_code=400,
            detail="El presupuesto mínimo es 300€",
        )
    return generar_por_presupuesto(
        presupuesto=request.presupuesto,
        selected=request.selected,
        deselected=request.deselected,
    )


@router.post("/perfil")
def configurar_por_perfil(request: PerfilRequest):
    """Generate a complete PC configuration based on a usage profile.

    Supported profiles: Gaming, Edicion, Programacion, Ofimatica.
    Optionally accepts a budget (uses sensible defaults if not provided).
    """
    resultado = generar_por_perfil(
        perfil=request.perfil,
        presupuesto=request.presupuesto,
    )
    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado


@router.get("/perfiles")
def listar_perfiles():
    """List available usage profiles with their descriptions."""
    from services.configurador_service import PERFILES

    return {nombre: config["descripcion"] for nombre, config in PERFILES.items()}
