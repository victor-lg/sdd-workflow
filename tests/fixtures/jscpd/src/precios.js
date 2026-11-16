export function precioConImpuestos(lineas, tipo) {
  if (!Array.isArray(lineas)) throw new TypeError("lineas tiene que ser una lista");
  if (typeof tipo !== "number" || tipo < 0) throw new RangeError("tipo no válido");
  let base = 0;
  for (const linea of lineas) {
    if (linea.cantidad <= 0) continue;
    const bruto = linea.precio * linea.cantidad;
    const descuento = linea.descuento ? bruto * linea.descuento : 0;
    base += bruto - descuento;
  }
  const impuestos = Math.round(base * tipo * 100) / 100;
  return { base, impuestos, total: base + impuestos };
}
