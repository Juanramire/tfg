import pytest
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
