import { create } from "zustand";
import { propagate, getProductos, generarPorPerfil, consultaIA } from "../services/api";

const useConfigStore = create((set, get) => ({
  // Estado
  activeStep: 0,
  perfil: null,
  presupuesto: null,
  selected: [],
  deselected: [],
  forced: [],
  excluded: [],
  selectable: [],
  productosPorCategoria: {},
  componentesElegidos: {},
  avisos: [],
  loading: false,
  error: null,

  // Pasos
  steps: [
    "Perfil",
    "Procesador",
    "Placa Base",
    "Memoria RAM",
    "Tarjeta Gráfica",
    "Almacenamiento",
    "Fuente",
    "Chasis",
    "Refrigeración",
    "Resumen",
  ],

  // Mapeo de categoría por cada paso
  stepCategoria: {
    1: "Procesador",
    2: "PlacaBase",
    3: "MemoriaRAM",
    4: "TarjetaGrafica",
    5: "Almacenamiento",
    6: "FuenteAlimentacion",
    7: "Chasis",
    8: "Refrigeracion",
  },

  nextStep: () => set((s) => ({ activeStep: Math.min(s.activeStep + 1, s.steps.length - 1) })),
  prevStep: () => set((s) => ({ activeStep: Math.max(s.activeStep - 1, 0) })),
  goToStep: (step) => set({ activeStep: step }),

  setPerfil: (perfil) => set({ perfil }),
  setPresupuesto: (presupuesto) => set({ presupuesto }),

  // Seleccionar una feature y propagar constraints
  selectFeature: async (feature) => {
    const state = get();
    const newSelected = [...new Set([...state.selected, feature])];
    const newDeselected = state.deselected.filter((f) => f !== feature);
    set({ selected: newSelected, deselected: newDeselected, loading: true, error: null });

    try {
      const result = await propagate(newSelected, newDeselected);
      set({
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        selected: newSelected,
        loading: false,
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Deseleccionar una feature
  deselectFeature: async (feature) => {
    const state = get();
    const newSelected = state.selected.filter((f) => f !== feature);
    const newDeselected = [...new Set([...state.deselected, feature])];
    set({ selected: newSelected, deselected: newDeselected, loading: true, error: null });

    try {
      const result = await propagate(newSelected, newDeselected);
      set({
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        loading: false,
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Carga productos de una categoría, filtrados por features válidas
  // Usa features de OTRAS categorías únicamente, para que el usuario pueda cambiar de opinión libremente
  loadProductos: async (categoria) => {
    const state = get();
    set({ loading: true });

    try {
      // Construir features seleccionadas de OTRAS categorías (no la actual)
      const otherFeatures = Object.entries(state.componentesElegidos)
        .filter(([cat]) => cat !== categoria)
        .flatMap(([, p]) => Array.isArray(p) ? p.flatMap((item) => item.features) : p.features);

      // Añadir features del perfil si existe
      const profileFeatures = state.perfil ? [state.perfil] : [];
      const selectedForPropagation = [...new Set([...otherFeatures, ...profileFeatures])];

      // Propagar sin las features de la categoría actual
      const result = await propagate(selectedForPropagation, state.deselected);
      const validFeatures = new Set([...result.forced, ...result.selectable]);

      // Obtener todos los productos de esta categoría
      const { productos } = await getProductos(categoria);

      // Filtrar: las features del producto deben ser un subconjunto de las válidas
      const compatibles = productos.filter((p) =>
        p.features.every((f) => validFeatures.has(f))
      );

      set((s) => ({
        productosPorCategoria: { ...s.productosPorCategoria, [categoria]: compatibles },
        loading: false,
      }));
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Elegir un producto concreto para una categoría (clic de nuevo para deseleccionar)
  // Almacenamiento admite varios productos (array); el resto solo admite uno.
  elegirProducto: async (categoria, producto) => {
    const state = get();

    // Construir features de todas las OTRAS categorías
    const otherFeatures = Object.entries(state.componentesElegidos)
      .filter(([cat]) => cat !== categoria)
      .flatMap(([, p]) => Array.isArray(p) ? p.flatMap((item) => item.features) : p.features);

    const profileFeatures = state.perfil ? [state.perfil] : [];

    let newComponentes;
    let newSelected;

    if (categoria === "Almacenamiento") {
      const current = Array.isArray(state.componentesElegidos["Almacenamiento"])
        ? state.componentesElegidos["Almacenamiento"]
        : state.componentesElegidos["Almacenamiento"]
          ? [state.componentesElegidos["Almacenamiento"]]
          : [];
      const yaElegido = current.some((p) => p.nombre === producto.nombre);
      const newArray = yaElegido
        ? current.filter((p) => p.nombre !== producto.nombre)
        : [...current, producto];

      if (newArray.length === 0) {
        newComponentes = Object.fromEntries(
          Object.entries(state.componentesElegidos).filter(([cat]) => cat !== "Almacenamiento")
        );
      } else {
        newComponentes = { ...state.componentesElegidos, Almacenamiento: newArray };
      }
      newSelected = [...new Set([...otherFeatures, ...newArray.flatMap((p) => p.features), ...profileFeatures])];
    } else {
      const yaElegido = state.componentesElegidos[categoria]?.nombre === producto.nombre;
      if (yaElegido) {
        newComponentes = Object.fromEntries(
          Object.entries(state.componentesElegidos).filter(([cat]) => cat !== categoria)
        );
        newSelected = [...new Set([...otherFeatures, ...profileFeatures])];
      } else {
        newComponentes = { ...state.componentesElegidos, [categoria]: producto };
        newSelected = [...new Set([...otherFeatures, ...producto.features, ...profileFeatures])];
      }
    }

    set({ componentesElegidos: newComponentes, selected: newSelected, loading: true });

    try {
      const result = await propagate(newSelected, state.deselected);
      set({
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        loading: false,
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Generar una configuración completa a partir de perfil + presupuesto
  generarConfigAuto: async () => {
    const state = get();
    if (!state.perfil) return;
    set({ loading: true, error: null });

    try {
      const resultado = await generarPorPerfil(state.perfil, state.presupuesto);

      // Mapear componentes a componentesElegidos por categoría
      const elegidos = {};
      const allFeatures = [];
      for (const comp of resultado.componentes) {
        if (comp.categoria === "Almacenamiento") {
          if (!elegidos["Almacenamiento"]) elegidos["Almacenamiento"] = [];
          elegidos["Almacenamiento"].push(comp.producto);
        } else {
          elegidos[comp.categoria] = comp.producto;
        }
        allFeatures.push(...comp.producto.features);
      }

      // Propagar con todas las features seleccionadas
      const result = await propagate(allFeatures, state.deselected);

      set({
        componentesElegidos: elegidos,
        selected: allFeatures,
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        avisos: resultado.avisos,
        activeStep: state.steps.length - 1, // Ir al resumen
        loading: false,
      });

      return resultado;
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Generar configuración a partir de una consulta en lenguaje natural vía Gemini
  consultarIA: async (consulta) => {
    set({ loading: true, error: null });
    try {
      const resultado = await consultaIA(consulta);

      const elegidos = {};
      const allFeatures = [];
      for (const comp of resultado.componentes) {
        if (comp.categoria === "Almacenamiento") {
          if (!elegidos["Almacenamiento"]) elegidos["Almacenamiento"] = [];
          elegidos["Almacenamiento"].push(comp.producto);
        } else {
          elegidos[comp.categoria] = comp.producto;
        }
        allFeatures.push(...comp.producto.features);
      }

      const result = await propagate(allFeatures, []);

      set({
        componentesElegidos: elegidos,
        selected: allFeatures,
        perfil: resultado.perfil || null,
        presupuesto: resultado.presupuesto,
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        avisos: resultado.avisos,
        activeStep: get().steps.length - 1,
        loading: false,
      });

      return resultado;
    } catch (err) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },

  // Obtener el precio total de los componentes elegidos
  getPrecioTotal: () => {
    const state = get();
    return Object.values(state.componentesElegidos).reduce(
      (sum, p) =>
        sum + (Array.isArray(p) ? p.reduce((s, item) => s + item.precio, 0) : p.precio),
      0
    );
  },

  // Resetear todo el estado
  reset: () =>
    set({
      activeStep: 0,
      perfil: null,
      presupuesto: null,
      selected: [],
      deselected: [],
      forced: [],
      excluded: [],
      selectable: [],
      productosPorCategoria: {},
      componentesElegidos: {},
      avisos: [],
      loading: false,
      error: null,
    }),
}));

export default useConfigStore;
