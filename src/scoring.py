"""Scoring en tiempo real: telemetría reciente -> actividad de cada registro.

Usa EXACTAMENTE las mismas funciones que el entrenamiento (limpieza, distancia
a puerto y variables), para que el modelo vea en producción lo mismo que vio al entrenar.
"""
import datetime as dt

import joblib
import numpy as np
import pandas as pd
import pyodbc

from src.config import DIR_MODELOS, cadena_conexion
from src.db import leer_sql
from src.limpieza import limpiar_telemetria
from src.puertos import distancia_puerto
from src.variables import construir_variables

UTC_OFFSET_PERU = -5   # Perú no cambia de horario; Azure (servidor y contenedor) trabaja en UTC

COLUMNAS_TABLA = {   # columna del DataFrame -> columna de ml.ActividadEmbarcacion
    "ep": "Embarcacion", "fecha": "FechaRegistro", "Latitud": "Latitud", "Longitud": "Longitud",
    "Velocidad": "Velocidad", "rpm": "Rpm", "gal_h": "GalH", "PuertoCercano": "PuertoCercano",
    "DistPuertoKm": "DistPuertoKm", "Actividad": "Actividad", "Probabilidad": "Probabilidad",
    "P_ida": "P_ida", "P_busqueda": "P_busqueda", "P_entrada_cala": "P_entrada_cala",
    "P_cala": "P_cala", "P_salida_cala": "P_salida_cala", "P_retorno": "P_retorno",
    "P_espera": "P_espera", "P_puerto": "P_puerto", "TipoEtiqueta": "TipoEtiqueta",
    "VersionModelo": "VersionModelo", "FechaProceso": "FechaProceso",
}


def ahora_peru() -> dt.datetime:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=UTC_OFFSET_PERU)).replace(tzinfo=None, microsecond=0)


def cargar_paquete(nombre="actividad_v1.joblib") -> dict:
    p = joblib.load(DIR_MODELOS / nombre)
    if "puertos" not in p:
        raise ValueError("El paquete no trae los puertos. Ejecuta la celda que los agrega (paso 11).")
    return p


def leer_telemetria_reciente(horas: float, ahora: dt.datetime | None = None) -> pd.DataFrame:
    desde = (ahora or ahora_peru()) - dt.timedelta(hours=horas)
    with pyodbc.connect(cadena_conexion("telemetria")) as conn:
        return pd.read_sql(leer_sql("scoring/telemetria_reciente.sql"), conn, params=[desde, desde])


def puntuar(tel: pd.DataFrame, paquete: dict, ahora: dt.datetime | None = None) -> pd.DataFrame:
    t = limpiar_telemetria(tel)
    t = distancia_puerto(t, paquete["puertos"])
    t = construir_variables(t)

    modelo = paquete["modelo"]
    proba = modelo.predict_proba(t[paquete["variables"]])
    clases = np.array(modelo.classes_)

    res = t[["ep", "fecha", "Latitud", "Longitud", "Velocidad", "rpm", "gal_h",
             "PuertoCercano", "DistPuertoKm"]].copy()
    for i, c in enumerate(clases):
        res[f"P_{c}"] = proba[:, i]
    res["Actividad"] = clases[proba.argmax(axis=1)]
    res["Probabilidad"] = proba.max(axis=1)
    res["TipoEtiqueta"] = "provisional"
    res["VersionModelo"] = paquete["version"]
    res["FechaProceso"] = ahora or ahora_peru()
    return res.reset_index(drop=True)


def retraso_por_embarcacion(res: pd.DataFrame, ahora: dt.datetime) -> pd.DataFrame:
    """Minutos desde el último registro recibido de cada embarcación."""
    u = res.groupby("ep")["fecha"].max().rename("UltimoRegistro").to_frame()
    u["RetrasoMin"] = (ahora - u["UltimoRegistro"]).dt.total_seconds() / 60
    return u.sort_values("RetrasoMin")


def escribir_sql(nuevos: pd.DataFrame, desde: dt.datetime, fuente="resultados") -> int:
    """Reemplaza en ml.ActividadEmbarcacion todo lo que hay desde `desde`.
    Borrar + insertar en una sola transacción: si algo falla, no queda a medias,
    y si el proceso se ejecuta dos veces el resultado es el mismo."""
    d = nuevos[list(COLUMNAS_TABLA)].rename(columns=COLUMNAS_TABLA)
    filas = d.astype(object).where(d.notna(), None).values.tolist()
    cols = ", ".join(d.columns)
    marcas = ", ".join("?" * len(d.columns))
    conn = pyodbc.connect(cadena_conexion(fuente), autocommit=False)
    try:
        cur = conn.cursor()
        cur.fast_executemany = True
        cur.execute("DELETE FROM ml.ActividadEmbarcacion WHERE FechaRegistro >= ?", desde)
        if filas:
            cur.executemany(f"INSERT INTO ml.ActividadEmbarcacion ({cols}) VALUES ({marcas})", filas)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return len(filas)


def registrar_proceso(fuente="resultados", **campos) -> None:
    cols = ", ".join(campos)
    with pyodbc.connect(cadena_conexion(fuente), autocommit=True) as conn:
        conn.execute(f"INSERT INTO ml.ProcesoScoring ({cols}) VALUES ({', '.join('?' * len(campos))})",
                     *campos.values())