from fastapi import APIRouter, HTTPException

from models.schemas import PresupuestoRequest, PerfilRequest, ConsultaRequest
from services.configurador_service import generar_por_presupuesto, generar_por_perfil

router = APIRouter(prefix="/api/configuracion", tags=["configuracion"])


@router.post("/presupuesto")
def configurar_por_presupuesto(request: PresupuestoRequest):
    """Genera una configuración completa de PC basada en un presupuesto.

    Distribuye el presupuesto entre categorías usando porcentajes optimizados
    y selecciona el mejor producto compatible para cada categoría.
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
    """Genera una configuración completa de PC basada en un perfil de uso.

    Perfiles disponibles: Gaming, Edicion, Programacion, Ofimatica.
    Acepta opcionalmente un presupuesto (usa valores por defecto si no se indica).
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
    """Interpreta una consulta en lenguaje natural y genera una configuración de PC."""
    if not request.consulta.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    try:
        from services.gemini_service import interpretar_consulta

        interpretacion = interpretar_consulta(request.consulta)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not interpretacion.get("entendida", True):
        raise HTTPException(
            status_code=422,
            detail=interpretacion.get(
                "explicacion",
                "No he podido entender tu consulta. Descríbe qué quieres hacer con tu PC "
                "(por ejemplo: 'PC para jugar a 1080p con 800€' o 'equipo para editar vídeo').",
            ),
        )

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

    # Si se detecta perfil, combinar sus features
    if perfil and perfil in PERFILES:
        selected = list(set(selected + PERFILES[perfil]["selected"]))
        deselected = list(set(deselected + PERFILES[perfil]["deselected"]))

    # Eliminar de deselected las features forzadas por el modelo UVL dado el conjunto seleccionado.
    # Evita que Gemini viole constraints UVL (ej. Gaming => TarjetaGrafica,
    # AMD => AM4|AM5, Intel_Gama_Alta => Refrigeracion_Liquida, etc.).
    # Usa `selected` tras la combinación con el perfil, para incluir las features implicadas por él.
    if selected and deselected:
        from services.flamapy_service import flamapy_service

        forced_by_model = set(flamapy_service.propagate(selected, [])["forced"])
        deselected = [f for f in deselected if f not in forced_by_model]

    # Garantizar presupuesto mínimo
    presupuesto = max(presupuesto, 300.0)

    resultado = generar_por_presupuesto(
        presupuesto=presupuesto,
        selected=selected,
        deselected=deselected,
    )

    # Si el modelo era insatisfacible (constraints contradictorias de Gemini),
    # reintentar ignorando deselected para que el usuario siempre reciba una configuración válida.
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
    """Lista los perfiles de uso disponibles con sus descripciones."""
    from services.configurador_service import PERFILES

    return {nombre: config["descripcion"] for nombre, config in PERFILES.items()}
