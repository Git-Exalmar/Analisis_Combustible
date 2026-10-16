"""Lectura de consultas SQL desde archivos .sql."""
import warnings
import pandas as pd
import pyodbc
from src.config import DIR_SQL, cadena_conexion

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")


def leer_sql(ruta_relativa: str) -> str:
    """Devuelve el texto de un archivo .sql, por ejemplo 'metas/faenas.sql'."""
    return (DIR_SQL / ruta_relativa).read_text(encoding="utf-8")


def consultar(fuente: str, ruta_sql: str) -> pd.DataFrame:
    """Ejecuta el .sql indicado contra la fuente ('metas' o 'telemetria')."""
    with pyodbc.connect(cadena_conexion(fuente)) as conn:
        return pd.read_sql(leer_sql(ruta_sql), conn)