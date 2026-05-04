"""
Importa catalogo_real.json a MongoDB (y lo convierte en el catálogo activo).

Uso:
  python import_catalogo.py           # importa catalogo_real.json
  python import_catalogo.py --dry-run # solo muestra estadísticas, no modifica nada
  python import_catalogo.py --restaurar # restaura el backup anterior
"""

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
REAL_PATH = DATA_DIR / "catalogo_real.json"
ACTIVO_PATH = DATA_DIR / "catalogo.json"
BACKUP_PATH = DATA_DIR / "catalogo_backup.json"

CATEGORIAS_VALIDAS = {
    "Procesador",
    "PlacaBase",
    "MemoriaRAM",
    "TarjetaGrafica",
    "Almacenamiento",
    "FuenteAlimentacion",
    "Chasis",
    "Refrigeracion",
}

FEATURES_VALIDAS = {
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
    "DDR4",
    "DDR5",
    "RAM_8GB",
    "RAM_16GB",
    "RAM_32GB",
    "RAM_64GB",
    "GPU_Gama_Baja",
    "GPU_Gama_Media",
    "GPU_Gama_Alta",
    "SSD_NVMe",
    "SSD_SATA",
    "Disco_HDD",
    "PSU_500W",
    "PSU_650W",
    "PSU_750W",
    "PSU_850W",
    "Placa_ATX",
    "Placa_MicroATX",
    "Placa_MiniITX",
    "Caja_ATX",
    "Caja_MicroATX",
    "Caja_MiniITX",
    "Refrigeracion_Aire",
    "Refrigeracion_Liquida",
}


def validar(catalogo: list[dict]) -> list[str]:
    errores = []
    for i, p in enumerate(catalogo):
        ref = f"[{i}] {p.get('nombre', '?')}"
        if not p.get("nombre"):
            errores.append(f"{ref}: falta 'nombre'")
        if p.get("categoria") not in CATEGORIAS_VALIDAS:
            errores.append(f"{ref}: categoría inválida '{p.get('categoria')}'")
        if not isinstance(p.get("precio"), (int, float)) or p["precio"] <= 0:
            errores.append(f"{ref}: precio inválido '{p.get('precio')}'")
        features = p.get("features", [])
        if not features:
            errores.append(f"{ref}: sin features")
        for f in features:
            if f not in FEATURES_VALIDAS:
                errores.append(f"{ref}: feature desconocida '{f}'")
    return errores


def mostrar_estadisticas(catalogo: list[dict]):
    print(f"\nTotal productos: {len(catalogo)}")
    print("\nPor categoría:")
    for cat, n in sorted(Counter(p["categoria"] for p in catalogo).items()):
        print(f"  {cat:<22} {n:>3}")
    print("\nPor feature (top 15):")
    todas = [f for p in catalogo for f in p.get("features", [])]
    for feat, n in Counter(todas).most_common(15):
        print(f"  {feat:<25} {n:>3}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="Mostrar estadísticas sin modificar nada"
    )
    parser.add_argument(
        "--restaurar", action="store_true", help="Restaurar backup anterior"
    )
    args = parser.parse_args()

    # --- Restaurar backup ---
    if args.restaurar:
        if not BACKUP_PATH.exists():
            print("No hay backup disponible.")
            sys.exit(1)
        shutil.copy2(BACKUP_PATH, ACTIVO_PATH)
        print(f"Restaurado: {BACKUP_PATH} → {ACTIVO_PATH}")
        sys.exit(0)

    # --- Cargar catalogo_real.json ---
    if not REAL_PATH.exists():
        print(f"ERROR: No existe {REAL_PATH}")
        print("Ejecuta primero: python scraper_coolmod.py")
        sys.exit(1)

    with open(REAL_PATH, encoding="utf-8") as f:
        catalogo = json.load(f)

    print(f"Cargado: {REAL_PATH} ({len(catalogo)} productos)")

    # --- Validar ---
    errores = validar(catalogo)
    if errores:
        print(f"\n{len(errores)} errores de validación:")
        for e in errores[:20]:
            print(f"  ⚠ {e}")
        if len(errores) > 20:
            print(f"  ... y {len(errores) - 20} más")
        respuesta = input("\n¿Continuar de todos modos? [s/N] ").strip().lower()
        if respuesta != "s":
            sys.exit(1)

    mostrar_estadisticas(catalogo)

    if args.dry_run:
        print("\n[dry-run] No se ha modificado nada.")
        sys.exit(0)

    # --- Backup + reemplazar catálogo activo ---
    if ACTIVO_PATH.exists():
        shutil.copy2(ACTIVO_PATH, BACKUP_PATH)
        print(f"\nBackup: {ACTIVO_PATH} → {BACKUP_PATH}")

    shutil.copy2(REAL_PATH, ACTIVO_PATH)
    print(f"Activo: {REAL_PATH} → {ACTIVO_PATH}")

    # --- Importar a MongoDB ---
    try:
        from services.db import seed_database

        n = seed_database()
        print(f"MongoDB: {n} productos importados correctamente.")
    except RuntimeError as e:
        print(f"MongoDB no disponible ({e}) — el catálogo JSON ya está actualizado.")
    except Exception as e:
        print(f"Error MongoDB: {e} — el catálogo JSON ya está actualizado.")

    print("\nImportación completada.")


if __name__ == "__main__":
    main()
