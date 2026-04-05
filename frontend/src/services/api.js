const API_BASE = "http://127.0.0.1:8000/api";

async function fetchAPI(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// Features
export const getFeatureTree = () => fetchAPI("/features/tree");
export const getModelInfo = () => fetchAPI("/features/info");
export const validateConfig = (selected) =>
  fetchAPI("/features/validate", {
    method: "POST",
    body: JSON.stringify({ selected }),
  });
export const propagate = (selected, deselected = []) =>
  fetchAPI("/features/propagate", {
    method: "POST",
    body: JSON.stringify({ selected, deselected }),
  });

// Productos
export const getProductos = (categoria, features) => {
  const params = new URLSearchParams();
  if (categoria) params.set("categoria", categoria);
  if (features?.length) params.set("features", features.join(","));
  return fetchAPI(`/productos/?${params}`);
};
export const getCategorias = () => fetchAPI("/productos/categorias");

// Configuración
export const generarPorPresupuesto = (presupuesto, selected = [], deselected = []) =>
  fetchAPI("/configuracion/presupuesto", {
    method: "POST",
    body: JSON.stringify({ presupuesto, selected, deselected }),
  });
export const generarPorPerfil = (perfil, presupuesto = null) =>
  fetchAPI("/configuracion/perfil", {
    method: "POST",
    body: JSON.stringify({ perfil, presupuesto }),
  });
export const getPerfiles = () => fetchAPI("/configuracion/perfiles");
