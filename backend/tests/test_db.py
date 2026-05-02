import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestFallbackJSON:
    """Verifica que la API funciona usando el catálogo JSON cuando MongoDB no está disponible."""

    def test_listar_todos_sin_mongodb(self):
        with patch("services.db._collection", None):
            r = client.get("/api/productos/")
            assert r.status_code == 200
            assert r.json()["total"] > 0

    def test_filtrar_categoria_sin_mongodb(self):
        with patch("services.db._collection", None):
            r = client.get("/api/productos/?categoria=Procesador")
            data = r.json()
            assert data["total"] > 0
            for p in data["productos"]:
                assert p["categoria"] == "Procesador"

    def test_filtrar_features_sin_mongodb(self):
        with patch("services.db._collection", None):
            r = client.get("/api/productos/?features=AMD,AM5")
            data = r.json()
            assert data["total"] > 0
            for p in data["productos"]:
                assert "AMD" in p["features"]
                assert "AM5" in p["features"]


class TestGetMongoCollection:
    """Verifica las ramas de _get_mongo_collection."""

    def test_sin_uri_devuelve_none(self):
        from services.db import _get_mongo_collection

        with patch("services.db.os.getenv", return_value=""):
            assert _get_mongo_collection() is None

    def test_conexion_fallida_devuelve_none(self):
        from services.db import _get_mongo_collection

        with patch("services.db.os.getenv", return_value="mongodb://invalid"):
            with patch("pymongo.MongoClient") as mock_client:
                mock_client.return_value.server_info.side_effect = Exception("timeout")
                assert _get_mongo_collection() is None


class TestSeedDatabase:
    """Verifica seed_database con colección mockeada."""

    def test_seed_inserta_productos(self):
        from services.db import seed_database

        mock_col = MagicMock()
        mock_col.insert_many.return_value.inserted_ids = list(range(10))
        with patch("services.db._collection", mock_col):
            n = seed_database()
            assert n == 10
            mock_col.delete_many.assert_called_once_with({})

    def test_seed_sin_mongodb_lanza_error(self):
        import pytest

        from services.db import seed_database

        with patch("services.db._collection", None):
            with pytest.raises(RuntimeError, match="MongoDB no disponible"):
                seed_database()
