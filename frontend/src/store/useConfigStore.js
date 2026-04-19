import { create } from "zustand";
import { propagate, getProductos, generarPorPerfil } from "../services/api";

const useConfigStore = create((set, get) => ({
  // State
  activeStep: 0,
  perfil: null,
  presupuesto: 1000,
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

  // Steps
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

  // Category mapping for each step
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

  // Select a feature and propagate constraints
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

  // Deselect a feature
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

  // Load products for a category, filtered by valid features
  // Uses features from OTHER categories only, so the user can freely change their mind
  loadProductos: async (categoria) => {
    const state = get();
    set({ loading: true });

    try {
      // Build selected features from OTHER categories only (not the current one)
      const otherFeatures = Object.entries(state.componentesElegidos)
        .filter(([cat]) => cat !== categoria)
        .flatMap(([, p]) => p.features);

      // Add profile features if any
      const profileFeatures = state.perfil ? [state.perfil] : [];
      const selectedForPropagation = [...new Set([...otherFeatures, ...profileFeatures])];

      // Propagate without current category's features
      const result = await propagate(selectedForPropagation, state.deselected);
      const validFeatures = new Set([...result.forced, ...result.selectable]);

      // Get all products for this category
      const { productos } = await getProductos(categoria);

      // Filter: product features must be subset of valid features
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

  // Choose a specific product for a category (click again to deselect)
  elegirProducto: async (categoria, producto) => {
    const state = get();
    const yaElegido = state.componentesElegidos[categoria]?.nombre === producto.nombre;

    // Build features from all OTHER categories
    const otherFeatures = Object.entries(state.componentesElegidos)
      .filter(([cat]) => cat !== categoria)
      .flatMap(([, p]) => p.features);

    const profileFeatures = state.perfil ? [state.perfil] : [];

    let newComponentes;
    let newSelected;

    if (yaElegido) {
      // Deselect: remove this category from chosen components
      newComponentes = Object.fromEntries(
        Object.entries(state.componentesElegidos).filter(([cat]) => cat !== categoria)
      );
      newSelected = [...new Set([...otherFeatures, ...profileFeatures])];
    } else {
      // Select new product
      newComponentes = { ...state.componentesElegidos, [categoria]: producto };
      newSelected = [...new Set([...otherFeatures, ...producto.features, ...profileFeatures])];
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

  // Generate a complete config from profile + budget
  generarConfigAuto: async () => {
    const state = get();
    if (!state.perfil) return;
    set({ loading: true, error: null });

    try {
      const resultado = await generarPorPerfil(state.perfil, state.presupuesto);

      // Map components to componentesElegidos by category
      const elegidos = {};
      const allFeatures = [];
      for (const comp of resultado.componentes) {
        elegidos[comp.categoria] = comp.producto;
        allFeatures.push(...comp.producto.features);
      }

      // Propagate with all selected features
      const result = await propagate(allFeatures, state.deselected);

      set({
        componentesElegidos: elegidos,
        selected: allFeatures,
        forced: result.forced,
        excluded: result.excluded,
        selectable: result.selectable,
        avisos: resultado.avisos,
        activeStep: state.steps.length - 1, // Go to summary
        loading: false,
      });

      return resultado;
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  // Get total price of chosen components
  getPrecioTotal: () => {
    const state = get();
    return Object.values(state.componentesElegidos).reduce(
      (sum, p) => sum + p.precio,
      0
    );
  },

  // Reset everything
  reset: () =>
    set({
      activeStep: 0,
      perfil: null,
      presupuesto: 1000,
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
