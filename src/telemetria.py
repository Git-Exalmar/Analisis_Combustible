"""Unión de la telemetría con los viajes (faenas)."""
import pandas as pd


def asignar_viaje(tel: pd.DataFrame, viajes: pd.DataFrame) -> pd.DataFrame:
    """Agrega IdViaje a cada registro de telemetría.

    Un registro pertenece a un viaje si su fecha está entre ZarpeCorregido y
    FinViaje de la misma embarcación. Los que no caen en ningún viaje quedan
    con IdViaje vacío (búsqueda no registrada, puerto, etc.).
    """
    t = tel.copy()
    t["ep"] = t["ep"].astype(str).str.strip().str.upper()
    t = t.sort_values("fecha")
    v = (viajes[["IdViaje", "Embarcacion", "ZarpeCorregido", "FinViaje"]]
         .rename(columns={"Embarcacion": "ep"})
         .sort_values("ZarpeCorregido"))

    m = pd.merge_asof(t, v, left_on="fecha", right_on="ZarpeCorregido",
                      by="ep", direction="backward")
    fuera = m["FinViaje"].isna() | (m["fecha"] > m["FinViaje"])
    m.loc[fuera, ["IdViaje", "ZarpeCorregido", "FinViaje"]] = pd.NA
    m["IdViaje"] = m["IdViaje"].astype("Int64")
    m["MinDesdeZarpe"] = (m["fecha"] - m["ZarpeCorregido"]).dt.total_seconds() / 60
    m["MinHastaFin"] = (m["FinViaje"] - m["fecha"]).dt.total_seconds() / 60
    return m.sort_values(["ep", "fecha"]).reset_index(drop=True)


def cruzar_nombres(tel: pd.DataFrame, viajes: pd.DataFrame) -> pd.DataFrame:
    """Muestra qué embarcaciones están en telemetría, en faenas o en ambas."""
    a = set(tel["ep"].astype(str).str.strip().str.upper())
    b = set(viajes["Embarcacion"])
    filas = [(n, n in a, n in b) for n in sorted(a | b)]
    return pd.DataFrame(filas, columns=["embarcacion", "en_telemetria", "en_faenas"])