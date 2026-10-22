"""Conversión y variables derivadas del rumbo."""
import numpy as np
import pandas as pd

# Código de sector (0-7) -> grados. Hipótesis: 0 = Norte, sentido horario, cada 45°.
# Verificar con verificar_codigos_rumbo() antes de usar.
CODIGO_A_GRADOS = {0: 0, 1: 45, 2: 90, 3: 135, 4: 180, 5: 225, 6: 270, 7: 315}


def rumbo_a_grados(serie: pd.Series, mapa=CODIGO_A_GRADOS) -> pd.Series:
    """Convierte el código de rumbo (0-7) a grados."""
    return pd.to_numeric(serie, errors="coerce").map(mapa)


def diferencia_angular(a, b):
    """Diferencia mínima entre dos rumbos, entre 0 y 180 grados (350° vs 10° = 20°)."""
    d = np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)) % 360
    return np.minimum(d, 360 - d)


def rumbo_gps(lat1, lon1, lat2, lon2):
    """Rumbo (0° = Norte, sentido horario) del desplazamiento entre dos posiciones."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    x = np.sin(lon2 - lon1) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360


def verificar_codigos_rumbo(tel: pd.DataFrame, vel_min=6, hueco_max_min=20) -> pd.DataFrame:
    """Compara cada código de rumbo con el rumbo real calculado por GPS.

    Solo usa tramos navegando (velocidad >= vel_min) y registros consecutivos.
    Devuelve, por código, el rumbo GPS medio (media circular) y su dispersión.
    """
    t = tel.sort_values(["ep", "fecha"]).copy()
    g = t.groupby("ep")
    sig_lat, sig_lon = g["Latitud"].shift(-1), g["Longitud"].shift(-1)
    dt = (g["fecha"].shift(-1) - t["fecha"]).dt.total_seconds() / 60
    t["rumbo_gps"] = rumbo_gps(t["Latitud"], t["Longitud"], sig_lat, sig_lon)
    ok = (t["Velocidad"] >= vel_min) & (dt <= hueco_max_min) & t["rumbo_gps"].notna()
    t = t[ok]

    def media_circular(x):
        r = np.radians(x)
        s, c = np.sin(r).mean(), np.cos(r).mean()
        return pd.Series({"rumbo_gps_medio": (np.degrees(np.arctan2(s, c)) + 360) % 360,
                          "concentracion": np.hypot(s, c),  # 1 = todos iguales, 0 = aleatorio
                          "n": len(x)})
    return t.groupby("Rumbo")["rumbo_gps"].apply(media_circular).unstack().round(2)


def agregar_variables_rumbo(tel: pd.DataFrame, mapa=CODIGO_A_GRADOS, hueco_max_min=30) -> pd.DataFrame:
    """Agrega RumboGrados, CambioRumbo, RumboGPS, CambioRumboGPS y GiroAcum45."""
    t = tel.sort_values(["ep", "fecha"]).copy()
    g = t.groupby("ep")
    hueco = g["fecha"].diff().dt.total_seconds().div(60).gt(hueco_max_min)

    t["RumboGrados"] = rumbo_a_grados(t["Rumbo"], mapa)
    t["CambioRumbo"] = pd.Series(diferencia_angular(t["RumboGrados"], g["RumboGrados"].shift()),
                                 index=t.index).mask(hueco)

    # Rumbo continuo calculado con GPS (desde el registro anterior hasta el actual)
    t["RumboGPS"] = pd.Series(rumbo_gps(g["Latitud"].shift(), g["Longitud"].shift(),
                                        t["Latitud"], t["Longitud"]), index=t.index).mask(hueco)
    t["CambioRumboGPS"] = pd.Series(diferencia_angular(t["RumboGPS"], t.groupby("ep")["RumboGPS"].shift()),
                                    index=t.index).mask(hueco)
    t["GiroAcum45"] = t.groupby("ep")["CambioRumboGPS"].transform(lambda s: s.rolling(3, min_periods=1).sum())
    return t