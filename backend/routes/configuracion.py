from fastapi import APIRouter, HTTPException

from models.schemas import PresupuestoRequest, PerfilRequest, ConsultaRequest
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


@router.post("/consulta")
def configurar_por_consulta(request: ConsultaRequest):
    """Interpret a natural language query and generate a PC configuration."""
    if not request.consulta.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    try:
        from services.gemini_service import interpretar_consulta

        interpretacion = interpretar_consulta(request.consulta)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    from services.configurador_service import PERFILES

    presupuestos_defecto = {
        "Gaming": 1200.0,
        "Edicion": 1500.0,
        "Programacion": 1000.0,
        "Ofimatica": 600.0,
    }
    perfil = interpretacion.get("perfil")
    selected = interpretacion.get("selected", [])
    deselected = interpretacion.get("deselected", [])
    presupuesto = interpretacion.get("presupuesto") or presupuestos_defecto.get(
        perfil, 1000.0
    )

    # If profile detected, merge its features
    if perfil and perfil in PERFILES:
        selected = list(set(selected + PERFILES[perfil]["selected"]))
        deselected = list(set(deselected + PERFILES[perfil]["deselected"]))

    # Remove from deselected any feature forced by the UVL model given the selected set.
    # This prevents Gemini from violating UVL constraints (e.g. Gaming => TarjetaGrafica,
    # AMD => AM4|AM5, Intel_Gama_Alta => Refrigeracion_Liquida, etc.).
    # Uses `selected` after the profile merge, so profile-implied features are included.
    if selected and deselected:
        from services.flamapy_service import flamapy_service

        forced_by_model = set(flamapy_service.propagate(selected, [])["forced"])
        deselected = [f for f in deselected if f not in forced_by_model]

    # Ensure minimum budget
    presupuesto = max(presupuesto, 300.0)

    resultado = generar_por_presupuesto(
        presupuesto=presupuesto,
        selected=selected,
        deselected=deselected,
    )

    # If the model was unsatisfiable (contradictory constraints from Gemini),
    # retry ignoring deselected so the user always gets a usable configuration.
    if not resultado["componentes"] and deselected:
        resultado = generar_por_presupuesto(
            presupuesto=presupuesto,
            selected=selected,
            deselected=[],
        )
        resultado["avisos"].insert(
            0,
            "Algunas restricciones indicadas eran incompatibles con el perfil y se han ignorado.",
        )

    resultado["perfil"] = perfil
    resultado["explicacion"] = interpretacion.get("explicacion", "")
    resultado["interpretacion"] = interpretacion

    return resultado


@router.get("/perfiles")
def listar_perfiles():
    """List available usage profiles with their descriptions."""
    from services.configurador_service import PERFILES

    return {nombre: config["descripcion"] for nombre, config in PERFILES.items()}
