import { Router } from 'express';
import { consultar } from '../db.js';
import { ahoraPeru, fechaValida, sumarHoras } from '../servicios/tiempo.js';
import { armarSegmentos, estadoActual } from '../servicios/actividad.js';

export const rutasFlota = Router();

/** Estado actual de cada embarcación. */
export async function flotaActual() {
  const ahora = ahoraPeru();
  const filas = await consultar('flota_actual.sql', { ahora });
  return { ahora, embarcaciones: filas.map(estadoActual) };
}

// GET /api/flota/actual
rutasFlota.get('/actual', async (req, res, next) => {
  try { res.json(await flotaActual()); } catch (e) { next(e); }
});

// GET /api/flota/bitacora?desde=2026-04-20&hasta=2026-04-25   (por defecto: últimas 120 h)
rutasFlota.get('/bitacora', async (req, res, next) => {
  try {
    const hasta = req.query.hasta ? fechaValida(req.query.hasta, 'hasta') : ahoraPeru();
    const desde = req.query.desde ? fechaValida(req.query.desde, 'desde') : sumarHoras(hasta, -120);
    const filas = await consultar('bitacora.sql', { desde, hasta });
    res.json({ desde, hasta, embarcaciones: armarSegmentos(filas) });
  } catch (e) { next(e); }
});
