"""Configuración: rutas del proyecto y cadenas de conexión."""
import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DIR_SQL = RAIZ / "sql"
DIR_DATA_RAW = RAIZ / "data" / "raw"
DIR_DATA_PROC = RAIZ / "data" / "processed"
DIR_MODELOS = RAIZ / "modelos"

FUENTES = {
    "metas": {
        "server": os.getenv("DB_SERVER_INDICADORES", "10.1.0.4"),
        "database": "DB_Indicadores",
        "user": os.getenv("DB_USER_INDICADORES"),
        "password": os.getenv("DB_PASS_INDICADORES"),
        "trust_cert": "yes",
    },
    "telemetria": {
        "server": os.getenv("DB_SERVER_TELEMETRIA", "exalmar-rg-qas.database.windows.net,1433"),
        "database": "BD_TEL_FLOTA_PRD",
        "user": os.getenv("DB_USER_QAS"),
        "password": os.getenv("DB_PASS_QAS"),
        "trust_cert": "no",
    },
}


def cadena_conexion(fuente: str) -> str:
    c = FUENTES[fuente]
    if not c["user"] or not c["password"]:
        raise ValueError(f"Faltan credenciales de '{fuente}' en el .env")
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={c['server']};DATABASE={c['database']};"
        f"UID={c['user']};PWD={c['password']};"
        f"Encrypt=yes;TrustServerCertificate={c['trust_cert']};"
    )