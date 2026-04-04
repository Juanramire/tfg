import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestListarProductos:
    def test_listar_todos(self):
        r = client.get("/api/productos/")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert len(data["productos"]) == data["total"]

    def test_filtrar_por_categoria(self):
        r = client.get("/api/productos/?categoria=Procesador")
        data = r.json()
        assert data["total"] > 0
        for p in data["productos"]:
            assert p["categoria"] == "Procesador"

    def test_filtrar_por_features(self):
        r = client.get("/api/productos/?features=AMD,AM5")
        data = r.json()
        assert data["total"] > 0
        for p in data["productos"]:
            assert "AMD" in p["features"]
            assert "AM5" in p["features"]

    def test_filtrar_categoria_y_features(self):
        r = client.get("/api/productos/?categoria=PlacaBase&features=LGA1700,DDR5")
        data = r.json()
        assert data["total"] > 0
        for p in data["productos"]:
            assert p["categoria"] == "PlacaBase"
            assert "LGA1700" in p["features"]
            assert "DDR5" in p["features"]

    def test_categoria_sin_resultados(self):
        r = client.get("/api/productos/?categoria=NoExiste")
        data = r.json()
        assert data["total"] == 0

    def test_features_incompatibles(self):
        r = client.get("/api/productos/?features=AMD,LGA1700")
        data = r.json()
        assert data["total"] == 0


class TestCategorias:
    def test_listar_categorias(self):
        r = client.get("/api/productos/categorias")
        assert r.status_code == 200
        data = r.json()
        assert "Procesador" in data["categorias"]
        assert "TarjetaGrafica" in data["categorias"]
        assert "PlacaBase" in data["categorias"]


class TestIntegracionFlamapyProductos:
    def test_flujo_gaming_amd_am5(self):
        """Gaming+AMD+AM5: propagar constraints -> filtrar productos compatibles."""
        # Propagar
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["Gaming", "AMD", "AM5"], "deselected": []},
        )
        prop = r.json()

        # Procesadores deben ser AMD AM5
        r = client.get("/api/productos/?categoria=Procesador&features=AMD,AM5")
        cpus = r.json()
        assert cpus["total"] > 0

        # GPU_Gama_Baja está excluida por Gaming
        assert "GPU_Gama_Baja" in prop["excluded"]

        # Solo GPUs media y alta
        r = client.get(
            "/api/productos/?categoria=TarjetaGrafica&features=GPU_Gama_Baja"
        )
        assert r.json()["total"] > 0  # existen en catálogo...
        # ...pero el modelo las excluye (validación la hace el frontend con prop["excluded"])

    def test_intel_lga1700_ddr4_filtra_placas(self):
        """Intel LGA1700 con DDR4: solo placas con esas features."""
        r = client.get("/api/productos/?categoria=PlacaBase&features=LGA1700,DDR4")
        data = r.json()
        assert data["total"] > 0
        for p in data["productos"]:
            assert "LGA1700" in p["features"]
            assert "DDR4" in p["features"]
