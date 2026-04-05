import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Button,
  Divider,
  Chip,
  Alert,
} from "@mui/material";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import useConfigStore from "../store/useConfigStore";

export default function StepResumen() {
  const navigate = useNavigate();
  const { componentesElegidos, presupuesto, perfil, reset, prevStep } =
    useConfigStore();

  const componentes = Object.entries(componentesElegidos);
  const precioTotal = componentes.reduce(
    (sum, [, p]) => sum + p.precio,
    0
  );
  const dentroPresupuesto = precioTotal <= presupuesto;

  const handleNueva = () => {
    reset();
    navigate("/configurar");
  };

  if (componentes.length === 0) {
    return (
      <Box textAlign="center" py={4}>
        <Typography variant="h6" color="text.secondary" mb={2}>
          No has seleccionado ningún componente todavía.
        </Typography>
        <Button variant="outlined" onClick={prevStep}>
          Volver atrás
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Resumen de tu configuración
      </Typography>

      {perfil && (
        <Chip label={`Perfil: ${perfil}`} color="primary" sx={{ mb: 2 }} />
      )}

      <Stack spacing={1.5} mb={3}>
        {componentes.map(([categoria, producto]) => (
          <Card key={categoria} variant="outlined">
            <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {categoria}
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {producto.nombre}
                  </Typography>
                </Box>
                <Typography variant="subtitle1" color="primary" fontWeight="bold">
                  {producto.precio.toFixed(2)}€
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Divider sx={{ mb: 2 }} />

      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body1" color="text.secondary">
          Presupuesto
        </Typography>
        <Typography variant="body1">{presupuesto.toFixed(2)}€</Typography>
      </Stack>

      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Total</Typography>
        <Typography
          variant="h5"
          fontWeight="bold"
          color={dentroPresupuesto ? "success.main" : "error.main"}
        >
          {precioTotal.toFixed(2)}€
        </Typography>
      </Stack>

      {!dentroPresupuesto && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          El precio total supera tu presupuesto en{" "}
          {(precioTotal - presupuesto).toFixed(2)}€.
        </Alert>
      )}

      {dentroPresupuesto && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Ahorras {(presupuesto - precioTotal).toFixed(2)}€ respecto a tu
          presupuesto.
        </Alert>
      )}

      <Stack direction="row" spacing={2} justifyContent="center" mt={3}>
        <Button
          variant="outlined"
          startIcon={<RestartAltIcon />}
          onClick={handleNueva}
        >
          Nueva configuración
        </Button>
      </Stack>
    </Box>
  );
}
