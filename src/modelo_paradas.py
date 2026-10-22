"""Nivel 1: ¿qué paradas son calas? Aprendizaje PU (positivos y no etiquetados).

- Positivas: paradas que coinciden con una cala registrada.
- El resto (paradas sin etiqueta + paradas en puerto) se trata como NO etiquetado.
- Método de Elkan y Noto (2008): se entrena un clasificador "registrada vs resto";
  como parte del "resto" también son calas (no registradas), la probabilidad se
  corrige dividiendo por c = P(registrada | es cala), estimada con las positivas.
- Las paradas en puerto se fijan en 0 al final (seguro no son calas).

No se usa la distancia al puerto como variable: con ella se definen las negativas y
el modelo aprendería esa regla en lugar del comportamiento de la cala.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

VARIABLES = ["duracion_min", "n_registros", "vel_media", "galh_mediana", "galh_std",
             "rpm_mediana", "rpm_std", "vel_antes", "vel_despues",
             "giro_antes", "giro_despues", "hora_sin", "hora_cos"]

def preparar(par: pd.DataFrame) -> pd.DataFrame:
    p = par.copy()
    h = p["inicio"].dt.hour + p["inicio"].dt.minute / 60
    p["hora_sin"], p["hora_cos"] = np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)
    p["s"] = (p["Tipo"] == "cala_registrada").astype(int)          # etiquetada como cala
    p["puerto"] = p["dist_puerto_km"] <= 5
    return p


def _modelo(semilla=0):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                          min_samples_leaf=20, l2_regularization=1.0,
                                          random_state=semilla)


def entrenar_pu(par: pd.DataFrame, n_folds=5, semilla=0):
    """Devuelve (paradas con P_cala, c, modelo final).

    Las probabilidades son 'fuera de muestra': cada parada se predice con un modelo
    que no la vio, agrupando por embarcación para no hacer trampa con viajes vecinos.
    """
    p = preparar(par)
    X, s, grupos = p[VARIABLES], p["s"], p["ep"]
    oof = np.zeros(len(p))
    for tr, te in GroupKFold(n_splits=min(n_folds, grupos.nunique())).split(X, s, grupos):
        m = _modelo(semilla).fit(X.iloc[tr], s.iloc[tr])
        oof[te] = m.predict_proba(X.iloc[te])[:, 1]

    c = oof[s == 1].mean()                       # P(registrada | cala)
    p["P_registrada"] = oof
    p["P_cala"] = np.clip(oof / c, 0, 1)
    p.loc[p["puerto"], "P_cala"] = 0.0
    final = _modelo(semilla).fit(X, s)
    return p, c, final


def predecir(modelo, c, par: pd.DataFrame) -> pd.Series:
    """Para producción: P(cala) de paradas nuevas con el modelo final."""
    p = preparar(par)
    prob = np.clip(modelo.predict_proba(p[VARIABLES])[:, 1] / c, 0, 1)
    return pd.Series(np.where(p["puerto"], 0.0, prob), index=par.index, name="P_cala")


def clasificar(p_cala: pd.Series, alto=0.5, bajo=0.2) -> pd.Series:
    return pd.Series(np.select([p_cala >= alto, p_cala < bajo], ["cala", "no cala"],
                               "posible cala"), index=p_cala.index)