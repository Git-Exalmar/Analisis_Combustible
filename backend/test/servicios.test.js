// Pruebas sin base de datos: npm test
import assert from 'node:assert/strict';
import { test } from 'node:test';

process.env.LIMITE_SIN_DATOS_MIN = '60';
const { armarSegmentos, estadoActual } = await import('../src/servicios/actividad.js');
const { sumarHoras, fechaValida } = await import('../src/servicios/tiempo.js');

const fila = (ep, h, act) => ({ Embarcacion: ep, FechaRegistro: `2026-04-25T${h}:00`, Actividad: act });

test('une registros seguidos con la misma actividad', () => {
  const r = armarSegmentos([
    fila('A', '10:00', 'ida'), fila('A', '10:15', 'ida'), fila('A', '10:30', 'busqueda'),
    fila('A', '10:45', 'busqueda'), fila('A', '11:00', 'cala'),
  ]);
  assert.deepEqual(r[0].segmentos.map((s) => [s.actividad, s.ini.slice(11, 16), s.fin.slice(11, 16), s.registros]), [
    ['ida', '10:00', '10:30', 2], ['busqueda', '10:30', '11:00', 2], ['cala', '11:00', '11:15', 1],
  ]);
});

test('corta el segmento si hay un hueco de más de 45 min', () => {
  const r = armarSegmentos([fila('A', '10:00', 'ida'), fila('A', '12:00', 'ida')]);
  assert.equal(r[0].segmentos.length, 2);
  assert.equal(r[0].segmentos[0].fin, '2026-04-25T10:15:00');
});

test('separa embarcaciones', () => {
  const r = armarSegmentos([fila('A', '10:00', 'ida'), fila('B', '10:15', 'ida')]);
  assert.deepEqual(r.map((e) => e.ep), ['A', 'B']);
});

test('sin datos y posible entrada', () => {
  assert.equal(estadoActual({ Actividad: 'cala', MinDesdeUltimo: 300 }).actividadMostrada, 'sin_datos');
  assert.equal(estadoActual({ Actividad: 'entrada_cala', MinDesdeUltimo: 10 }).actividadMostrada, 'posible_entrada');
  assert.equal(estadoActual({ Actividad: 'cala', MinDesdeUltimo: 10 }).actividadMostrada, 'cala');
});

test('fechas: suma horas sin depender de la zona del servidor y rechaza texto inválido', () => {
  assert.equal(sumarHoras('2026-04-25T14:00:00', -120), '2026-04-20T14:00:00');
  assert.equal(sumarHoras('2026-04-25', 24), '2026-04-26T00:00:00');
  assert.throws(() => fechaValida("2026-04-25'; DROP TABLE x--", 'desde'));
});
