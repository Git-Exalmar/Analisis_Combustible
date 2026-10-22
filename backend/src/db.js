// Conexión a SQL Server: UN pool compartido por toda la API (abrir una conexión
// por petición sería lento). Las consultas viven en /sql, igual que en Python.
import { readFileSync } from 'node:fs';
import sql from 'mssql';
import { config } from './config.js';

const DIR_SQL = new URL('../sql/', import.meta.url);
const cache = new Map();
let pool = null;

function leerSql(nombre) {
  if (!cache.has(nombre)) cache.set(nombre, readFileSync(new URL(nombre, DIR_SQL), 'utf8'));
  return cache.get(nombre);
}

async function obtenerPool() {
  if (!pool) {
    pool = new sql.ConnectionPool(config.db());
    pool.on('error', () => { pool = null; });   // si se cae, se recrea en la siguiente consulta
    await pool.connect();
  }
  return pool;
}

/** Ejecuta un .sql con parámetros. Los valores SIEMPRE van como parámetros (@nombre),
 *  nunca pegados en el texto: así no hay inyección de SQL. */
export async function consultar(archivo, parametros = {}) {
  const p = await obtenerPool();
  const req = p.request();
  for (const [nombre, valor] of Object.entries(parametros)) {
    req.input(nombre, sql.VarChar(50), valor);
  }
  const r = await req.query(leerSql(archivo));
  return r.recordset;
}

export async function cerrar() {
  if (pool) await pool.close();
  pool = null;
}
