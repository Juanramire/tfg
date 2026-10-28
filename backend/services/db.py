import json
import logging
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

CATALOGO_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogo.json"

# Tiempo mínimo entre intentos de reconexión a MongoDB, para no penalizar la
# latencia de cada petición mientras la base de datos no esté disponible.
MONGO_RETRY_INTERVAL_S = 60


class CatalogoNoDisponibleError(RuntimeError):
    """Ni MongoDB ni el catálogo JSON local están disponibles."""


def _mongo_configurado() -> bool:
    mongo_uri = os.getenv("MONGO_URI", "")
    return (
        bool(mongo_uri)
        and "xxxxx" not in mongo_uri
        and "TU_CONTRASEÑA" not in mongo_uri
    )


def _get_mongo_collection():
    """Intenta conectar a MongoDB. Devuelve la colección o None."""
    if not _mongo_configurado():
        logger.warning("MONGO_URI no configurado, usando catálogo local JSON")
        return None
    try:
        from pymongo import MongoClient

        client = MongoClient(
            os.getenv("MONGO_URI"),
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=8000,
            tls=True,
            tlsAllowInvalidCertificates=True,
        )
        client.server_info()
        db = client["pc_configurador"]
        return db["productos"]
    except Exception as e:
        logger.warning("No se pudo conectar a MongoDB (%s), usando JSON local", e)
        return None


_collection = None
_last_attempt: float | None = None
_connect_lock = threading.Lock()


def _connect() -> None:
    global _collection, _last_attempt
    _last_attempt = time.monotonic()
    _collection = _get_mongo_collection()
    if _collection is not None:
        logger.info("Conectado a MongoDB")


def _get_collection():
    """Devuelve la colección de MongoDB, reintentando la conexión si toca.

    Si no hay conexión, solo se reintenta cuando han pasado al menos
    MONGO_RETRY_INTERVAL_S desde el último intento. Si otra petición ya está
    reintentando, esta no espera y usa el fallback.
    """
    if _collection is not None:
        return _collection
    if not _mongo_configurado():
        return None

    def _toca_reintentar() -> bool:
        return (
            _last_attempt is None
            or time.monotonic() - _last_attempt >= MONGO_RETRY_INTERVAL_S
        )

    if not _toca_reintentar() or not _connect_lock.acquire(blocking=False):
        return None
    try:
        if _collection is None and _toca_reintentar():
            _connect()
    finally:
        _connect_lock.release()
    return _collection


def _marcar_desconectado(error: Exception) -> None:
    global _collection, _last_attempt
    logger.warning("Error consultando MongoDB (%s), usando JSON local", error)
    _collection = None
    _last_attempt = time.monotonic()


_connect()


def _load_json_catalog() -> list[dict]:
    try:
        with open(CATALOGO_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error("Catálogo JSON no encontrado en %s", CATALOGO_PATH)
        raise CatalogoNoDisponibleError(
            "El catálogo de productos no está disponible en este momento. "
            "Inténtalo de nuevo más tarde."
        ) from e


def get_productos(
    categoria: str | None = None,
    features: list[str] | None = None,
) -> list[dict]:
    """Obtiene productos, opcionalmente filtrados por categoría y/o features.

    Si MongoDB está disponible, consulta en él. Si no, usa el fichero JSON como fallback.
    Lanza CatalogoNoDisponibleError si no hay ninguna de las dos fuentes.
    """
    collection = _get_collection()
    if collection is not None:
        query = {}
        if categoria:
            query["categoria"] = categoria
        if features:
            query["features"] = {"$all": features}
        try:
            return list(collection.find(query, {"_id": 0}))
        except Exception as e:
            _marcar_desconectado(e)

    # Fallback: catálogo JSON local
    productos = _load_json_catalog()
    if categoria:
        productos = [p for p in productos if p["categoria"] == categoria]
    if features:
        feature_set = set(features)
        productos = [p for p in productos if feature_set.issubset(set(p["features"]))]
    return productos


def seed_database() -> int:
    """Carga el catálogo JSON en MongoDB. Devuelve el número de productos insertados."""
    collection = _get_collection()
    if collection is None:
        raise RuntimeError("MongoDB no disponible. Configura MONGO_URI en .env")
    productos = _load_json_catalog()
    collection.delete_many({})
    result = collection.insert_many(productos)
    return len(result.inserted_ids)
