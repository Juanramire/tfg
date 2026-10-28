const API_ROOT = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const API_BASE = `${API_ROOT}/api`;

// El backend está en el plan gratuito de Render y se duerme tras 15 min sin
// tráfico. Si una petición tarda más de SLOW_START_MS antes de que el servidor
// haya respondido alguna vez, se avisa al usuario de que está arrancando.
export const SLOW_START_MS = 3000;

let servidorRespondio = false;
let arrancando = false;
let pendientes = 0;
const suscriptores = new Set();

function setArrancando(valor) {
  if (arrancando === valor) return;
  arrancando = valor;
  suscriptores.forEach((fn) => fn());
}

export const suscribirArranque = (fn) => {
  suscriptores.add(fn);
  return () => suscriptores.delete(fn);
};
export const isServidorArrancando = () => arrancando;

async function vigilarArranque(peticion) {
  if (servidorRespondio) return peticion;
  pendientes++;
  const timer = setTimeout(() => {
    if (!servidorRespondio) setArrancando(true);
  }, SLOW_START_MS);
  try {
    const res = await peticion;
    servidorRespondio = true;
    return res;
  } finally {
    clearTimeout(timer);
    pendientes--;
    if (servidorRespondio || pendientes === 0) setArrancando(false);
  }
}

// Petición ligera para despertar el backend; los errores se ignoran.
export const despertarServidor = () =>
  vigilarArranque(fetch(`${API_ROOT}/health`)).catch(() => {});

async function fetchAPI(endpoint, options = {}) {
  const res = await vigilarArranque(
    fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    })
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// Features (árbol de características)
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

// Productos (catálogo)
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
export const consultaIA = (consulta) =>
  fetchAPI("/configuracion/consulta", {
    method: "POST",
    body: JSON.stringify({ consulta }),
  });
