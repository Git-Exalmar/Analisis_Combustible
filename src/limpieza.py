"""Limpieza de la telemetría: la MISMA para entrenar y para el scoring en tiempo real."""
import pandas as pd

NUMERICAS = ["Latitud", "Longitud", "Velocidad", "rpm", "gal_h"]


def limpiar_telemetria(tel: pd.DataFrame) -> pd.DataFrame:
    t = tel.copy()
    t["fecha"] = pd.to_datetime(t["fecha"])
    t["ep"] = t["ep"].astype(str).str.strip().str.upper()
    for c in NUMERICAS:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    t = t.drop_duplicates(["ep", "fecha"])
    t = t[(t["Latitud"].abs() < 89) & (t["Longitud"].abs() < 179)]   # coordenadas vacías (90°/180°)
    t = t[t["rpm"].between(300, 1400) & (t["gal_h"] < 6553)]           # 6553.5 = error del sensor
    return t.sort_values(["ep", "fecha"]).reset_index(drop=True)