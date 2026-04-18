import { Stack, Tooltip, IconButton, Typography } from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";

const STORES = [
  {
    label: "PcComponentes",
    color: "#e8393e",
    url: (name) =>
      `https://www.pccomponentes.com/buscar/?query=${encodeURIComponent(name)}`,
  },
  {
    label: "Amazon",
    color: "#ff9900",
    url: (name) =>
      `https://www.amazon.es/s?k=${encodeURIComponent(name)}`,
  },
];

export default function PriceLinks({ nombre, size = "small" }) {
  const handleClick = (e, url) => {
    e.stopPropagation();
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <Stack direction="row" spacing={0.5} alignItems="center">
      {STORES.map(({ label, color, url }) => (
        <Tooltip key={label} title={`Buscar en ${label}`} placement="top">
          <IconButton
            size={size}
            onClick={(e) => handleClick(e, url(nombre))}
            sx={{ color, p: 0.5 }}
          >
            <Stack direction="row" alignItems="center" spacing={0.3}>
              <Typography variant="caption" sx={{ color, fontWeight: "bold", fontSize: "0.65rem" }}>
                {label === "PcComponentes" ? "PCC" : "AMZ"}
              </Typography>
              <OpenInNewIcon sx={{ fontSize: "0.75rem" }} />
            </Stack>
          </IconButton>
        </Tooltip>
      ))}
    </Stack>
  );
}
