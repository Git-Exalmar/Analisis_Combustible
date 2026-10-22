"""Extrae los datos de las bases y los guarda en data/raw/ como parquet.

Uso:
    py -m scripts.extraer_datos              # extrae todo
    py -m scripts.extraer_datos metas        # solo metas
    py -m scripts.extraer_datos telemetria   # solo telemetría
"""
import sys
import time
from datetime import datetime

from src.config import DIR_DATA_RAW
from src.db import consultar

# Qué consultas ejecutar en cada fuente: nombre_salida -> archivo .sql
EXTRACCIONES = {
    "metas": {
        "faenas": "metas/faenas.sql",
    },
        "silver": {
        "faenas": "operacion/faenas.sql",
        "calas": "operacion/calas.sql",
    },
    "telemetria": {
        "mp_m": "telemetria/mp_m.sql",
        "mp_e": "telemetria/mp_e.sql",
        "mp_e_h": "telemetria/mp_e_h.sql",
        "mp_m_h": "telemetria/mp_m_h.sql",
    },
}


def extraer(fuente: str) -> None:
    destino = DIR_DATA_RAW / fuente
    destino.mkdir(parents=True, exist_ok=True)

    for nombre, ruta_sql in EXTRACCIONES[fuente].items():
        inicio = time.time()
        print(f"[{fuente}] {nombre}: consultando...", end=" ", flush=True)
        df = consultar(fuente, ruta_sql)
        df["origen"] = nombre  # para saber de qué consulta vino cada fila
        archivo = destino / f"{nombre}.parquet"
        df.to_parquet(archivo, index=False)
        print(f"{len(df):,} filas en {time.time() - inicio:.1f}s -> {archivo.name}")


def main() -> None:
    fuentes = sys.argv[1:] or list(EXTRACCIONES)
    print(f"Extracción iniciada: {datetime.now():%Y-%m-%d %H:%M}")
    for fuente in fuentes:
        extraer(fuente)
    print("Listo.")


if __name__ == "__main__":
    main()