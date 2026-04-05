import { useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Stack,
  Alert,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import useConfigStore from "../store/useConfigStore";
import StepPerfil from "../components/StepPerfil";
import StepComponente from "../components/StepComponente";
import StepResumen from "../components/StepResumen";

export default function Configurador() {
  const navigate = useNavigate();
  const {
    activeStep,
    steps,
    stepCategoria,
    nextStep,
    prevStep,
    error,
    loading,
    reset,
  } = useConfigStore();

  const handleReset = () => {
    reset();
    navigate("/");
  };

  const renderStep = () => {
    if (activeStep === 0) return <StepPerfil />;
    if (activeStep === steps.length - 1) return <StepResumen />;

    const categoria = stepCategoria[activeStep];
    if (!categoria) return null;

    return <StepComponente categoria={categoria} />;
  };

  const isLastStep = activeStep === steps.length - 1;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack direction="row" alignItems="center" spacing={2} mb={3}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={handleReset}
          color="inherit"
        >
          Inicio
        </Button>
        <Typography variant="h5" fontWeight="bold" flex={1}>
          Configurador de PC
        </Typography>
      </Stack>

      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => useConfigStore.setState({ error: null })}>
          {error}
        </Alert>
      )}

      <Box sx={{ minHeight: 300 }}>{renderStep()}</Box>

      {!isLastStep && (
        <Stack direction="row" justifyContent="space-between" mt={4}>
          <Button
            disabled={activeStep === 0}
            onClick={prevStep}
            variant="outlined"
          >
            Anterior
          </Button>
          <Button
            onClick={nextStep}
            variant="contained"
            disabled={loading}
          >
            Siguiente
          </Button>
        </Stack>
      )}
    </Container>
  );
}
