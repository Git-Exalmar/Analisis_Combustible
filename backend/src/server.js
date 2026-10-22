import { app } from './app.js';
import { config } from './config.js';
import { cerrar } from './db.js';

const servidor = app.listen(config.puerto, () => {
  console.log(`API escuchando en http://localhost:${config.puerto}/api`);
  if (config.ahoraFijo) console.log(`MODO DEMO: la hora "actual" está fijada en ${config.ahoraFijo}`);
});

for (const senal of ['SIGINT', 'SIGTERM']) {
  process.on(senal, async () => {
    servidor.close();
    await cerrar();
    process.exit(0);
  });
}
