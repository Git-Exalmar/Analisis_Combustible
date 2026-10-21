"""Indicadores del modelo PU de paradas y búsqueda del punto de corte.

Dos evaluaciones, porque en PU no hay negativas perfectas:
  A) Cala registrada vs todo el resto  -> COTA INFERIOR (el resto incluye calas no registradas).
  B) Cala registrada vs paradas en puerto -> COTA SUPERIOR (negativas seguras pero fáciles).
El rendimiento real está entre ambas.

Punto de corte recomendado: criterio de Lee y Liu (2003), recall² / P(predicho = cala),
pensado para PU porque no necesita negativas.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (roc_auc_score, roc_curve, accuracy_score, precision_score,
                             recall_score, f1_score, confusion_matrix, average_precision_score)

def metricas(y, prob, umbral):
    pred = (prob >= umbral).astype(int)
    auc = roc_auc_score(y, prob)
    return {"AUC-ROC": auc, "Gini": 2 * auc - 1, "AP (área PR)": average_precision_score(y, prob),
            "Accuracy": accuracy_score(y, pred), "Precision": precision_score(y, pred, zero_division=0),
            "Recall": recall_score(y, pred), "F1": f1_score(y, pred, zero_division=0)}

def evaluar(p, c, umbral_base=0.5, carpeta=None):
    """p y c salen de entrenar_pu(). Devuelve (tabla de métricas, tabla de cortes, mejores cortes)."""
    # A) PU: cala registrada (1) vs todo el resto (0). El "resto" incluye calas no
    #    registradas, así que estas métricas son una COTA INFERIOR del rendimiento real.
    yA, probA = p["s"].to_numpy(), p["P_registrada"].to_numpy()
    # B) Limpio: cala registrada (1) vs paradas en puerto (0). Las negativas son seguras
    #    pero fáciles, así que estas métricas son una COTA SUPERIOR.
    #    Se usa la probabilidad del modelo SIN forzar el puerto a 0 (si no, sería trampa).
    p = p.assign(P_modelo=np.clip(p["P_registrada"] / c, 0, 1))
    lim = (p["s"] == 1) | p["puerto"]
    yB, probB = p.loc[lim, "s"].to_numpy(), p.loc[lim, "P_modelo"].to_numpy()

    tabla = pd.DataFrame({
        "A · PU (cota inferior)": metricas(yA, probA, umbral_base * c),
        "B · vs puerto (cota superior)": metricas(yB, probB, umbral_base),
    }).round(3)

    # Punto de corte sobre P_cala
    umbrales = np.round(np.arange(0.05, 0.96, 0.01), 2)
    pc = p["P_modelo"].to_numpy()
    filas = []
    for u in umbrales:
        pred = pc >= u
        rec = pred[yA == 1].mean()                       # recall sobre calas registradas
        p_pos = pred.mean()                              # proporción predicha como cala
        lee_liu = rec ** 2 / p_pos if p_pos > 0 else 0   # criterio PU (Lee y Liu, 2003)
        predB = probB >= u
        tpr, fpr = predB[yB == 1].mean(), predB[yB == 0].mean()
        filas.append({"umbral": u, "recall_registradas": rec, "pct_predicho_cala": p_pos,
                      "Lee_Liu": lee_liu, "Youden_vs_puerto": tpr - fpr,
                      "F1_vs_puerto": f1_score(yB, predB.astype(int), zero_division=0)})
    cortes = pd.DataFrame(filas)
    mejor = {
        "Lee-Liu (PU, recomendado)": cortes.loc[cortes["Lee_Liu"].idxmax(), "umbral"],
        "Youden (vs puerto)": cortes.loc[cortes["Youden_vs_puerto"].idxmax(), "umbral"],
        "F1 (vs puerto)": cortes.loc[cortes["F1_vs_puerto"].idxmax(), "umbral"],
    }

    fig, ax = plt.subplots(1, 3, figsize=(17, 4.5))
    for y, prob, nombre in [(yA, probA, "A · PU"), (yB, probB, "B · vs puerto")]:
        f, t, _ = roc_curve(y, prob)
        ax[0].plot(f, t, label=f"{nombre} (AUC {roc_auc_score(y, prob):.3f})")
    ax[0].plot([0, 1], [0, 1], "--", color="gray"); ax[0].set_title("Curva ROC")
    ax[0].set_xlabel("Falsos positivos"); ax[0].set_ylabel("Verdaderos positivos"); ax[0].legend()
    ax[1].plot(cortes["umbral"], cortes["Lee_Liu"] / cortes["Lee_Liu"].max(), label="Lee-Liu (normalizado)")
    ax[1].plot(cortes["umbral"], cortes["recall_registradas"], label="Recall calas registradas")
    ax[1].plot(cortes["umbral"], cortes["pct_predicho_cala"], label="% predicho como cala")
    ax[1].axvline(mejor["Lee-Liu (PU, recomendado)"], color="black", ls="--")
    ax[1].set_title("Punto de corte"); ax[1].set_xlabel("umbral sobre P(cala)"); ax[1].legend()
    u = mejor["Lee-Liu (PU, recomendado)"]
    cm = confusion_matrix(yB, (probB >= u).astype(int))
    ax[2].imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax[2].text(j, i, f"{v:,}", ha="center", va="center", color="white" if v > cm.max() / 2 else "black")
    ax[2].set_xticks([0, 1], ["no cala", "cala"]); ax[2].set_yticks([0, 1], ["puerto", "cala registrada"])
    ax[2].set_title(f"Matriz (B) con umbral {u}")
    plt.tight_layout()
    if carpeta: plt.savefig(carpeta)
    return tabla, cortes, mejor