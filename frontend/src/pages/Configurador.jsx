import { useNavigate } from "react-router-dom";
import { styled } from "@mui/material/styles";
import {
  Box,
  Container,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
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

const CenteredConnector = styled(StepConnector)(({ theme }) => ({
  "&.MuiStepConnector-alternativeLabel": {
    top: 12,
  },
  "& .MuiStepConnector-line": {
    borderColor: theme.palette.divider,
  },
}));

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
    <Box sx={{ pb: isLastStep ? 0 : 9 }}>
      <Container maxWidth="md" sx={{ pt: 4 }}>
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
      </Container>

      <Container maxWidth="xl">
        <Stepper
          activeStep={activeStep}
          alternativeLabel
          connector={<CenteredConnector />}
          sx={{ mb: 4 }}
        >
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Container>

      <Container maxWidth="md" sx={{ pb: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => useConfigStore.setState({ error: null })}>
            {error}
          </Alert>
        )}

        <Box sx={{ minHeight: 300 }}>{renderStep()}</Box>
      </Container>

      {!isLastStep && (
        <Box
          sx={{
            position: "sticky",
            bottom: 0,
            bgcolor: "background.paper",
            borderTop: 1,
            borderColor: "divider",
            py: 1.5,
            zIndex: 10,
          }}
        >
          <Container maxWidth="md">
            <Stack direction="row" justifyContent="space-between">
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
          </Container>
        </Box>
      )}
    </Box>
  );
}
