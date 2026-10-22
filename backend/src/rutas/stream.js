// Server-Sent Events: el panel abre UNA conexión y el servidor le avisa cuando hay datos nuevos.
// Un solo "vigilante" revisa la base cada N segundos y reparte a todos los navegadores conectados
// (si cada navegador consultara la base por su cuenta, 50 usuarios serían 50 consultas).
import { Router } from 'express';
import { config } from '../config.js';
import { consultar } from '../db.js';
import { flotaActual } from './flota.js';

export const rutasStream = Router();
const clientes = new Set();
let ultimoIdProceso = null;
let vigilante = null;

function enviar(res, evento, datos) {
  res.write(`event: ${evento}\ndata: ${JSON.stringify(datos)}\n\n`);
}

async function revisar() {
  try {
    const [proc] = await consultar('ultimo_proceso.sql');
    if (!proc || proc.IdProceso === ultimoIdProceso) return;
    ultimoIdProceso = proc.IdProceso;
    const flota = await flotaActual();
    for (const res of clientes) enviar(res, 'flota', { proceso: proc, ...flota });
  } catch (e) {
    for (const res of clientes) enviar(res, 'error', { mensaje: 'No se pudo consultar la base' });
    console.error('[sse]', e.message);
  }
}

function iniciarVigilante() {
  if (vigilante) return;
  vigilante = setInterval(revisar, config.intervaloSseSeg * 1000);
}

function detenerVigilanteSiNoHayClientes() {
  if (clientes.size === 0 && vigilante) {
    clearInterval(vigilante);
    vigilante = null;
    ultimoIdProceso = null;
  }
}

// GET /api/stream
rutasStream.get('/', async (req, res) => {
  res.set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  res.flushHeaders();
  clientes.add(res);
  iniciarVigilante();

  // Al conectarse recibe el estado actual de inmediato, sin esperar al próximo proceso
  try { enviar(res, 'flota', await flotaActual()); } catch { enviar(res, 'error', { mensaje: 'No se pudo consultar la base' }); }

  // Comentario cada 25 s para que proxies y balanceadores no corten la conexión por inactividad
  const latido = setInterval(() => res.write(': latido\n\n'), 25000);
  req.on('close', () => {
    clearInterval(latido);
    clientes.delete(res);
    detenerVigilanteSiNoHayClientes();
  });
});

export const sseClientes = () => clientes.size;
