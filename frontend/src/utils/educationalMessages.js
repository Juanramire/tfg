/**
 * Reglas educativas para notificaciones contextuales.
 *
 * Cada regla puede usar:
 *  - anyOf:          se activa si AL MENOS UNA feature está en excluded
 *  - allOf:          se activa solo si TODAS están en excluded
 *  - noneOf:         NO se activa si alguna de estas está en excluded
 *  - requiresAnySelected: solo se activa si al menos una de estas está en selected
 */
const RULES = {
  Procesador: [
    {
      anyOf: ["Intel"],
      message:
        "Has elegido un procesador AMD. Necesitarás una placa base con socket AMD (AM4 o AM5).",
    },
    {
      anyOf: ["AMD"],
      message:
        "Has elegido un procesador Intel. Necesitarás una placa base con socket Intel (LGA1700 o LGA1851).",
    },
  ],

  PlacaBase: [
    {
      allOf: ["LGA1700", "LGA1851"],
      message:
        "Has elegido un procesador AMD. Solo se muestran placas base con socket AMD (AM4 o AM5).",
    },
    {
      allOf: ["AM4", "AM5"],
      message:
        "Has elegido un procesador Intel. Solo se muestran placas base con socket Intel (LGA1700 o LGA1851).",
    },
  ],

  MemoriaRAM: [
    {
      anyOf: ["DDR4"],
      requiresAnySelected: ["AM5", "LGA1851"],
      message:
        "Tu procesador y placa base solo admiten memoria DDR5. Las opciones DDR4 no están disponibles.",
    },
    {
      anyOf: ["DDR5"],
      requiresAnySelected: ["AM4"],
      message:
        "Tu procesador y placa base solo admiten memoria DDR4. Las opciones DDR5 no están disponibles.",
    },
    {
      // Edicion excluye RAM_8GB y RAM_16GB → necesita 32 GB
      allOf: ["RAM_8GB", "RAM_16GB"],
      requiresAnySelected: ["Edicion"],
      message:
        "El perfil Edición requiere al menos 32 GB de RAM para edición de vídeo y renderizado.",
    },
    {
      // Gaming / Programación excluyen solo RAM_8GB → necesita 16 GB
      anyOf: ["RAM_8GB"],
      noneOf: ["RAM_16GB"],
      requiresAnySelected: ["Gaming", "Programacion"],
      message:
        "Tu perfil de uso requiere al menos 16 GB de RAM para un rendimiento adecuado.",
    },
  ],

  TarjetaGrafica: [
    {
      anyOf: ["Gaming"],
      requiresAnySelected: ["Ofimatica"],
      message:
        "Para ofimática, una GPU dedicada no es necesaria. Si tu procesador incluye gráficos integrados, puedes pasar al siguiente paso.",
    },
    {
      anyOf: ["GPU_Gama_Baja"],
      requiresAnySelected: ["Gaming"],
      message:
        "El perfil Gaming requiere una GPU de gama media o alta para cumplir los requisitos de rendimiento.",
    },
  ],

  FuenteAlimentacion: [
    {
      allOf: ["PSU_500W", "PSU_650W"],
      requiresAnySelected: ["GPU_Gama_Alta"],
      message:
        "Tu GPU de gama alta consume mucha energía. Se necesita una fuente de al menos 750W para garantizar la estabilidad del sistema.",
    },
    {
      anyOf: ["PSU_500W"],
      noneOf: ["PSU_650W"],
      requiresAnySelected: ["GPU_Gama_Media"],
      message:
        "Tu tarjeta gráfica de gama media necesita una fuente de alimentación de al menos 650W para funcionar correctamente.",
    },
  ],

  Chasis: [
    {
      allOf: ["Caja_MicroATX", "Caja_MiniITX"],
      requiresAnySelected: ["Placa_ATX"],
      message:
        "Has elegido una placa base ATX. Este formato solo cabe en cajas ATX.",
    },
    {
      anyOf: ["Caja_MiniITX"],
      noneOf: ["Caja_MicroATX"],
      requiresAnySelected: ["Placa_MicroATX"],
      message:
        "Has elegido una placa base Micro-ATX. Este formato solo cabe en cajas ATX o Micro-ATX.",
    },
    {
      anyOf: ["Caja_MiniITX"],
      noneOf: ["Caja_MicroATX"],
      requiresAnySelected: ["GPU_Gama_Alta"],
      message:
        "Has elegido una GPU de gama alta. Las cajas Mini-ITX no tienen espacio suficiente — elige una caja ATX o Micro-ATX.",
    },
    {
      anyOf: ["Caja_MiniITX"],
      noneOf: ["Caja_MicroATX"],
      requiresAnySelected: ["Intel_Gama_Alta", "AMD_Gama_Alta"],
      message:
        "Tu procesador de gama alta necesita refrigeración líquida, que no cabe en una caja Mini-ITX. Elige una caja ATX o Micro-ATX.",
    },
  ],

  Refrigeracion: [
    {
      anyOf: ["Refrigeracion_Aire"],
      requiresAnySelected: ["Intel_Gama_Alta", "AMD_Gama_Alta"],
      message:
        "Los procesadores de gama alta generan mucho calor. La refrigeración líquida es necesaria para mantener temperaturas seguras y estables.",
    },
    {
      anyOf: ["Refrigeracion_Liquida"],
      requiresAnySelected: ["Caja_MiniITX"],
      message:
        "Con una caja Mini-ITX, la refrigeración líquida no está disponible. Solo se muestran opciones de refrigeración por aire.",
    },
  ],
};

export function getMessages(categoria, excluded, selected = []) {
  const rules = RULES[categoria];
  if (!rules || excluded.length === 0) return [];

  const excludedSet = new Set(excluded);
  const selectedSet = new Set(selected);
  const seen = new Set();
  const messages = [];

  for (const rule of rules) {
    const triggered = rule.allOf
      ? rule.allOf.every((f) => excludedSet.has(f))
      : rule.anyOf.some((f) => excludedSet.has(f));

    const blocked = rule.noneOf?.some((f) => excludedSet.has(f)) ?? false;

    const requirementMet =
      !rule.requiresAnySelected ||
      rule.requiresAnySelected.some((f) => selectedSet.has(f));

    if (triggered && !blocked && requirementMet && !seen.has(rule.message)) {
      seen.add(rule.message);
      messages.push(rule.message);
    }
  }

  return messages;
}
