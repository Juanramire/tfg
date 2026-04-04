import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestFeatureTree:
    def test_tree_returns_root(self):
        r = client.get("/api/features/tree")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "PC_Custom"
        assert len(data["groups"]) > 0

    def test_tree_has_mandatory_and_optional_groups(self):
        r = client.get("/api/features/tree")
        data = r.json()
        group_types = [g["type"] for g in data["groups"]]
        assert "mandatory" in group_types
        assert "optional" in group_types


class TestValidate:
    def test_valid_partial_config(self):
        r = client.post(
            "/api/features/validate",
            json={"selected": ["AMD", "AM5", "DDR5"]},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_invalid_config_amd_with_lga1700(self):
        r = client.post(
            "/api/features/validate",
            json={"selected": ["AMD", "LGA1700"]},
        )
        assert r.status_code == 200
        assert r.json()["valid"] is False

    def test_invalid_config_gaming_without_gpu(self):
        """Gaming requires TarjetaGrafica, so selecting Gaming + deselecting GPU is invalid."""
        r = client.post(
            "/api/features/validate",
            json={"selected": ["Gaming"]},
        )
        # Gaming alone IS satisfiable (GPU can be added)
        assert r.json()["valid"] is True

    def test_unknown_feature_returns_400(self):
        r = client.post(
            "/api/features/validate",
            json={"selected": ["NO_EXISTE"]},
        )
        assert r.status_code == 400
        assert "desconocidas" in r.json()["detail"]


class TestPropagate:
    def test_propagate_amd_excludes_intel(self):
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["AMD"], "deselected": []},
        )
        assert r.status_code == 200
        data = r.json()
        assert "AMD" in data["forced"]
        assert "Intel" in data["excluded"]
        assert "LGA1700" in data["excluded"]
        assert "LGA1851" in data["excluded"]

    def test_propagate_am5_forces_ddr5(self):
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["AMD", "AM5"], "deselected": []},
        )
        data = r.json()
        assert "DDR5" in data["forced"]
        assert "DDR4" in data["excluded"]

    def test_propagate_gaming_forces_gpu(self):
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["Gaming"], "deselected": []},
        )
        data = r.json()
        assert "TarjetaGrafica" in data["forced"]
        assert "GPU_Gama_Baja" in data["excluded"]
        assert "RAM_8GB" in data["excluded"]

    def test_propagate_unknown_feature_returns_400(self):
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["INVENTADA"], "deselected": []},
        )
        assert r.status_code == 400

    def test_propagate_conflicting_features_returns_400(self):
        r = client.post(
            "/api/features/propagate",
            json={"selected": ["AMD"], "deselected": ["AMD"]},
        )
        assert r.status_code == 400
        assert "ambas listas" in r.json()["detail"]


class TestInfo:
    def test_info_returns_satisfiable(self):
        r = client.get("/api/features/info")
        assert r.status_code == 200
        data = r.json()
        assert data["satisfiable"] is True
        assert data["num_configurations"] > 0
        assert "PC_Custom" in data["core_features"]
        assert data["dead_features"] == []
