import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture
def sin_mongodb():
    """Simula MongoDB caído sin reintentos reales (no toca el Mongo del .env)."""
    with patch("services.db._collection", None), patch(
        "services.db._last_attempt", None
    ), patch("services.db._get_mongo_collection", return_value=None):
        yield


@pytest.fixture
def mongo_configurado():
    with patch("services.db._mongo_configurado", return_value=True):
        yield


class TestFallbackJSON:
    """Verifica que la API funciona usando el catálogo JSON cuando MongoDB no está disponible."""

    def test_listar_todos_sin_mongodb(self, sin_mongodb):
        r = client.get("/api/productos/")
        assert r.status_code == 200
        assert r.json()["total"] > 0

    def test_filtrar_categoria_sin_mongodb(self, sin_mongodb):
        r = client.get("/api/productos/?categoria=Procesador")
        data = r.json()
        assert data["total"] > 0
        for p in data["productos"]:
            assert p["categoria"] == "Procesador"

    def test_filtrar_features_sin_mongodb(self, sin_mongodb):
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


class TestReconexionMongo:
    """Verifica que se reintenta conectar a MongoDB respetando el intervalo mínimo."""

    def test_reintenta_tras_intervalo_y_usa_mongo(self, sin_mongodb, mongo_configurado):
        import services.db as db

        mock_col = MagicMock()
        mock_col.find.return_value = [{"nombre": "X", "categoria": "Procesador"}]
        with patch(
            "services.db._get_mongo_collection", return_value=mock_col
        ) as conn, patch("services.db.time.monotonic", return_value=1000.0):
            db._last_attempt = 1000.0 - db.MONGO_RETRY_INTERVAL_S
            productos = db.get_productos(categoria="Procesador")

        conn.assert_called_once()
        assert productos == [{"nombre": "X", "categoria": "Procesador"}]
        mock_col.find.assert_called_once_with({"categoria": "Procesador"}, {"_id": 0})

    def test_no_reintenta_antes_del_intervalo(self, sin_mongodb, mongo_configurado):
        import services.db as db

        with patch("services.db._get_mongo_collection") as conn, patch(
            "services.db.time.monotonic", return_value=1000.0
        ):
            db._last_attempt = 1000.0 - db.MONGO_RETRY_INTERVAL_S + 1
            productos = db.get_productos()

        conn.assert_not_called()
        assert len(productos) > 0  # catálogo JSON

    def test_reintento_fallido_actualiza_marca_y_no_repite(
        self, sin_mongodb, mongo_configurado
    ):
        import services.db as db

        reloj = [1000.0]
        with patch(
            "services.db._get_mongo_collection", return_value=None
        ) as conn, patch("services.db.time.monotonic", side_effect=lambda: reloj[0]):
            db._last_attempt = 0.0
            db.get_productos()
            assert conn.call_count == 1
            assert db._last_attempt == 1000.0

            reloj[0] = 1000.0 + db.MONGO_RETRY_INTERVAL_S - 1
            db.get_productos()
            assert conn.call_count == 1

            reloj[0] = 1000.0 + db.MONGO_RETRY_INTERVAL_S
            db.get_productos()
            assert conn.call_count == 2

    def test_sin_uri_no_reintenta(self, sin_mongodb):
        import services.db as db

        with patch("services.db._mongo_configurado", return_value=False), patch(
            "services.db._get_mongo_collection"
        ) as conn:
            db.get_productos()
        conn.assert_not_called()

    def test_no_reintenta_si_otra_peticion_ya_lo_hace(
        self, sin_mongodb, mongo_configurado
    ):
        import services.db as db

        with patch("services.db._get_mongo_collection") as conn:
            db._connect_lock.acquire()
            try:
                assert db._get_collection() is None
            finally:
                db._connect_lock.release()
        conn.assert_not_called()

    def test_error_en_consulta_cae_a_json_y_marca_desconectado(self, sin_mongodb):
        import services.db as db

        mock_col = MagicMock()
        mock_col.find.side_effect = Exception("conexión perdida")
        with patch("services.db._collection", mock_col), patch(
            "services.db.time.monotonic", return_value=500.0
        ):
            productos = db.get_productos(categoria="Procesador")
            assert db._collection is None
            assert db._last_attempt == 500.0

        assert len(productos) > 0
        assert all(p["categoria"] == "Procesador" for p in productos)


class TestCatalogoNoDisponible:
    """Sin MongoDB y sin catálogo JSON, la API responde 503 con mensaje claro."""

    @pytest.fixture
    def sin_json(self, tmp_path):
        with patch("services.db.CATALOGO_PATH", tmp_path / "no_existe.json"):
            yield

    def test_load_json_lanza_error_especifico(self, sin_json):
        from services.db import CatalogoNoDisponibleError, _load_json_catalog

        with pytest.raises(CatalogoNoDisponibleError):
            _load_json_catalog()

    def test_listar_productos_devuelve_503(self, sin_mongodb, sin_json):
        r = client.get("/api/productos/")
        assert r.status_code == 503
        assert "catálogo de productos no está disponible" in r.json()["detail"]

    def test_categorias_devuelve_503(self, sin_mongodb, sin_json):
        r = client.get("/api/productos/categorias")
        assert r.status_code == 503

    def test_configuracion_devuelve_503(self, sin_mongodb, sin_json):
        r = client.post("/api/configuracion/presupuesto", json={"presupuesto": 1000})
        assert r.status_code == 503
        assert "detail" in r.json()


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

    def test_seed_sin_mongodb_lanza_error(self, sin_mongodb):
        from services.db import seed_database

        with pytest.raises(RuntimeError, match="MongoDB no disponible"):
            seed_database()
