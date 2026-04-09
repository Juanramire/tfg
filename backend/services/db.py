import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

CATALOGO_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogo.json"


def _get_mongo_collection():
    """Try to connect to MongoDB. Returns the collection or None."""
    mongo_uri = os.getenv("MONGO_URI", "")
    if not mongo_uri or "xxxxx" in mongo_uri or "TU_CONTRASEÑA" in mongo_uri:
        logger.warning("MONGO_URI no configurado, usando catálogo local JSON")
        return None
    try:
        from pymongo import MongoClient

        client = MongoClient(
            mongo_uri,
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


_collection = _get_mongo_collection()


def _load_json_catalog() -> list[dict]:
    with open(CATALOGO_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_productos(
    categoria: str | None = None,
    features: list[str] | None = None,
) -> list[dict]:
    """Get products, optionally filtered by category and/or features.

    If MongoDB is available, queries it. Otherwise falls back to the JSON file.
    """
    if _collection is not None:
        query = {}
        if categoria:
            query["categoria"] = categoria
        if features:
            query["features"] = {"$all": features}
        return list(_collection.find(query, {"_id": 0}))

    # Fallback: JSON local
    productos = _load_json_catalog()
    if categoria:
        productos = [p for p in productos if p["categoria"] == categoria]
    if features:
        feature_set = set(features)
        productos = [p for p in productos if feature_set.issubset(set(p["features"]))]
    return productos


def seed_database() -> int:
    """Load the JSON catalog into MongoDB. Returns number of products inserted."""
    if _collection is None:
        raise RuntimeError("MongoDB no disponible. Configura MONGO_URI en .env")
    productos = _load_json_catalog()
    _collection.delete_many({})
    result = _collection.insert_many(productos)
    return len(result.inserted_ids)
