"""
Scraper de Coolmod + clasificación con Gemini
Genera data/catalogo_real.json listo para importar a MongoDB

Uso:
  python scraper_coolmod.py              # scraping completo
  python scraper_coolmod.py --solo-cat Procesador  # solo una categoría
  python scraper_coolmod.py --max-paginas 1        # 1 página por categoría (~25 productos c/u)
"""

import argparse
import json
import logging
import os
import sys
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CATEGORIAS = {
    "Procesador": "https://www.coolmod.com/componentes-pc-procesadores/",
    "PlacaBase": "https://www.coolmod.com/componentes-pc-placas-base/",
    "MemoriaRAM": "https://www.coolmod.com/componentes-pc-memorias-ram/",
    "TarjetaGrafica": "https://www.coolmod.com/tarjetas-graficas/",
    "Almacenamiento": "https://www.coolmod.com/componentes-pc-discos-duros/",
    "FuenteAlimentacion": "https://www.coolmod.com/componentes-pc-fuentes-alimentacion/",
    "Chasis": "https://www.coolmod.com/componentes-pc-torres-cajas/",
    "Refrigeracion": "https://www.coolmod.com/componentes-pc-disipadores-ventiladores/",
}

FEATURES_POR_CATEGORIA = {
    "Procesador": [
        "Intel",
        "AMD",
        "Intel_Gama_Baja",
        "Intel_Gama_Media",
        "Intel_Gama_Alta",
        "AMD_Gama_Baja",
        "AMD_Gama_Media",
        "AMD_Gama_Alta",
        "LGA1700",
        "LGA1851",
        "AM4",
        "AM5",
    ],
    "PlacaBase": [
        "LGA1700",
        "LGA1851",
        "AM4",
        "AM5",
        "DDR4",
        "DDR5",
        "Placa_ATX",
        "Placa_MicroATX",
        "Placa_MiniITX",
    ],
    "MemoriaRAM": ["DDR4", "DDR5", "RAM_8GB", "RAM_16GB", "RAM_32GB", "RAM_64GB"],
    "TarjetaGrafica": ["GPU_Gama_Baja", "GPU_Gama_Media", "GPU_Gama_Alta"],
    "Almacenamiento": ["SSD_NVMe", "SSD_SATA", "Disco_HDD"],
    "FuenteAlimentacion": ["PSU_500W", "PSU_650W", "PSU_750W", "PSU_850W"],
    "Chasis": ["Caja_ATX", "Caja_MicroATX", "Caja_MiniITX"],
    "Refrigeracion": ["Refrigeracion_Aire", "Refrigeracion_Liquida"],
}

SPECS_FORMATO = {
    "Procesador": '{"nucleos": int, "hilos": int, "frecuencia_base": "X.X GHz", "frecuencia_boost": "X.X GHz", "tdp": int}',
    "PlacaBase": "{}",
    "MemoriaRAM": '{"velocidad": "XXXX MHz", "modulos": "NxXGB"}',
    "TarjetaGrafica": '{"vram": "XX GB GDDRx", "tdp": int}',
    "Almacenamiento": '{"capacidad": "X TB o X GB", "lectura": "XXXX MB/s"}  (lectura solo si es SSD)',
    "FuenteAlimentacion": '{"certificacion": "80 PLUS Gold"}  (o el certificado que corresponda, {} si no tiene)',
    "Chasis": "{}",
    "Refrigeracion": '{"tipo_radiador": "120mm"}  (solo si es líquida; si es aire, {})',
}

DELAY_REQUESTS = 0.6  # segundos entre peticiones HTTP
DELAY_GEMINI = 0.5  # segundos entre lotes Gemini
LOTE_GEMINI = 5  # productos por llamada a Gemini

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


def get_soup(url: str, retries: int = 3) -> BeautifulSoup | None:
    for intento in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
            logger.warning(f"HTTP {r.status_code} en {url}")
        except Exception as e:
            logger.warning(f"Error ({intento+1}/{retries}) en {url}: {e}")
            time.sleep(2)
    return None


def scrape_listing(url: str) -> list[dict]:
    """Extrae nombre, precio y URL de detalle de una página de listing."""
    soup = get_soup(url)
    if not soup:
        return []
    productos = []
    for a in soup.find_all("a", attrs={"data-itemname": True}):
        nombre = a.get("data-itemname", "").strip()
        precio_str = a.get("data-itemprice", "0").replace(",", ".")
        href = a.get("href", "")
        try:
            precio = float(precio_str)
        except ValueError:
            precio = 0.0
        if nombre and precio > 0:
            productos.append(
                {
                    "nombre": nombre,
                    "precio": precio,
                    "url": ("https://www.coolmod.com" + href)
                    if href.startswith("/")
                    else href,
                }
            )
    return productos


def scrape_detalle(url: str) -> dict:
    """Extrae specs en bruto (clave: valor) de la página de detalle."""
    soup = get_soup(url)
    if not soup:
        return {}
    specs = {}
    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if ":" in txt and len(txt) < 250:
            clave, _, valor = txt.partition(":")
            clave, valor = clave.strip(), valor.strip()
            if clave and valor:
                specs[clave] = valor
    return specs


def scrape_categoria(categoria: str, base_url: str, max_paginas: int) -> list[dict]:
    """Scraping completo de una categoría: listing + detalle."""
    logger.info(f"\n{'='*55}")
    logger.info(f"  {categoria}  ({base_url})")
    logger.info(f"{'='*55}")

    # 1. Listing pages
    todos_raw = []
    for pagina in range(1, max_paginas + 1):
        url = base_url if pagina == 1 else f"{base_url}?pagina={pagina}"
        prods = scrape_listing(url)
        if not prods:
            logger.info(f"  Página {pagina}: sin productos → fin")
            break
        todos_raw.extend(prods)
        logger.info(
            f"  Página {pagina}: {len(prods)} productos (acum. {len(todos_raw)})"
        )
        time.sleep(DELAY_REQUESTS)

    if not todos_raw:
        return []

    # 2. Detalle de cada producto
    for prod in todos_raw:
        logger.info(f"    Detalle: {prod['nombre'][:60]}")
        prod["specs_raw"] = scrape_detalle(prod["url"])
        time.sleep(DELAY_REQUESTS)

    return todos_raw


# ---------------------------------------------------------------------------
# Clasificación con Gemini
# ---------------------------------------------------------------------------


def construir_prompt_lote(categoria: str, productos: list[dict]) -> str:
    features_validas = FEATURES_POR_CATEGORIA.get(categoria, [])
    specs_fmt = SPECS_FORMATO.get(categoria, "{}")

    items_txt = ""
    for i, p in enumerate(productos):
        items_txt += f"""
Producto {i+1}:
  nombre: {p['nombre']}
  precio: {p['precio']}€
  specs_brutos: {json.dumps(p.get('specs_raw', {}), ensure_ascii=False)}
"""

    return f"""Eres un experto en hardware de PC de sobremesa. Clasifica estos {len(productos)} productos de la categoría "{categoria}".

Features válidas para "{categoria}": {features_validas}

Reglas de clasificación:
- Procesador: features = [Intel/AMD] + [gama] + [socket]. Gama baja ≤150€, media 150-400€, alta >400€.
- PlacaBase: features = [socket AM4/AM5/LGA1700/LGA1851] + [DDR4/DDR5] + [Placa_ATX/Placa_MicroATX/Placa_MiniITX].
- MemoriaRAM: features = [DDR4/DDR5] + [RAM_8GB/16GB/32GB/64GB según GB totales]. 2x16GB = RAM_32GB.
- TarjetaGrafica: features = [gama]. Gama baja <400€, media 400-800€, alta >800€.
- Almacenamiento: SSD_NVMe si es M.2 PCIe/NVMe, SSD_SATA si es 2.5" SATA, Disco_HDD si es mecánico.
- FuenteAlimentacion: PSU_Xw según potencia nominal (elige el más cercano por debajo: 500/650/750/850).
- Chasis: Caja_ATX/Caja_MicroATX/Caja_MiniITX según factor de forma compatible.
- Refrigeracion: Refrigeracion_Aire para disipadores de torre/top-flow, Refrigeracion_Liquida para AIO/custom loop.
- incluir=false si: es para portátil, servidor, workstation extrema, o no es componente estándar de sobremesa.

{items_txt}

Responde ÚNICAMENTE con un array JSON de {len(productos)} objetos, en el mismo orden:
[
  {{
    "marca": "string",
    "features": ["feature1", ...],
    "specs": {specs_fmt},
    "incluir": true
  }},
  ...
]"""


def clasificar_lote(categoria: str, productos: list[dict]) -> list[dict | None]:
    """Llama a Gemini con un lote de productos y devuelve la clasificación.
    Reintenta automáticamente si hay error 429 (quota)."""
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no encontrada en .env")

    client = genai.Client(api_key=api_key)
    prompt = construir_prompt_lote(categoria, productos)

    for intento in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip()

            # Limpiar bloque markdown si Gemini lo añade
            if "```" in text:
                bloques = text.split("```")
                for bloque in bloques:
                    bloque = bloque.strip()
                    if bloque.startswith("json"):
                        bloque = bloque[4:].strip()
                    if bloque.startswith("["):
                        text = bloque
                        break

            resultado = json.loads(text)
            if isinstance(resultado, list) and len(resultado) == len(productos):
                return resultado
            logger.warning(
                f"Gemini devolvió {len(resultado)} resultados para {len(productos)} productos"
            )
            return [None] * len(productos)

        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                # Extraer tiempo de espera sugerido si está disponible
                wait = 65
                import re

                match = re.search(r"retry[^\d]*(\d+)", msg, re.IGNORECASE)
                if match:
                    wait = int(match.group(1)) + 5
                logger.warning(
                    f"Quota agotada (429). Esperando {wait}s antes de reintentar ({intento+1}/3)..."
                )
                time.sleep(wait)
            else:
                logger.error(f"Error Gemini en lote de {categoria}: {e}")
                return [None] * len(productos)

    logger.error(
        f"Gemini sigue sin responder tras 3 reintentos para lote de {categoria}"
    )
    return [None] * len(productos)


def clasificar_categoria(categoria: str, productos_raw: list[dict]) -> list[dict]:
    """Clasifica todos los productos de una categoría en lotes."""
    clasificados = []
    total = len(productos_raw)

    for inicio in range(0, total, LOTE_GEMINI):
        lote = productos_raw[inicio : inicio + LOTE_GEMINI]
        logger.info(
            f"  Gemini lote {inicio//LOTE_GEMINI + 1}/{(total-1)//LOTE_GEMINI + 1} ({len(lote)} productos)"
        )

        resultados = clasificar_lote(categoria, lote)
        time.sleep(DELAY_GEMINI)

        for prod, res in zip(lote, resultados):
            if res and res.get("incluir", True):
                entry = {
                    "nombre": prod["nombre"],
                    "marca": res.get("marca", ""),
                    "categoria": categoria,
                    "features": res.get("features", []),
                    "precio": prod["precio"],
                    "specs": res.get("specs", {}),
                }
                clasificados.append(entry)
                logger.info(f"    ✓ {entry['nombre'][:55]} → {entry['features']}")
            else:
                logger.info(f"    ✗ Descartado: {prod['nombre'][:55]}")

    return clasificados


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Scraper Coolmod + Gemini")
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=2,
        help="Páginas por categoría (default 2 = ~50 productos)",
    )
    parser.add_argument(
        "--solo-cat",
        type=str,
        default=None,
        help="Scrapear solo esta categoría (ej: Procesador)",
    )
    parser.add_argument(
        "--sin-gemini",
        action="store_true",
        help="Solo scraping, sin clasificación Gemini (guarda datos en bruto)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Añadir resultados al catalogo_real.json existente (no sobreescribir)",
    )
    args = parser.parse_args()

    categorias = CATEGORIAS
    if args.solo_cat:
        if args.solo_cat not in CATEGORIAS:
            logger.error(
                f"Categoría desconocida: {args.solo_cat}. Válidas: {list(CATEGORIAS)}"
            )
            sys.exit(1)
        categorias = {args.solo_cat: CATEGORIAS[args.solo_cat]}

    catalogo_final = []

    for categoria, base_url in categorias.items():
        # Scraping
        productos_raw = scrape_categoria(categoria, base_url, args.max_paginas)
        if not productos_raw:
            logger.warning(f"Sin productos para {categoria}")
            continue

        if args.sin_gemini:
            # Guardar datos en bruto para inspección
            out = os.path.join(
                os.path.dirname(__file__), "data", f"raw_{categoria}.json"
            )
            with open(out, "w", encoding="utf-8") as f:
                json.dump(productos_raw, f, ensure_ascii=False, indent=2)
            logger.info(f"  Guardado en {out}")
            continue

        # Clasificación con Gemini
        logger.info(f"\n  Clasificando {len(productos_raw)} productos con Gemini...")
        clasificados = clasificar_categoria(categoria, productos_raw)
        catalogo_final.extend(clasificados)
        logger.info(f"  {len(clasificados)}/{len(productos_raw)} productos incluidos")

    if not args.sin_gemini and catalogo_final:
        out_path = os.path.join(os.path.dirname(__file__), "data", "catalogo_real.json")

        # En modo append, cargar los productos existentes y combinar
        if args.append and os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                existentes = json.load(f)
            cats_nuevas = {p["categoria"] for p in catalogo_final}
            existentes_filtrados = [
                p for p in existentes if p["categoria"] not in cats_nuevas
            ]
            catalogo_final = existentes_filtrados + catalogo_final
            logger.info(
                f"Modo append: {len(existentes_filtrados)} productos previos + {len(cats_nuevas)} categorías nuevas"
            )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(catalogo_final, f, ensure_ascii=False, indent=2)

        from collections import Counter

        por_cat = Counter(p["categoria"] for p in catalogo_final)
        logger.info(f"\n{'='*55}")
        logger.info(f"COMPLETADO — {len(catalogo_final)} productos en {out_path}")
        for cat, n in sorted(por_cat.items()):
            logger.info(f"  {cat}: {n}")


if __name__ == "__main__":
    main()
