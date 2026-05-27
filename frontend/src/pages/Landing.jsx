import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Container,
  Typography,
  Card,
  CardContent,
  Stack,
} from "@mui/material";
import ComputerIcon from "@mui/icons-material/Computer";
import SavingsIcon from "@mui/icons-material/Savings";
import TuneIcon from "@mui/icons-material/Tune";
import SchoolIcon from "@mui/icons-material/School";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

const features = [
  {
    icon: <AutoAwesomeIcon fontSize="large" />,
    title: "Configuración por IA",
    desc: "Describe con tus propias palabras qué quieres hacer con el PC y la IA generará la configuración óptima.",
  },
  {
    icon: <TuneIcon fontSize="large" />,
    title: "Configurador inteligente",
    desc: "Selecciona componentes con validación automática de compatibilidad mediante un modelo de características.",
  },
  {
    icon: <SavingsIcon fontSize="large" />,
    title: "Optimización de presupuesto",
    desc: "Introduce tu presupuesto y el sistema reparte el dinero de forma óptima entre los componentes.",
  },
  {
    icon: <ComputerIcon fontSize="large" />,
    title: "Perfiles de uso",
    desc: "Gaming, Edición, Programación u Ofimática. Elige tu perfil y obtén una configuración adaptada.",
  },
  {
    icon: <SchoolIcon fontSize="large" />,
    title: "Notificaciones educativas",
    desc: "Aprende por qué ciertos componentes son incompatibles o por qué se recomiendan otros.",
  },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Box textAlign="center" mb={6}>
        <Typography variant="h3" fontWeight="bold" gutterBottom>
          Configurador de PC
        </Typography>
        <Typography variant="h6" color="text.secondary" mb={4}>
          Configura tu PC ideal con validación automática de compatibilidad
        </Typography>
        <Stack direction="row" spacing={2} justifyContent="center" flexWrap="wrap" useFlexGap>
          <Button
            variant="contained"
            size="large"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => navigate("/consulta")}
            sx={{ px: 4, py: 1.5, fontSize: "1.1rem" }}
          >
            Configurar con IA
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<TuneIcon />}
            onClick={() => navigate("/configurar")}
            sx={{ px: 4, py: 1.5, fontSize: "1.1rem" }}
          >
            Configurar manualmente
          </Button>
        </Stack>
      </Box>

      <Stack spacing={3}>
        {features.map((f) => (
          <Card key={f.title} sx={{ display: "flex", alignItems: "center", p: 1 }}>
            <Box sx={{ p: 2, color: "primary.main" }}>{f.icon}</Box>
            <CardContent>
              <Typography variant="h6">{f.title}</Typography>
              <Typography variant="body2" color="text.secondary">
                {f.desc}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Container>
  );
}
