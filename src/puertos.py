"""Ubicación de los puertos (aprendida de la telemetría) y estado de los registros fuera de viaje."""
import numpy as np
import pandas as pd


def _km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def estimar_puertos(tel_v: pd.DataFrame, viajes: pd.DataFrame, ventana_min=30, min_viajes=5) -> pd.DataFrame:
    """Posición de cada puerto = mediana de las posiciones en los primeros minutos
    después del zarpe de los viajes que salieron de ese puerto."""
    t = tel_v.merge(viajes[["IdViaje", "PuertoZarpe"]], on="IdViaje", how="inner")
    t = t[(t["MinDesdeZarpe"] <= ventana_min) & t["PuertoZarpe"].notna()]
    p = (t.groupby("PuertoZarpe")
           .agg(Latitud=("Latitud", "median"), Longitud=("Longitud", "median"),
                viajes=("IdViaje", "nunique"), registros=("IdViaje", "size"))
           .reset_index())
    return p[p["viajes"] >= min_viajes].sort_values("viajes", ascending=False).reset_index(drop=True)


def distancia_puerto(tel: pd.DataFrame, puertos: pd.DataFrame) -> pd.DataFrame:
    """Agrega PuertoCercano y DistPuertoKm a cada registro."""
    t = tel.copy()
    d = np.column_stack([_km(t["Latitud"].to_numpy(), t["Longitud"].to_numpy(), r.Latitud, r.Longitud)
                         for r in puertos.itertuples()])
    i = d.argmin(axis=1)
    t["PuertoCercano"] = puertos["PuertoZarpe"].to_numpy()[i]
    t["DistPuertoKm"] = d[np.arange(len(t)), i]
    return t


def estado_fuera_de_viaje(t: pd.DataFrame, radio_km=5, vel_max=1.5) -> pd.Series:
    """Para registros SIN viaje: 'puerto' si está quieto cerca de un puerto;
    'mar sin faena' si no (búsqueda no registrada, traslado u otra actividad)."""
    en_puerto = (t["DistPuertoKm"] <= radio_km) & (t["Velocidad"] <= vel_max)
    estado = np.where(t["IdViaje"].notna(), "en viaje",
                      np.where(en_puerto, "puerto", "mar sin faena"))
    return pd.Series(estado, index=t.index)