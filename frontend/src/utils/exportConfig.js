import { jsPDF } from "jspdf";

export function exportJSON(componentesElegidos, presupuesto, perfil) {
  const componentes = Object.entries(componentesElegidos).map(([categoria, p]) => ({
    categoria,
    nombre: p.nombre,
    marca: p.marca,
    precio: p.precio,
    specs: p.specs,
  }));

  const precioTotal = componentes.reduce((s, c) => s + c.precio, 0);

  const data = {
    fecha: new Date().toLocaleDateString("es-ES"),
    perfil: perfil || null,
    presupuesto: presupuesto ?? null,
    precio_total: Math.round(precioTotal * 100) / 100,
    ahorro: presupuesto !== null ? Math.max(0, Math.round((presupuesto - precioTotal) * 100) / 100) : null,
    componentes,
  };

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `configuracion-pc-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function exportPDF(componentesElegidos, presupuesto, perfil) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const W = 210;
  const margin = 20;
  const colW = W - margin * 2;
  let y = 20;

  const addLine = (text, size = 10, bold = false, color = [30, 30, 30]) => {
    doc.setFontSize(size);
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setTextColor(...color);
    doc.text(text, margin, y);
    y += size * 0.5 + 2;
  };

  const addDivider = () => {
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, y, W - margin, y);
    y += 4;
  };

  // Cabecera
  doc.setFillColor(10, 25, 41);
  doc.rect(0, 0, W, 30, "F");
  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(144, 202, 249);
  doc.text("Configuración de PC", margin, 13);
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(180, 200, 220);
  doc.text(`Generado el ${new Date().toLocaleDateString("es-ES")}`, margin, 22);
  y = 40;

  // Info general
  if (perfil) addLine(`Perfil: ${perfil}`, 11, true, [90, 170, 249]);
  if (presupuesto !== null) addLine(`Presupuesto: ${presupuesto.toFixed(2)} €`, 10);
  y += 4;
  addDivider();

  // Componentes
  addLine("Componentes seleccionados", 12, true);
  y += 2;

  const componentes = Object.entries(componentesElegidos);
  let precioTotal = 0;

  componentes.forEach(([categoria, p]) => {
    if (y > 260) { doc.addPage(); y = 20; }

    doc.setFillColor(20, 40, 60);
    doc.roundedRect(margin, y - 4, colW, 18, 2, 2, "F");

    doc.setFontSize(8);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(144, 202, 249);
    doc.text(categoria.toUpperCase(), margin + 3, y + 2);

    doc.setFontSize(10);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(230, 230, 230);
    doc.text(p.nombre, margin + 3, y + 8);

    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(144, 202, 249);
    doc.text(`${p.precio.toFixed(2)} €`, W - margin - 3, y + 8, { align: "right" });

    y += 22;
    precioTotal += p.precio;
  });

  y += 2;
  addDivider();

  // Totales
  const dentroPresupuesto = presupuesto !== null && precioTotal <= presupuesto;
  addLine("TOTAL", 12, true);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  const colorTotal = presupuesto === null ? [230, 230, 230] : dentroPresupuesto ? [76, 175, 80] : [244, 67, 54];
  doc.setTextColor(...colorTotal);
  doc.text(`${precioTotal.toFixed(2)} €`, W - margin, y - 6, { align: "right" });

  y += 4;
  if (presupuesto !== null) {
    if (dentroPresupuesto) {
      addLine(`Ahorro: ${(presupuesto - precioTotal).toFixed(2)} €`, 10, false, [76, 175, 80]);
    } else {
      addLine(`Excede el presupuesto en: ${(precioTotal - presupuesto).toFixed(2)} €`, 10, false, [244, 67, 54]);
    }
  }

  doc.save(`configuracion-pc-${Date.now()}.pdf`);
}
