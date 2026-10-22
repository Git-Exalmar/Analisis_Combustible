// Reglas de negocio para mostrar la actividad (se decidieron con el análisis del modelo).
import { config } from '../config.js';

const MIN_POR_REGISTRO = 15;   // Perú Controls envía un registro cada ~15 min
const HUECO_MAX_MIN = 45;      // si pasan más de 45 min entre registros, se corta el segmento

/** Qué se muestra en el panel para el último registro de una embarcación. */
export function estadoActual(fila) {
  const sinDatos = fila.MinDesdeUltimo > config.limiteSinDatosMin;
  let mostrada = fila.Actividad;
  if (sinDatos) mostrada = 'sin_datos';
  // Precisión de "entrada a cala" ≈ 0.34 en tiempo real: se muestra como posible
  else if (fila.Actividad === 'entrada_cala') mostrada = 'posible_entrada';
  return { ...fila, sinDatos, actividadMostrada: mostrada };
}

const minutos = (a, b) => (Date.parse(`${b}Z`) - Date.parse(`${a}Z`)) / 60000;
const masMinutos = (iso, m) => new Date(Date.parse(`${iso}Z`) + m * 60000).toISOString().slice(0, 19);

/** Une registros consecutivos con la misma actividad en segmentos {actividad, ini, fin, registros}.
 *  Espera filas ordenadas por Embarcacion y FechaRegistro. */
export function armarSegmentos(filas) {
  const porEp = new Map();
  for (const f of filas) {
    if (!porEp.has(f.Embarcacion)) porEp.set(f.Embarcacion, []);
    const segs = porEp.get(f.Embarcacion);
    const ult = segs.at(-1);
    const continuo = ult && minutos(ult.ultimoRegistro, f.FechaRegistro) <= HUECO_MAX_MIN;
    if (continuo) ult.fin = f.FechaRegistro;   // el segmento anterior llega hasta este registro
    if (continuo && ult.actividad === f.Actividad) {
      ult.ultimoRegistro = f.FechaRegistro;
      ult.fin = masMinutos(f.FechaRegistro, MIN_POR_REGISTRO);
      ult.registros += 1;
    } else {
      segs.push({
        actividad: f.Actividad,
        ini: f.FechaRegistro,
        fin: masMinutos(f.FechaRegistro, MIN_POR_REGISTRO),
        ultimoRegistro: f.FechaRegistro,
        registros: 1,
      });
    }
  }
  return [...porEp].map(([ep, segs]) => ({
    ep,
    segmentos: segs.map(({ ultimoRegistro, ...s }) => s),
  }));
}
