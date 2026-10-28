import { useSyncExternalStore } from "react";
import { Alert, CircularProgress } from "@mui/material";
import { suscribirArranque, isServidorArrancando } from "../services/api";

// Aviso que aparece si la primera petición al backend tarda más de 3 s
// (el servidor gratuito de Render se duerme y tarda en arrancar).
export default function AvisoArranque() {
  const arrancando = useSyncExternalStore(suscribirArranque, isServidorArrancando);
  if (!arrancando) return null;

  return (
    <Alert
      severity="info"
      role="status"
      icon={<CircularProgress size={18} color="inherit" />}
      sx={{ mb: 2 }}
    >
      Arrancando el servidor, puede tardar hasta un minuto…
    </Alert>
  );
}
