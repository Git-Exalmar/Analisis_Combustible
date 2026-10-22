import cors from 'cors';
import express from 'express';
import { config } from './config.js';
import { consultar } from './db.js';
import { rutasFlota } from './rutas/flota.js';
import { rutasEmbarcaciones } from './rutas/embarcaciones.js';
import { rutasStream, sseClientes } from './rutas/stream.js';
import { ahoraPeru } from './servicios/tiempo.js';

export const app = express();
app.disable('x-powered-by');
app.use(cors({ origin: config.corsOrigin }));
app.use(express.json());

// GET /api/salud: ¿la API está viva y llega a la base? ¿cuándo corrió el último scoring?
app.get('/api/salud', async (req, res) => {
  try {
    const [proceso] = await consultar('ultimo_proceso.sql');
    res.json({ ok: true, ahora: ahoraPeru(), modoDemo: Boolean(config.ahoraFijo), ultimoProceso: proceso ?? null, clientesSse: sseClientes() });
  } catch (e) {
    res.status(503).json({ ok: false, error: 'Sin conexión a la base' });
  }
});

app.use('/api/flota', rutasFlota);
app.use('/api/embarcaciones', rutasEmbarcaciones);
app.use('/api/stream', rutasStream);

app.use((req, res) => res.status(404).json({ error: `No existe ${req.method} ${req.path}` }));

// Errores: al navegador solo un mensaje general; el detalle queda en el log del servidor
app.use((err, req, res, next) => {
  const status = err.status ?? 500;
  if (status >= 500) console.error('[error]', err);
  res.status(status).json({ error: status < 500 ? err.message : 'Error interno del servidor' });
});
