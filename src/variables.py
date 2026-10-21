"""Variables por registro para el modelo de actividad.

REGLA: solo se usa el pasado (el modelo corre en tiempo real). La MISMA función
se usa para entrenar y para el proceso de scoring cada 5 minutos, así lo que el
modelo ve al entrenar es exactamente lo que verá en producción.
Los rezagos se cortan en los huecos: si el registro anterior está a más de
`hueco_max_min` minutos, se considera un tramo nuevo y el rezago queda vacío.
"""
import numpy as np
import pandas as pd

from src.rumbo import diferencia_angular, rumbo_gps

BASE = ["Velocidad", "rpm", "gal_h"]

FEATURES = (
    BASE
    + [f"{c}_lag{k}" for c in BASE for k in (1, 2)]
    + [f"{c}_delta" for c in BASE]
    + [f"{c}_media4" for c in BASE]
    + ["Velocidad_std4", "Velocidad_min4", "Velocidad_max4"]
    + ["CambioRumboGPS", "GiroAcum3", "DesplazKm", "MinDesdeAnterior", "PosEnTramo"]
    + ["hora_sin", "hora_cos"]
    + ["DistPuertoKm", "DistPuerto_delta", "DistPuerto_delta4"]
    + ["MinFueraPuerto", "DistPuertoMax", "DistRelMax", "ParadasEnSalida", "MinDesdeParada"]
)

# Contexto del viaje: necesita la historia desde la última vez que estuvo en puerto.
# En producción, el scoring debe cargar al menos HORAS_HISTORIA horas hacia atrás.
HORAS_HISTORIA = 120


def construir_variables(tel: pd.DataFrame, hueco_max_min=30, ventana=4) -> pd.DataFrame:
    """Devuelve `tel` con las columnas de FEATURES y `Tramo` (segmento continuo)."""
    t = tel.sort_values(["ep", "fecha"]).copy()
    dt = t.groupby("ep")["fecha"].diff().dt.total_seconds() / 60
    t["MinDesdeAnterior"] = dt
    t["Tramo"] = (dt.isna() | (dt > hueco_max_min)).cumsum()
    g = t.groupby("Tramo", sort=False)
    t["PosEnTramo"] = g.cumcount()  # 0 = primer registro tras un hueco (sin historia)

    for c in BASE:
        for k in (1, 2):
            t[f"{c}_lag{k}"] = g[c].shift(k)
        t[f"{c}_delta"] = t[c] - t[f"{c}_lag1"]
        t[f"{c}_media4"] = g[c].transform(lambda s: s.rolling(ventana, min_periods=1).mean())
    t["Velocidad_std4"] = g["Velocidad"].transform(lambda s: s.rolling(ventana, min_periods=2).std())
    t["Velocidad_min4"] = g["Velocidad"].transform(lambda s: s.rolling(ventana, min_periods=1).min())
    t["Velocidad_max4"] = g["Velocidad"].transform(lambda s: s.rolling(ventana, min_periods=1).max())

    # Movimiento real entre el registro anterior y el actual (GPS)
    lat0, lon0 = g["Latitud"].shift(1), g["Longitud"].shift(1)
    t["RumboGPS"] = rumbo_gps(lat0, lon0, t["Latitud"], t["Longitud"])
    la0, lo0, la1, lo1 = map(np.radians, [lat0, lon0, t["Latitud"], t["Longitud"]])
    a = np.sin((la1 - la0) / 2) ** 2 + np.cos(la0) * np.cos(la1) * np.sin((lo1 - lo0) / 2) ** 2
    t["DesplazKm"] = 6371 * 2 * np.arcsin(np.sqrt(a))
    # Con la embarcación casi quieta el rumbo GPS es ruido: no se usa para giros
    rumbo_ok = t["RumboGPS"].where(t["DesplazKm"] > 0.2)
    t["CambioRumboGPS"] = diferencia_angular(rumbo_ok, rumbo_ok.groupby(t["Tramo"]).shift(1))
    t["GiroAcum3"] = t.groupby("Tramo")["CambioRumboGPS"].transform(
        lambda s: s.fillna(0).rolling(3, min_periods=1).sum())

    hora = t["fecha"].dt.hour + t["fecha"].dt.minute / 60
    t["hora_sin"], t["hora_cos"] = np.sin(2 * np.pi * hora / 24), np.cos(2 * np.pi * hora / 24)
    if "DistPuertoKm" not in t:
        t["DistPuertoKm"] = np.nan
    # ¿Se aleja (+) o se acerca (−) al puerto? Separa ida de retorno, que a la misma
    # velocidad y rumbo recto son indistinguibles por lo demás.
    t["DistPuerto_delta"] = t["DistPuertoKm"] - t.groupby("Tramo")["DistPuertoKm"].shift(1)
    t["DistPuerto_delta4"] = t.groupby("Tramo")["DistPuerto_delta"].transform(
        lambda s: s.rolling(4, min_periods=1).mean())
    return agregar_contexto(t)


def agregar_contexto(t: pd.DataFrame, radio_puerto=5, vel_parada=2.0) -> pd.DataFrame:
    """Lo que ya hizo la embarcación desde que salió de puerto (solo pasado).
    Separa ida de retorno: en el retorno ya paró y se está acercando desde su punto más lejano."""
    ep = t["ep"]
    en_puerto = t["DistPuertoKm"] <= radio_puerto
    # cada entrada a puerto inicia una "salida" nueva
    t["Salida"] = (en_puerto & ~en_puerto.groupby(ep).shift(1, fill_value=False)).groupby(ep).cumsum()
    grupo = [ep, t["Salida"]]

    ult_puerto = t["fecha"].where(en_puerto).groupby(ep).ffill()
    t["MinFueraPuerto"] = (t["fecha"] - ult_puerto).dt.total_seconds() / 60
    t["DistPuertoMax"] = t.groupby(grupo)["DistPuertoKm"].cummax()
    t["DistRelMax"] = t["DistPuertoKm"] / t["DistPuertoMax"].clip(lower=1)

    lento = (t["Velocidad"] < vel_parada) & ~en_puerto
    inicio = lento & ~lento.groupby(ep).shift(1, fill_value=False)
    t["ParadasEnSalida"] = inicio.groupby(grupo).cumsum()
    ult_lento = t["fecha"].where(lento).groupby(grupo).ffill()
    t["MinDesdeParada"] = (t["fecha"] - ult_lento).dt.total_seconds() / 60
    return t


def verificar_sin_futuro(tel: pd.DataFrame, n=200, semilla=0) -> bool:
    """Prueba de fuga: las variables de un registro no deben cambiar si se borra
    todo lo posterior a él. Devuelve True si se cumple en `n` registros al azar."""
    completo = construir_variables(tel).set_index(["ep", "fecha"])
    muestra = completo.sample(min(n, len(completo)), random_state=semilla).index
    for ep, fecha in muestra:
        parcial = construir_variables(tel[(tel["ep"] == ep) & (tel["fecha"] <= fecha)]).set_index(["ep", "fecha"])
        a, b = completo.loc[(ep, fecha), FEATURES], parcial.loc[(ep, fecha), FEATURES]
        if not np.allclose(a.astype(float).fillna(-999), b.astype(float).fillna(-999)):
            print("Fuga de futuro en", ep, fecha)
            return False
    return True