"""Motor de configuración inteligente.

Combina FlamaPy (propagación de constraints) con el catálogo de productos
para generar configuraciones completas basadas en presupuesto y/o perfil de uso.
"""

from services.flamapy_service import flamapy_service
from services.db import get_productos

# Porcentajes de reparto de presupuesto por categoría.
# Heurística de diseño coherente con las guías de montaje de PC (la GPU
# concentra el mayor peso en equipos gaming). Se ajustan dinámicamente
# según si hay GPU o no.
REPARTO_CON_GPU = {
    "Procesador": 0.20,
    "PlacaBase": 0.10,
    "MemoriaRAM": 0.08,
    "TarjetaGrafica": 0.35,
    "Almacenamiento": 0.07,
    "FuenteAlimentacion": 0.06,
    "Chasis": 0.07,
    "Refrigeracion": 0.07,
}

REPARTO_SIN_GPU = {
    "Procesador": 0.30,
    "PlacaBase": 0.15,
    "MemoriaRAM": 0.15,
    "Almacenamiento": 0.12,
    "FuenteAlimentacion": 0.10,
    "Chasis": 0.10,
    "Refrigeracion": 0.08,
}

# Features mínimas por perfil de uso
PERFILES = {
    "Gaming": {
        "selected": ["Gaming"],
        "deselected": [],
        "descripcion": "PC optimizado para juegos",
    },
    "Edicion": {
        "selected": ["Edicion"],
        "deselected": [],
        "descripcion": "PC para edición de vídeo/foto y renderizado",
    },
    "Programacion": {
        "selected": ["Programacion"],
        "deselected": ["TarjetaGrafica"],
        "descripcion": "PC para desarrollo de software",
    },
    "Ofimatica": {
        "selected": ["Ofimatica"],
        "deselected": ["TarjetaGrafica"],
        "descripcion": "PC básico para ofimática y navegación",
    },
}


def _elegir_producto(
    categoria: str,
    features_validas: set[str],
    presupuesto_categoria: float,
) -> dict | None:
    """Elige el mejor producto de una categoría dentro del presupuesto.

    Estrategia: de los productos compatibles con las features válidas,
    elige el más caro que quepa en el presupuesto (máximo rendimiento).
    Si ninguno cabe, elige el más barato disponible.
    """
    todos = get_productos(categoria=categoria)

    # Filtrar por compatibilidad con features válidas
    compatibles = []
    for p in todos:
        product_features = set(p["features"])
        if product_features.issubset(features_validas):
            compatibles.append(p)

    if not compatibles:
        return None

    # Ordenar por precio descendente
    compatibles.sort(key=lambda p: p["precio"], reverse=True)

    # El más caro que quepa en el presupuesto
    for p in compatibles:
        if p["precio"] <= presupuesto_categoria:
            return p

    # Si nada cabe, devolver el más barato
    return compatibles[-1]


def _seleccionar_almacenamiento(
    features_validas: set[str],
    presupuesto_categoria: float,
) -> list[dict]:
    """Selecciona almacenamiento. Prioriza SSD NVMe, añade HDD si sobra presupuesto."""
    todos = get_productos(categoria="Almacenamiento")
    compatibles = [p for p in todos if set(p["features"]).issubset(features_validas)]

    if not compatibles:
        return []

    # Priorizar NVMe > SATA > HDD
    nvme = [p for p in compatibles if "SSD_NVMe" in p["features"]]
    sata = [p for p in compatibles if "SSD_SATA" in p["features"]]
    hdd = [p for p in compatibles if "Disco_HDD" in p["features"]]

    resultado = []
    restante = presupuesto_categoria

    # Primero un SSD (NVMe preferido)
    for grupo in [nvme, sata]:
        grupo.sort(key=lambda p: p["precio"], reverse=True)
        for p in grupo:
            if p["precio"] <= restante:
                resultado.append(p)
                restante -= p["precio"]
                break
        if resultado:
            break

    if not resultado and compatibles:
        mas_barato = min(compatibles, key=lambda p: p["precio"])
        resultado.append(mas_barato)
        restante -= mas_barato["precio"]

    # Si sobra presupuesto, añadir HDD
    if restante > 0 and hdd:
        hdd.sort(key=lambda p: p["precio"])
        for disco in hdd:
            if disco["precio"] <= restante:
                resultado.append(disco)
                break

    return resultado


def generar_por_presupuesto(
    presupuesto: float,
    selected: list[str] | None = None,
    deselected: list[str] | None = None,
) -> dict:
    """Genera una configuración completa basada en un presupuesto.

    1. Propaga constraints con FlamaPy
    2. Reparte el presupuesto por categoría según porcentajes
    3. Elige el mejor producto compatible para cada categoría
    """
    selected = selected or []
    deselected = deselected or []

    # Propagar constraints
    prop = flamapy_service.propagate(selected, deselected)
    features_validas = set(prop["forced"] + prop["selectable"])

    # Determinar si incluye GPU
    incluye_gpu = (
        "TarjetaGrafica" in features_validas
        and "TarjetaGrafica" not in prop.get("excluded", [])
    )
    reparto = REPARTO_CON_GPU if incluye_gpu else REPARTO_SIN_GPU

    # Si se piden SSD NVMe + HDD simultáneamente, ampliar presupuesto de almacenamiento
    if "SSD_NVMe" in features_validas and "Disco_HDD" in features_validas:
        reparto = dict(reparto)
        if incluye_gpu:
            reparto["Almacenamiento"] = 0.14
            reparto["TarjetaGrafica"] -= 0.07
        else:
            reparto["Almacenamiento"] = 0.20
            reparto["Procesador"] -= 0.08

    # Seleccionar productos por categoría
    componentes = []
    precio_total = 0.0
    avisos = []

    for categoria, porcentaje in reparto.items():
        presupuesto_cat = presupuesto * porcentaje

        if categoria == "Almacenamiento":
            productos = _seleccionar_almacenamiento(features_validas, presupuesto_cat)
            for p in productos:
                componentes.append({"categoria": categoria, "producto": p})
                precio_total += p["precio"]
            if not productos:
                avisos.append("No se encontró almacenamiento compatible")
            continue

        if categoria == "TarjetaGrafica" and not incluye_gpu:
            continue

        producto = _elegir_producto(categoria, features_validas, presupuesto_cat)
        if producto:
            componentes.append({"categoria": categoria, "producto": producto})
            precio_total += producto["precio"]

            # Actualizar features válidas con la selección concreta
            # para que las siguientes categorías sean coherentes
            nuevas_selected = list(set(selected) | set(producto["features"]))
            prop = flamapy_service.propagate(nuevas_selected, deselected)
            features_validas = set(prop["forced"] + prop["selectable"])
            selected = nuevas_selected
        else:
            avisos.append(f"No se encontró {categoria} compatible")

    if precio_total > presupuesto:
        avisos.append(
            f"El coste mínimo de esta configuración ({precio_total:.2f}€) "
            f"supera el presupuesto en {precio_total - presupuesto:.2f}€. "
            f"Considera aumentar el presupuesto o relajar las restricciones."
        )

    return {
        "presupuesto": presupuesto,
        "precio_total": round(precio_total, 2),
        "ahorro": max(0, round(presupuesto - precio_total, 2)),
        "reparto": {k: f"{v * 100:.0f}%" for k, v in reparto.items()},
        "componentes": componentes,
        "avisos": avisos,
        "propagacion": prop,
    }


def generar_por_perfil(
    perfil: str,
    presupuesto: float | None = None,
) -> dict:
    """Genera una configuración basada en un perfil de uso.

    1. Obtiene las features del perfil
    2. Si hay presupuesto, genera por presupuesto con esas features
    3. Si no, genera con un presupuesto por defecto según el perfil
    """
    if perfil not in PERFILES:
        return {
            "error": f"Perfil desconocido: {perfil}. Opciones: {list(PERFILES.keys())}"
        }

    config_perfil = PERFILES[perfil]

    # Presupuestos por defecto según perfil
    presupuestos_defecto = {
        "Gaming": 1200.0,
        "Edicion": 1500.0,
        "Programacion": 1000.0,
        "Ofimatica": 600.0,
    }

    presupuesto_final = presupuesto or presupuestos_defecto[perfil]

    resultado = generar_por_presupuesto(
        presupuesto=presupuesto_final,
        selected=config_perfil["selected"],
        deselected=config_perfil["deselected"],
    )
    resultado["perfil"] = perfil
    resultado["descripcion"] = config_perfil["descripcion"]

    return resultado
