import { Router } from 'express';
import { consultar } from '../db.js';
import { ahoraPeru, fechaValida, sumarHoras } from '../servicios/tiempo.js';
import { armarSegmentos } from '../servicios/actividad.js';

export const rutasEmbarcaciones = Router();

// GET /api/embarcaciones/CUZCO%204/registros?desde=...&hasta=...   (por defecto: últimas 48 h)
rutasEmbarcaciones.get('/:ep/registros', async (req, res, next) => {
  try {
    const ep = String(req.params.ep).trim().toUpperCase().slice(0, 50);
    const hasta = req.query.hasta ? fechaValida(req.query.hasta, 'hasta') : ahoraPeru();
    const desde = req.query.desde ? fechaValida(req.query.desde, 'desde') : sumarHoras(hasta, -48);
    const registros = await consultar('registros_embarcacion.sql', { ep, desde, hasta });
    const segmentos = armarSegmentos(registros.map((r) => ({ ...r, Embarcacion: ep })))[0]?.segmentos ?? [];
    res.json({ ep, desde, hasta, registros, segmentos });
  } catch (e) { next(e); }
});
