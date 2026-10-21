"""Etiquetado por reglas (etiquetas débiles) de la actividad de cada registro."""
import numpy as np
import pandas as pd

CALA, IDA, BUSQUEDA, RETORNO = "cala", "ida", "busqueda", "retorno"
ENTRADA, SALIDA = "entrada_cala", "salida_cala"
SIN_VIAJE, SIN_CALA = "sin_viaje", "viaje_sin_cala"


def ventanas_finales(ventanas: pd.DataFrame, dur_min=30, dur_max=150, dur_defecto=75,
                     desfase_fin=(-30, 45)) -> pd.DataFrame:
    """Define Inicio y Fin definitivos de cada cala.

    - Fin: el detectado por telemetría si es coherente con la hora registrada;
      si no, la hora registrada (que en la práctica es el fin de la cala).
    - Inicio: el detectado si la duración es razonable; si no, Fin - dur_defecto.
    """
    v = ventanas.copy()
    fin_ok = v["CalaDetectada"] & v["DesfaseFinMin"].between(*desfase_fin)
    v["Fin"] = v["FinCalaEst"].where(fin_ok, v["HoraRegistrada"])
    dur_ok = fin_ok & v["DuracionEstMin"].between(dur_min, dur_max)
    v["Inicio"] = v["InicioCalaEst"].where(dur_ok, v["Fin"] - pd.Timedelta(minutes=dur_defecto))
    v["MetodoVentana"] = np.select([dur_ok, fin_ok], ["telemetria", "fin_telemetria"], "regla")
    return v[["IdViaje", "NumCala", "HoraRegistrada", "Inicio", "Fin", "MetodoVentana"]]


def etiquetar(tel_v: pd.DataFrame, ventanas: pd.DataFrame, vel_crucero=8.5,
              registros_sostenido=2, min_transicion=35, vel_detenida=2.0,
              registros_entrada=1) -> pd.DataFrame:
    """Asigna una etiqueta a cada registro de telemetría con viaje.

    Reglas por viaje con calas:
      cala     -> dentro de [Inicio, Fin] de alguna cala
      retorno  -> después del Fin de la última cala
      ida      -> desde el zarpe hasta la primera vez que la velocidad baja de
                  vel_crucero durante `registros_sostenido` registros seguidos
      busqueda -> el resto antes de la primera cala y entre calas
      entrada_cala -> el (los `registros_entrada`) último(s) registro(s) en movimiento (>= vel_detenida) dentro de los
                  `min_transicion` minutos previos al inicio de la cala (frenado y cerco)
      salida_cala  -> el primer registro en movimiento dentro de los `min_transicion`
                  minutos posteriores al fin de la cala (arranque)
    Viajes sin calas -> 'viaje_sin_cala'; registros sin viaje -> 'sin_viaje'.
    """
    t = tel_v.sort_values(["ep", "fecha"]).copy()
    t["Etiqueta"] = np.where(t["IdViaje"].isna(), SIN_VIAJE, SIN_CALA)
    t["NumCala"] = pd.NA

    vent = ventanas.sort_values(["IdViaje", "Inicio"])
    con_viaje = t["IdViaje"].notna()
    for id_viaje, idx in t[con_viaje].groupby("IdViaje").groups.items():
        w = vent[vent["IdViaje"] == id_viaje]
        if w.empty:
            continue
        f = t.loc[idx, "fecha"]
        etiqueta = pd.Series(BUSQUEDA, index=idx)

        for _, c in w.iterrows():
            dentro = f.between(c["Inicio"], c["Fin"])
            etiqueta[dentro] = CALA
            t.loc[dentro[dentro].index, "NumCala"] = c["NumCala"]
        etiqueta[f > w["Fin"].max()] = RETORNO

        # ida: desde el zarpe hasta que deja la velocidad de crucero de forma sostenida
        antes = f < w["Inicio"].min()
        vel = t.loc[idx, "Velocidad"][antes]
        lento = (vel < vel_crucero).astype(int)
        sostenido = lento.rolling(registros_sostenido).sum().eq(registros_sostenido)
        if sostenido.any():
            pos = sostenido.to_numpy().argmax() - (registros_sostenido - 1)
            fin_ida = vel.index[pos]
            ida_idx = vel.index[:list(vel.index).index(fin_ida)]
        else:
            ida_idx = vel.index
        etiqueta[ida_idx] = IDA

        # transiciones: se aplican al final para que prevalezcan sobre ida/búsqueda/retorno
        vel_v = t.loc[idx, "Velocidad"]
        margen = pd.Timedelta(minutes=min_transicion)
        for _, c in w.iterrows():
            previos = f[(f >= c["Inicio"] - margen) & (f < c["Inicio"])].index
            previos = [i for i in previos if vel_v[i] >= vel_detenida and etiqueta[i] != CALA][-registros_entrada:]
            etiqueta[previos] = ENTRADA
            siguientes = f[(f > c["Fin"]) & (f <= c["Fin"] + margen)].index
            siguientes = [i for i in siguientes if vel_v[i] >= vel_detenida and etiqueta[i] != CALA][:1]
            etiqueta[siguientes] = SALIDA

        t.loc[idx, "Etiqueta"] = etiqueta
    return t


ESPERA, PUERTO, MAR_SIN_FAENA = "espera", "puerto", "mar_sin_faena"


def etiquetar_completo(tel_f: pd.DataFrame, ventanas_reg: pd.DataFrame, paradas_pu: pd.DataFrame,
                       umbral_cala=0.5, umbral_no_cala=0.2, min_transicion=35, vel_detenida=2.0) -> pd.DataFrame:
    """Etiquetas finales para entrenar el modelo por registro.

    - Calas = registradas (ventanas_reg) + paradas del modelo PU con P_cala >= umbral_cala.
    - Dentro de viaje: reglas de etiquetar() con todas esas calas (ida, búsqueda,
      entrada, cala, salida, retorno).
    - Paradas con P_cala < umbral_no_cala que no están en puerto -> espera.
    - Fuera de viaje: puerto (Estado == 'puerto'); calas PU con su entrada y salida;
      el resto queda como 'mar_sin_faena' (SIN etiqueta: no se usa para entrenar).
    """
    pu = paradas_pu.copy()
    nuevas = pu[(pu["s"] == 0) & (pu["P_cala"] >= umbral_cala)]
    v_nuevas = nuevas.loc[nuevas["IdViaje"].notna(), ["IdViaje", "inicio", "fin"]].rename(
        columns={"inicio": "Inicio", "fin": "Fin"})
    v_nuevas["MetodoVentana"] = "modelo_pu"
    ventanas = pd.concat([ventanas_reg, v_nuevas], ignore_index=True)
    ventanas["IdViaje"] = ventanas["IdViaje"].astype("Int64")

    t = etiquetar(tel_f, ventanas, min_transicion=min_transicion, vel_detenida=vel_detenida)

    # Fuera de viaje
    fuera = t["IdViaje"].isna()
    t.loc[fuera, "Etiqueta"] = np.where(t.loc[fuera, "Estado"].eq("puerto"), PUERTO, MAR_SIN_FAENA) \
        if "Estado" in t else MAR_SIN_FAENA
    margen = pd.Timedelta(minutes=min_transicion)
    for _, c in nuevas[nuevas["IdViaje"].isna()].iterrows():
        m = fuera & (t["ep"] == c["ep"])
        f = t.loc[m, "fecha"]
        t.loc[f[f.between(c["inicio"], c["fin"])].index, "Etiqueta"] = CALA
        antes = f[(f >= c["inicio"] - margen) & (f < c["inicio"])].index
        antes = [i for i in antes if t.at[i, "Velocidad"] >= vel_detenida][-1:]
        t.loc[antes, "Etiqueta"] = ENTRADA
        despues = f[(f > c["fin"]) & (f <= c["fin"] + margen)].index
        despues = [i for i in despues if t.at[i, "Velocidad"] >= vel_detenida][:1]
        t.loc[despues, "Etiqueta"] = SALIDA

    # Esperas: paradas claramente no-cala fuera de puerto (dentro o fuera de viaje)
    esperas = pu[(pu["P_cala"] < umbral_no_cala) & (pu["dist_puerto_km"] > 5)]
    for _, e in esperas.iterrows():
        m = (t["ep"] == e["ep"]) & t["fecha"].between(e["inicio"], e["fin"]) & (t["Etiqueta"] != CALA)
        t.loc[m, "Etiqueta"] = ESPERA
    return t