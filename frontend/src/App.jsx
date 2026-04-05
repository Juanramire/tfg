import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import Landing from "./pages/Landing";
import Configurador from "./pages/Configurador";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#90caf9" },
    secondary: { main: "#f48fb1" },
    background: { default: "#0a1929", paper: "#132f4c" },
  },
  typography: {
    fontFamily: "'Segoe UI', Roboto, sans-serif",
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/configurar" element={<Configurador />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
