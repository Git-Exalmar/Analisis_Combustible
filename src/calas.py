"""Estimación de inicio y fin real de cada cala a partir de la telemetría."""
import numpy as np
import pandas as pd


def estimar_ventana_calas(tel: pd.DataFrame, calas: pd.DataFrame, viajes: pd.DataFrame,
                          vel_max: float = 2.0, antes_h: float = 4, despues_min: float = 45,
                          hueco_max_min: float = 30) -> pd.DataFrame:
    """Para cada cala busca el tramo de embarcación casi detenida (Velocidad < vel_max)
    más cercano a la hora registrada (HoraRegistrada).

    tel: telemetría con columnas ep, fecha, Velocidad (sin duplicados).
    Devuelve calas con InicioCalaEst, FinCalaEst, DuracionEstMin, DesfaseFinMin
    (FinCalaEst - hora registrada) y CalaDetectada (bool).
    """
    c = calas.merge(viajes[["IdViaje", "Embarcacion"]], on="IdViaje")
    salida = []
    for ep, grupo in c.groupby("Embarcacion"):
        t = tel.loc[tel["ep"] == ep, ["fecha", "Velocidad"]].sort_values("fecha")
        if t.empty:
            continue
        fechas = t["fecha"].to_numpy()
        for _, cala in grupo.iterrows():
            reg = cala["HoraRegistrada"]
            ini = np.searchsorted(fechas, np.datetime64(reg - pd.Timedelta(hours=antes_h)))
            fin = np.searchsorted(fechas, np.datetime64(reg + pd.Timedelta(minutes=despues_min)), side="right")
            w = t.iloc[ini:fin].copy()
            res = {"IdViaje": cala["IdViaje"], "NumCala": cala["NumCala"], "HoraRegistrada": reg,
                   "InicioCalaEst": pd.NaT, "FinCalaEst": pd.NaT}
            if len(w) >= 2:
                lento = w["Velocidad"] < vel_max
                hueco = w["fecha"].diff().dt.total_seconds().div(60).gt(hueco_max_min)
                tramo = (lento.ne(lento.shift()) | hueco).cumsum()
                runs = (w[lento].groupby(tramo[lento])["fecha"].agg(["min", "max", "size"]))
                if not runs.empty:
                    # distancia del tramo a la hora registrada (0 si la contiene)
                    dist = np.maximum((runs["min"] - reg).dt.total_seconds(),
                                      (reg - runs["max"]).dt.total_seconds()).clip(lower=0)
                    mejor = runs.loc[dist.idxmin()]
                    if dist.min() <= 45 * 60:
                        res["InicioCalaEst"], res["FinCalaEst"] = mejor["min"], mejor["max"]
            salida.append(res)

    out = pd.DataFrame(salida)
    out["CalaDetectada"] = out["InicioCalaEst"].notna()
    out["DuracionEstMin"] = (out["FinCalaEst"] - out["InicioCalaEst"]).dt.total_seconds() / 60
    out["DesfaseFinMin"] = (out["FinCalaEst"] - out["HoraRegistrada"]).dt.total_seconds() / 60
    out["DesfaseInicioMin"] = (out["InicioCalaEst"] - out["HoraRegistrada"]).dt.total_seconds() / 60
    return out
