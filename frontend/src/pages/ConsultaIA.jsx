import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  Chip,
  CircularProgress,
  Paper,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import TuneIcon from "@mui/icons-material/Tune";
import useConfigStore from "../store/useConfigStore";

const EJEMPLOS = [
  "Quiero jugar a Elden Ring en 4K con los gráficos al máximo",
  "Necesito un PC para editar vídeos en 4K, sin gastarme mucho",
  "PC para programar en casa, que sea silencioso y compacto",
  "Algo básico para trabajar con Excel y navegar por internet",
  "PC gaming de gama media para jugar a 1080p sin arruinarme",
];

export default function ConsultaIA() {
  const navigate = useNavigate();
  const { consultarIA, loading, error } = useConfigStore();
  const [consulta, setConsulta] = useState("");
  const [explicacion, setExplicacion] = useState(null);
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async () => {
    if (!consulta.trim()) return;
    setLocalError(null);
    setExplicacion(null);
    try {
      const resultado = await consultarIA(consulta);
      setExplicacion(resultado.explicacion);
      setTimeout(() => navigate("/configurar"), 1200);
    } catch (err) {
      setLocalError(err.message);
    }
  };

  const handleEjemplo = (ejemplo) => setConsulta(ejemplo);

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Stack alignItems="center" spacing={1} mb={4}>
        <AutoAwesomeIcon sx={{ fontSize: 48, color: "primary.main" }} />
        <Typography variant="h4" fontWeight="bold" textAlign="center">
          ¿Qué quieres hacer con tu PC?
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          Descríbelo con tus propias palabras y la IA configurará el PC por ti
        </Typography>
      </Stack>

      <TextField
        fullWidth
        multiline
        minRows={3}
        maxRows={6}
        placeholder="Ej: Quiero editar vídeos en 4K pero sin gastarme demasiado..."
        value={consulta}
        onChange={(e) => setConsulta(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && e.ctrlKey) handleSubmit();
        }}
        sx={{ mb: 2 }}
      />

      <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
        Ejemplos:
      </Typography>
      <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap sx={{ mb: 3 }}>
        {EJEMPLOS.map((ej) => (
          <Chip
            key={ej}
            label={ej}
            size="small"
            variant="outlined"
            onClick={() => handleEjemplo(ej)}
            sx={{ cursor: "pointer", mb: 0.5 }}
          />
        ))}
      </Stack>

      {(error || localError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || localError}
        </Alert>
      )}

      {explicacion && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {explicacion} — redirigiendo al resumen...
        </Alert>
      )}

      <Stack spacing={1.5}>
        <Button
          fullWidth
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <AutoAwesomeIcon />}
          onClick={handleSubmit}
          disabled={loading || !consulta.trim()}
        >
          {loading ? "Analizando consulta..." : "Generar configuración con IA"}
        </Button>

        <Button
          fullWidth
          variant="outlined"
          size="large"
          startIcon={<TuneIcon />}
          onClick={() => navigate("/configurar")}
          disabled={loading}
        >
          Configurar manualmente
        </Button>

        <Button
          size="small"
          color="inherit"
          startIcon={<ArrowForwardIcon />}
          onClick={() => navigate("/")}
          sx={{ alignSelf: "center", opacity: 0.6 }}
        >
          Volver al inicio
        </Button>
      </Stack>

      <Paper variant="outlined" sx={{ mt: 4, p: 2, opacity: 0.6 }}>
        <Typography variant="caption" color="text.secondary">
          Powered by Google Gemini · El análisis tarda unos segundos · Ctrl+Enter para enviar
        </Typography>
      </Paper>
    </Container>
  );
}
