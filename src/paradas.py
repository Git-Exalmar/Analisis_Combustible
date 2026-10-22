"""Detección de paradas (embarcación casi detenida) y su caracterización."""
import numpy as np
import pandas as pd


def _km(lat1, lon1, lat2, lon2):
    """Distancia haversine en km."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def detectar_paradas(tel: pd.DataFrame, vel_max=2.0, min_registros=2, hueco_max_min=30) -> pd.DataFrame:
    """Devuelve una fila por parada: tramo continuo con Velocidad < vel_max.

    tel: telemetría con ep, fecha, Velocidad, rpm, gal_h, Latitud, Longitud, IdViaje.
    """
    t = tel.sort_values(["ep", "fecha"]).reset_index(drop=True)
    lento = t["Velocidad"] < vel_max
    hueco = t.groupby("ep")["fecha"].diff().dt.total_seconds().div(60).gt(hueco_max_min)
    nuevo_ep = t["ep"].ne(t["ep"].shift())
    t["tramo"] = (lento.ne(lento.shift()) | hueco | nuevo_ep).cumsum()

    # velocidad de los 2 registros previos y posteriores a cada tramo (contexto)
    vel_prev = t.groupby("ep")["Velocidad"].transform(lambda s: s.shift(1).rolling(2).mean())
    vel_next = t.groupby("ep")["Velocidad"].transform(lambda s: s[::-1].shift(1).rolling(2).mean()[::-1])

    p = t[lento].assign(vel_prev=vel_prev, vel_next=vel_next).groupby("tramo").agg(
        ep=("ep", "first"),
        IdViaje=("IdViaje", "first"),
        inicio=("fecha", "min"),
        fin=("fecha", "max"),
        n_registros=("fecha", "size"),
        vel_media=("Velocidad", "mean"),
        rpm_mediana=("rpm", "median"),
        rpm_std=("rpm", "std"),
        galh_mediana=("gal_h", "median"),
        galh_std=("gal_h", "std"),
        lat_ini=("Latitud", "first"), lon_ini=("Longitud", "first"),
        lat_fin=("Latitud", "last"), lon_fin=("Longitud", "last"),
    )
    # contexto: velocidad justo antes (primer registro del tramo) y justo después (último)
    p["vel_antes"] = t[lento].groupby("tramo").apply(lambda g: vel_prev.loc[g.index[0]], include_groups=False)
    p["vel_despues"] = t[lento].groupby("tramo").apply(lambda g: vel_next.loc[g.index[-1]], include_groups=False)

    # contexto de rumbo (requiere CambioRumboGPS de src/rumbo.py): giro en los 2 registros
    # antes de detenerse (cerco) y en los 2 registros después de arrancar
    if "CambioRumboGPS" in t:
        giro = t["CambioRumboGPS"].fillna(0)
        g_prev = t.groupby("ep")["CambioRumboGPS"].transform(lambda s: s.fillna(0).shift(1).rolling(2).sum())
        g_next = t.groupby("ep")["CambioRumboGPS"].transform(lambda s: s.fillna(0)[::-1].shift(1).rolling(2).sum()[::-1])
        p["giro_antes"] = t[lento].groupby("tramo").apply(lambda g: g_prev.loc[g.index[0]], include_groups=False)
        p["giro_despues"] = t[lento].groupby("tramo").apply(lambda g: g_next.loc[g.index[-1]], include_groups=False)
    if "DistPuertoKm" in t:
        p["dist_puerto_km"] = t[lento].groupby("tramo")["DistPuertoKm"].median()

    p = p[p["n_registros"] >= min_registros].reset_index(drop=True)
    p["duracion_min"] = (p["fin"] - p["inicio"]).dt.total_seconds() / 60 + 15
    p["deriva_km"] = _km(p["lat_ini"], p["lon_ini"], p["lat_fin"], p["lon_fin"])
    p["hora_inicio"] = p["inicio"].dt.hour
    return p.drop(columns=["lat_fin", "lon_fin"])


def marcar_calas_registradas(paradas: pd.DataFrame, ventanas_fin: pd.DataFrame,
                             viajes: pd.DataFrame, tolerancia_min=30) -> pd.DataFrame:
    """Marca las paradas que coinciden con una cala registrada (ventana definitiva)."""
    w = ventanas_fin.merge(viajes[["IdViaje", "Embarcacion"]], on="IdViaje").rename(columns={"Embarcacion": "ep"})
    tol = pd.Timedelta(minutes=tolerancia_min)
    p = paradas.copy()
    p["CalaRegistrada"] = False
    p["NumCala"] = pd.NA
    for ep, grupo in w.groupby("ep"):
        idx = p.index[p["ep"] == ep]
        for _, c in grupo.iterrows():
            cruza = (p.loc[idx, "inicio"] <= c["Fin"] + tol) & (p.loc[idx, "fin"] >= c["Inicio"] - tol)
            p.loc[cruza[cruza].index, ["CalaRegistrada", "NumCala"]] = [True, c["NumCala"]]
    p["Tipo"] = np.where(p["CalaRegistrada"], "cala_registrada",
                         np.where(p["IdViaje"].isna(), "parada_sin_viaje", "parada_no_registrada"))
    return p