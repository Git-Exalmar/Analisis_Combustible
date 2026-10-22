// Todas las fechas de la API son HORA DE PERÚ, en texto ISO sin zona: "2026-04-25T14:00:00".
// Perú no cambia de horario (UTC−5). El servidor (Azure) trabaja en UTC.
import { config } from '../config.js';

const OFFSET_PERU_MS = -5 * 3600 * 1000;
const FORMATO = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$/;

export function ahoraPeru() {
  if (config.ahoraFijo) return config.ahoraFijo;
  return new Date(Date.now() + OFFSET_PERU_MS).toISOString().slice(0, 19);
}

/** Valida una fecha recibida en la URL. Devuelve el texto o lanza un error 400. */
export function fechaValida(texto, nombre) {
  if (!texto || !FORMATO.test(texto) || Number.isNaN(Date.parse(texto))) {
    const e = new Error(`Parámetro "${nombre}" inválido. Formato: AAAA-MM-DD o AAAA-MM-DDTHH:MM`);
    e.status = 400;
    throw e;
  }
  return texto;
}

/** Suma horas a una fecha ISO sin zona, sin que intervenga la zona horaria del servidor. */
export function sumarHoras(iso, horas) {
  const d = new Date(`${iso.length === 10 ? `${iso}T00:00:00` : iso}Z`);
  return new Date(d.getTime() + horas * 3600 * 1000).toISOString().slice(0, 19);
}
