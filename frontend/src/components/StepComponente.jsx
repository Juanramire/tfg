import { useEffect } from "react";
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Typography,
  Stack,
  Chip,
  Alert,
  CircularProgress,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import useConfigStore from "../store/useConfigStore";

const LABELS = {
  Procesador: "Elige un procesador",
  PlacaBase: "Elige una placa base",
  MemoriaRAM: "Elige la memoria RAM",
  TarjetaGrafica: "Elige una tarjeta gráfica",
  Almacenamiento: "Elige almacenamiento",
  FuenteAlimentacion: "Elige la fuente de alimentación",
  Chasis: "Elige la caja",
  Refrigeracion: "Elige la refrigeración",
};

const FEATURE_LABELS = {
  Intel: "Intel",
  AMD: "AMD",
  LGA1700: "LGA 1700",
  LGA1851: "LGA 1851",
  AM4: "AM4",
  AM5: "AM5",
  DDR4: "DDR4",
  DDR5: "DDR5",
  GPU_Gama_Baja: "Gama Baja",
  GPU_Gama_Media: "Gama Media",
  GPU_Gama_Alta: "Gama Alta",
  Placa_ATX: "ATX",
  Placa_MicroATX: "Micro-ATX",
  Placa_MiniITX: "Mini-ITX",
  Caja_ATX: "ATX",
  Caja_MicroATX: "Micro-ATX",
  Caja_MiniITX: "Mini-ITX",
  PSU_500W: "500W",
  PSU_650W: "650W",
  PSU_750W: "750W",
  PSU_850W: "850W",
  SSD_NVMe: "NVMe",
  SSD_SATA: "SATA",
  Disco_HDD: "HDD",
  Refrigeracion_Aire: "Aire",
  Refrigeracion_Liquida: "Líquida",
  RAM_8GB: "8 GB",
  RAM_16GB: "16 GB",
  RAM_32GB: "32 GB",
  RAM_64GB: "64 GB",
};

function formatSpecs(specs) {
  const parts = [];
  if (specs.nucleos) parts.push(`${specs.nucleos} núcleos`);
  if (specs.frecuencia_boost) parts.push(`hasta ${specs.frecuencia_boost}`);
  if (specs.tdp) parts.push(`${specs.tdp}W TDP`);
  if (specs.vram) parts.push(specs.vram);
  if (specs.capacidad) parts.push(specs.capacidad);
  if (specs.velocidad) parts.push(specs.velocidad);
  if (specs.modulos) parts.push(specs.modulos);
  if (specs.lectura) parts.push(`Lectura: ${specs.lectura}`);
  if (specs.certificacion) parts.push(specs.certificacion);
  if (specs.tipo_radiador) parts.push(`Radiador ${specs.tipo_radiador}`);
  return parts.join(" · ");
}

export default function StepComponente({ categoria }) {
  const {
    productosPorCategoria,
    componentesElegidos,
    excluded,
    loading,
    loadProductos,
    elegirProducto,
    selectFeature,
  } = useConfigStore();

  const productos = productosPorCategoria[categoria] || [];
  const elegido = componentesElegidos[categoria];
  const isGPU = categoria === "TarjetaGrafica";
  const gpuExcluida = excluded.includes("TarjetaGrafica");

  useEffect(() => {
    loadProductos(categoria);
  }, [categoria, excluded.length, loadProductos]);

  const handleSelect = async (producto) => {
    elegirProducto(categoria, producto);
    for (const f of producto.features) {
      await selectFeature(f);
    }
  };

  if (isGPU && gpuExcluida) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Tarjeta Gráfica
        </Typography>
        <Alert severity="info">
          Tu configuración no requiere tarjeta gráfica dedicada. El procesador
          incluye gráficos integrados.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {LABELS[categoria] || categoria}
      </Typography>

      {loading && productos.length === 0 && (
        <Box textAlign="center" py={4}>
          <CircularProgress />
        </Box>
      )}

      {!loading && productos.length === 0 && (
        <Alert severity="warning">
          No hay productos compatibles con tu configuración actual.
        </Alert>
      )}

      <Stack spacing={2}>
        {productos.map((p) => {
          const isSelected = elegido?.nombre === p.nombre;
          return (
            <Card
              key={p.nombre}
              sx={{
                border: isSelected ? 2 : 0,
                borderColor: "primary.main",
                opacity: isSelected ? 1 : 0.85,
              }}
            >
              <CardActionArea onClick={() => handleSelect(p)}>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box flex={1}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {p.nombre}
                        </Typography>
                        {isSelected && <CheckCircleIcon color="primary" fontSize="small" />}
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {formatSpecs(p.specs)}
                      </Typography>
                      <Stack direction="row" spacing={0.5} mt={1} flexWrap="wrap" useFlexGap>
                        {p.features.map((f) => (
                          <Chip
                            key={f}
                            label={FEATURE_LABELS[f] || f}
                            size="small"
                            variant="outlined"
                            color={excluded.includes(f) ? "error" : "default"}
                          />
                        ))}
                      </Stack>
                    </Box>
                    <Typography variant="h6" color="primary" sx={{ ml: 2, whiteSpace: "nowrap" }}>
                      {p.precio.toFixed(2)}€
                    </Typography>
                  </Stack>
                </CardContent>
              </CardActionArea>
            </Card>
          );
        })}
      </Stack>
    </Box>
  );
}
