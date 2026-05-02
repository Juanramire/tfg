import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


RESPUESTA_GAMING = '{"perfil": "Gaming", "presupuesto": 1000, "selected": ["Gaming", "GPU_Gama_Media"], "deselected": [], "explicacion": "PC gaming 1080p"}'
RESPUESTA_CON_FEATURE_INVALIDA = '{"perfil": "Gaming", "presupuesto": 900, "selected": ["Gaming", "FeatureInventada"], "deselected": [], "explicacion": "test"}'


def _mock_client(texto_respuesta):
    mock_response = MagicMock()
    mock_response.text = texto_respuesta
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


class TestInterpretarConsulta:
    def test_sin_api_key_lanza_error(self):
        from services.gemini_service import interpretar_consulta

        with patch("services.gemini_service.os.getenv", return_value=""):
            with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
                interpretar_consulta("quiero gaming")

    def test_respuesta_valida(self):
        from services.gemini_service import interpretar_consulta

        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch(
                "google.genai.Client", return_value=_mock_client(RESPUESTA_GAMING)
            ):
                result = interpretar_consulta("quiero gaming 1080p")
                assert result["perfil"] == "Gaming"
                assert "Gaming" in result["selected"]
                assert result["presupuesto"] == 1000

    def test_sanitiza_features_invalidas(self):
        from services.gemini_service import interpretar_consulta

        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch(
                "google.genai.Client",
                return_value=_mock_client(RESPUESTA_CON_FEATURE_INVALIDA),
            ):
                result = interpretar_consulta("gaming")
                assert "FeatureInventada" not in result["selected"]
                assert "Gaming" in result["selected"]

    def test_strip_markdown_con_json(self):
        from services.gemini_service import interpretar_consulta

        respuesta_md = f"```json\n{RESPUESTA_GAMING}\n```"
        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch("google.genai.Client", return_value=_mock_client(respuesta_md)):
                result = interpretar_consulta("gaming")
                assert result["perfil"] == "Gaming"

    def test_strip_markdown_sin_json(self):
        from services.gemini_service import interpretar_consulta

        respuesta_md = f"```\n{RESPUESTA_GAMING}\n```"
        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch("google.genai.Client", return_value=_mock_client(respuesta_md)):
                result = interpretar_consulta("gaming")
                assert result["perfil"] == "Gaming"

    def test_json_invalido_lanza_error(self):
        from services.gemini_service import interpretar_consulta

        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch(
                "google.genai.Client", return_value=_mock_client("esto no es json")
            ):
                with pytest.raises(RuntimeError, match="no pudo interpretar"):
                    interpretar_consulta("gaming")

    def test_error_de_red_lanza_error(self):
        from services.gemini_service import interpretar_consulta

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("timeout")
        with patch("services.gemini_service.os.getenv", return_value="fake-key"):
            with patch("google.genai.Client", return_value=mock_client):
                with pytest.raises(RuntimeError, match="Error al contactar"):
                    interpretar_consulta("gaming")
