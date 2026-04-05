import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestPresupuesto:
    def test_presupuesto_1000(self):
        r = client.post(
            "/api/configuracion/presupuesto",
            json={"presupuesto": 1000},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["presupuesto"] == 1000
        assert data["precio_total"] > 0
        assert len(data["componentes"]) >= 7

    def test_presupuesto_minimo(self):
        r = client.post(
            "/api/configuracion/presupuesto",
            json={"presupuesto": 100},
        )
        assert r.status_code == 400
        assert "mínimo" in r.json()["detail"]

    def test_presupuesto_con_restricciones(self):
        r = client.post(
            "/api/configuracion/presupuesto",
            json={"presupuesto": 1500, "selected": ["AMD", "AM5"]},
        )
        data = r.json()
        # Todos los componentes deben ser compatibles con AMD AM5
        for c in data["componentes"]:
            p = c["producto"]
            if c["categoria"] == "Procesador":
                assert "AMD" in p["features"]
            if c["categoria"] == "PlacaBase":
                assert "AM5" in p["features"]

    def test_presupuesto_gaming(self):
        r = client.post(
            "/api/configuracion/presupuesto",
            json={"presupuesto": 1500, "selected": ["Gaming"]},
        )
        data = r.json()
        categorias = [c["categoria"] for c in data["componentes"]]
        assert "TarjetaGrafica" in categorias
        # GPU no debe ser gama baja (Gaming lo prohíbe)
        for c in data["componentes"]:
            if c["categoria"] == "TarjetaGrafica":
                assert "GPU_Gama_Baja" not in c["producto"]["features"]

    def test_aviso_presupuesto_insuficiente(self):
        r = client.post(
            "/api/configuracion/presupuesto",
            json={"presupuesto": 300, "selected": ["Gaming"]},
        )
        data = r.json()
        assert data["precio_total"] > 300
        assert len(data["avisos"]) > 0
        assert "supera" in data["avisos"][0]


class TestPerfil:
    def test_perfil_gaming(self):
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Gaming"},
        )
        data = r.json()
        assert data["perfil"] == "Gaming"
        categorias = [c["categoria"] for c in data["componentes"]]
        assert "TarjetaGrafica" in categorias

    def test_perfil_ofimatica_sin_gpu(self):
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Ofimatica"},
        )
        data = r.json()
        categorias = [c["categoria"] for c in data["componentes"]]
        assert "TarjetaGrafica" not in categorias

    def test_perfil_con_presupuesto_custom(self):
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Gaming", "presupuesto": 2000},
        )
        data = r.json()
        assert data["presupuesto"] == 2000

    def test_perfil_desconocido(self):
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Inventado"},
        )
        assert r.status_code == 400

    def test_listar_perfiles(self):
        r = client.get("/api/configuracion/perfiles")
        assert r.status_code == 200
        data = r.json()
        assert "Gaming" in data
        assert "Ofimatica" in data
        assert "Edicion" in data
        assert "Programacion" in data


class TestCoherencia:
    def test_componentes_son_compatibles_entre_si(self):
        """All selected products should form a valid FlamaPy configuration."""
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Gaming", "presupuesto": 1500},
        )
        data = r.json()

        # Collect all features from selected products
        all_features = []
        for c in data["componentes"]:
            all_features.extend(c["producto"]["features"])

        # Validate with FlamaPy
        r = client.post(
            "/api/features/validate",
            json={"selected": all_features},
        )
        assert r.json()["valid"] is True

    def test_ofimatica_coherente(self):
        """Ofimática config should also be valid in FlamaPy."""
        r = client.post(
            "/api/configuracion/perfil",
            json={"perfil": "Ofimatica"},
        )
        data = r.json()

        all_features = []
        for c in data["componentes"]:
            all_features.extend(c["producto"]["features"])

        r = client.post(
            "/api/features/validate",
            json={"selected": all_features},
        )
        assert r.json()["valid"] is True
