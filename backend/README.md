# API · Panel de actividad de flota

Node.js + Express. Lee `ml.ActividadEmbarcacion` (escrita por `scripts/scoring.py`) y la entrega al panel React.

## Ejecutar
```powershell
cd backend
npm install
copy .env.example .env     # y completar DB_USER / DB_PASS
npm run dev                # se reinicia sola al guardar cambios
npm test                   # pruebas sin base de datos
```

## Endpoints (todas las fechas en hora de Perú, formato `AAAA-MM-DDTHH:MM:SS`)
| Método | Ruta | Qué devuelve |
|---|---|---|
| GET | `/api/salud` | Si la API llega a la base y la última ejecución del scoring |
| GET | `/api/flota/actual` | Último registro de cada embarcación; `actividadMostrada` = `sin_datos` si el dato tiene más de `LIMITE_SIN_DATOS_MIN`, `posible_entrada` para la entrada a cala |
| GET | `/api/flota/bitacora?desde=&hasta=` | Segmentos de actividad por embarcación (por defecto, últimas 120 h) |
| GET | `/api/embarcaciones/:ep/registros?desde=&hasta=` | Serie de una embarcación con las 8 probabilidades (por defecto, últimas 48 h) |
| GET | `/api/stream` | SSE: evento `flota` al conectarse y cada vez que corre un scoring nuevo |

## Modo demo
`AHORA_FIJO=2026-04-25T14:00:00` en el `.env` fija la hora "actual" para usar los datos repetidos de temporada. En producción va vacío.
