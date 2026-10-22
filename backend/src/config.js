// Configuración leída del .env. Nada de credenciales escritas en el código.
import 'dotenv/config';

function obligatoria(nombre) {
  const v = process.env[nombre];
  if (!v) throw new Error(`Falta la variable ${nombre} en el .env`);
  return v;
}

export const config = {
  puerto: Number(process.env.PORT ?? 3000),
  corsOrigin: process.env.CORS_ORIGIN ?? 'http://localhost:5173',
  limiteSinDatosMin: Number(process.env.LIMITE_SIN_DATOS_MIN ?? 60),
  intervaloSseSeg: Number(process.env.INTERVALO_SSE_SEG ?? 30),
  ahoraFijo: process.env.AHORA_FIJO || null,
  db: () => ({
    server: obligatoria('DB_SERVER'),
    database: process.env.DB_NAME ?? 'BD_TEL_FLOTA_PRD',
    user: obligatoria('DB_USER'),
    password: obligatoria('DB_PASS'),
    options: { encrypt: true, trustServerCertificate: false },
    pool: { max: 5, min: 0, idleTimeoutMillis: 30000 },
  }),
};
