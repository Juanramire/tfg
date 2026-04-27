import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  Typography,
  Slider,
  Stack,
  Chip,
  Checkbox,
  FormControlLabel,
} from "@mui/material";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import MovieIcon from "@mui/icons-material/Movie";
import CodeIcon from "@mui/icons-material/Code";
import DescriptionIcon from "@mui/icons-material/Description";
import useConfigStore from "../store/useConfigStore";
import { getPerfiles } from "../services/api";

const iconMap = {
  Gaming: <SportsEsportsIcon fontSize="large" />,
  Edicion: <MovieIcon fontSize="large" />,
  Programacion: <CodeIcon fontSize="large" />,
  Ofimatica: <DescriptionIcon fontSize="large" />,
};

const presupuestoDefecto = {
  Gaming: 1200,
  Edicion: 1500,
  Programacion: 1000,
  Ofimatica: 600,
};

export default function StepPerfil() {
  const { perfil, presupuesto, setPerfil, setPresupuesto, selectFeature, deselectFeature, generarConfigAuto, loading } =
    useConfigStore();
  const [perfiles, setPerfiles] = useState({});

  useEffect(() => {
    getPerfiles().then(setPerfiles).catch(() => {});
  }, []);

  const usarPresupuesto = presupuesto !== null;

  const handleTogglePresupuesto = () => {
    if (usarPresupuesto) {
      setPresupuesto(null);
    } else {
      setPresupuesto(presupuestoDefecto[perfil] || 1000);
    }
  };

  const handleSelectPerfil = async (nombre) => {
    if (perfil === nombre) {
      setPerfil(null);
      await deselectFeature(nombre);
      return;
    }

    if (perfil) {
      await deselectFeature(perfil);
    }

    setPerfil(nombre);
    if (usarPresupuesto) {
      setPresupuesto(presupuestoDefecto[nombre] || 1000);
    }
    await selectFeature(nombre);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Elige tu perfil de uso (opcional)
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Selecciona para qué usarás el PC. El sistema ajustará las
        recomendaciones automáticamente.
      </Typography>

      <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap mb={4}>
        {Object.entries(perfiles).map(([nombre, descripcion]) => (
          <Card
            key={nombre}
            sx={{
              width: 200,
              border: perfil === nombre ? 2 : 0,
              borderColor: "primary.main",
            }}
          >
            <CardActionArea onClick={() => handleSelectPerfil(nombre)} sx={{ p: 2 }}>
              <Stack alignItems="center" spacing={1}>
                <Box color={perfil === nombre ? "primary.main" : "text.secondary"}>
                  {iconMap[nombre]}
                </Box>
                <Typography fontWeight="bold">{nombre}</Typography>
                <Typography variant="caption" color="text.secondary" textAlign="center">
                  {descripcion}
                </Typography>
                {perfil === nombre && <Chip label="Seleccionado" color="primary" size="small" />}
              </Stack>
            </CardActionArea>
          </Card>
        ))}
      </Stack>

      <Stack direction="row" alignItems="center" spacing={1} mb={1}>
        <Typography variant="h6">Presupuesto</Typography>
        <FormControlLabel
          control={
            <Checkbox
              checked={usarPresupuesto}
              onChange={handleTogglePresupuesto}
              size="small"
            />
          }
          label={
            <Typography variant="body2" color="text.secondary">
              Establecer presupuesto
            </Typography>
          }
          sx={{ ml: 1 }}
        />
      </Stack>

      {usarPresupuesto && (
        <Stack direction="row" alignItems="center" spacing={3} sx={{ px: 2 }}>
          <Slider
            value={presupuesto}
            onChange={(_, v) => setPresupuesto(v)}
            min={300}
            max={3000}
            step={50}
            valueLabelDisplay="on"
            valueLabelFormat={(v) => `${v}€`}
          />
        </Stack>
      )}

      {perfil && (
        <Box textAlign="center" mt={4}>
          <Button
            variant="contained"
            size="large"
            onClick={generarConfigAuto}
            disabled={loading || !usarPresupuesto}
            sx={{ px: 5 }}
          >
            {loading ? "Generando..." : "Generar configuración automática"}
          </Button>
          <Typography variant="caption" display="block" color="text.secondary" mt={1}>
            {usarPresupuesto
              ? "El sistema elegirá los mejores componentes para tu perfil y presupuesto. Podrás modificarlos después."
              : "Establece un presupuesto para usar la generación automática."}
          </Typography>
        </Box>
      )}
    </Box>
  );
}
