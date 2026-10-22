"""Nivel 2: actividad de cada registro (tiempo real, solo variables del pasado)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from src.variables import FEATURES

CLASES = ["ida", "busqueda", "entrada_cala", "cala", "salida_cala", "retorno", "espera", "puerto"]


def armar_entrenamiento(tel_e: pd.DataFrame) -> pd.DataFrame:
    """Solo registros con etiqueta confiable (descarta sin_viaje, viaje_sin_cala, mar_sin_faena)."""
    d = tel_e[tel_e["Etiqueta"].isin(CLASES)].copy()
    d["Etiqueta"] = pd.Categorical(d["Etiqueta"], categories=CLASES)
    return d


def _modelo(semilla=0):
    return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=63,
                                          min_samples_leaf=40, l2_regularization=1.0,
                                          class_weight="balanced", early_stopping=True,
                                          validation_fraction=0.1, random_state=semilla)


def entrenar(d: pd.DataFrame, semilla=0):
    return _modelo(semilla).fit(d[FEATURES], d["Etiqueta"].astype(str))


def evaluar(modelo, d: pd.DataFrame):
    """Métricas POR CLASE (el accuracy global esconde las clases pequeñas)."""
    y, pred = d["Etiqueta"].astype(str), modelo.predict(d[FEATURES])
    reporte = pd.DataFrame(classification_report(y, pred, labels=CLASES, output_dict=True,
                                                 zero_division=0)).T.round(3)
    cm = pd.DataFrame(confusion_matrix(y, pred, labels=CLASES, normalize="true"),
                      index=CLASES, columns=CLASES).round(3)
    return reporte, cm, f1_score(y, pred, labels=CLASES, average="macro", zero_division=0)