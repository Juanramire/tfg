from fastapi.testclient import TestClient

# Asumiendo que main.py está en el directorio padre de tests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "¡El Backend del TFG está funcionando!"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_no_consulta_mongo_ni_flamapy():
    from unittest.mock import patch

    with patch("services.db.get_productos") as productos, patch(
        "services.db._get_collection"
    ) as coleccion, patch("services.flamapy_service.flamapy_service") as flamapy:
        response = client.get("/health")
    assert response.status_code == 200
    productos.assert_not_called()
    coleccion.assert_not_called()
    assert flamapy.mock_calls == []
