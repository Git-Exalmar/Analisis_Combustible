"""Limpieza de faenas y construcción de viajes y calas.

Entradas (de scripts/extraer_datos.py):
- faenas: una fila por faena (sql/operacion/faenas.sql)
- calas:  una fila por cala, con IdFaena y FechaHoraCala (sql/operacion/calas.sql)

Ojo: FechaHoraCala es la hora REGISTRADA de la cala, que en la práctica es su FIN
(ver claude/ml-actividad-embarcaciones.md). Por eso se llama HoraRegistrada.
"""
import pandas as pd


def preparar(faenas: pd.DataFrame, calas: pd.DataFrame):
    """Tipos y nombres normalizados."""
    f = faenas.copy()
    for c in [c for c in f.columns if c.startswith("FechaHora")]:
        f[c] = pd.to_datetime(f[c], errors="coerce")
    f["Embarcacion"] = f["Embarcacion"].astype(str).str.strip().str.upper()
    if "PuertoZarpe" in f:
        f["PuertoZarpe"] = f["PuertoZarpe"].str.strip().str.upper()
    c = calas.rename(columns={"FechaHoraCala": "HoraRegistrada"}).copy()
    c["HoraRegistrada"] = pd.to_datetime(c["HoraRegistrada"], errors="coerce")
    c = c.dropna(subset=["IdFaena", "HoraRegistrada"]).drop_duplicates(["IdFaena", "HoraRegistrada"])
    return f, c


def construir_viajes(faenas: pd.DataFrame, calas: pd.DataFrame):
    """Une las faenas de una misma salida y corrige errores de fechas.

    Devuelve (viajes, calas, observaciones). Un viaje = misma embarcación +
    misma FechaHoraZarpe ('Espera en zona' comparte zarpe con su faena principal).
    """
    obs = []
    df, c = preparar(faenas, calas)

    # 1. Fechas imposibles (año futuro)
    malas = df["FechaHoraZarpe"].dt.year > pd.Timestamp.now().year
    obs.append(("zarpe con año futuro (descartadas)", int(malas.sum())))
    df = df[~malas]

    # 2. Calas con la clave de viaje (embarcación + zarpe) de su faena
    clave = ["IND_IdEmbarcacion", "FechaHoraZarpe"]
    obs.append(("calas duplicadas (misma faena y hora, descartadas)",
                int(calas.dropna(subset=["IdFaena"]).duplicated(["IdFaena", "FechaHoraCala"]).sum())))
    n_tabla = len(c)
    c = c.merge(df[["IdFaena"] + clave], on="IdFaena", how="inner")
    obs.append(("calas sin faena válida (descartadas)", int(n_tabla - len(c))))
    c["FuenteCala"] = "tabla de calas"

    # 2b. Faenas sin IdFaena: sus calas no están en la tabla de calas.
    #     Respaldo parcial con la primera y la última cala que trae la faena.
    sin_id = df[df["IdFaena"].isna()]
    respaldo = pd.concat([
        sin_id[clave + [col]].rename(columns={col: "HoraRegistrada"})
        for col in ["FechaHoraPrimeraCala", "FechaHoraUltimaCala"] if col in sin_id
    ]).dropna(subset=["HoraRegistrada"]).drop_duplicates()
    respaldo["IdFaena"] = pd.NA
    respaldo["FuenteCala"] = "faena (sin IdFaena)"
    obs.append(("calas de respaldo para faenas sin IdFaena", len(respaldo)))
    c = pd.concat([c, respaldo], ignore_index=True)

    # 2c. Control: faenas donde NumeroCalas no coincide con la tabla de calas
    if "NumeroCalas" in df:
        conteo = c[c["FuenteCala"] == "tabla de calas"].groupby("IdFaena").size()
        con_id = df[df["IdFaena"].notna()].set_index("IdFaena")
        dif = con_id["NumeroCalas"].fillna(0) != conteo.reindex(con_id.index).fillna(0)
        obs.append(("faenas con NumeroCalas distinto a la tabla (se usa la tabla)", int(dif.sum())))

    # 3. Un registro por viaje: se prioriza el que tiene arribo real
    prioridad = df["FechaHoraArriboReal"].notna().astype(int) * 2 + \
                (df["EstadoFaena"] != "Espera en zona").astype(int)
    df = df.assign(_p=prioridad).sort_values("_p", ascending=False)
    ids = df.groupby(clave)["IdFaena"].apply(lambda s: sorted(s.dropna().astype(int).tolist()))
    viajes = (df.drop_duplicates(clave).drop(columns=["_p"])
                .merge(ids.rename("IdsFaena"), on=clave))
    obs.append(("faenas unidas al mismo viaje", len(df) - len(viajes)))

    # 4. Calas del viaje (todas sus faenas), en orden
    c = c.drop_duplicates(clave + ["HoraRegistrada"]).sort_values(clave + ["HoraRegistrada"])
    resumen = c.groupby(clave)["HoraRegistrada"].agg(PrimeraCala="min", UltimaCala="max", NCalas="size")
    viajes = viajes.merge(resumen, on=clave, how="left")
    viajes["NCalas"] = viajes["NCalas"].fillna(0).astype(int)

    # 5. Zarpe registrado un día después (zarpe > primera cala)
    error_dia = viajes["FechaHoraZarpe"] > viajes["PrimeraCala"]
    corregible = error_dia & (viajes["FechaHoraZarpe"] - pd.Timedelta(days=1) < viajes["PrimeraCala"])
    viajes["ZarpeCorregido"] = viajes["FechaHoraZarpe"].where(
        ~corregible, viajes["FechaHoraZarpe"] - pd.Timedelta(days=1))
    obs.append(("zarpe posterior a la 1ra cala (corregido -1 día)", int(corregible.sum())))

    # 6. Fin del viaje: arribo real; si falta, estimado
    viajes["FinViaje"] = viajes["FechaHoraArriboReal"].fillna(viajes["FechaHoraArriboEstimado"])
    viajes["FuenteFin"] = (viajes["FechaHoraArriboReal"].notna().map({True: "real", False: "estimado"})
                           .where(viajes["FinViaje"].notna(), "sin dato"))

    # 7. Validaciones
    dur = (viajes["FinViaje"] - viajes["ZarpeCorregido"]).dt.total_seconds() / 3600
    viajes["DuracionH"] = dur
    viajes["Valido"] = dur.between(0.5, 120) & ~(error_dia & ~corregible)
    viajes.loc[viajes["UltimaCala"] > viajes["FinViaje"], "Valido"] = False
    obs.append(("viajes inválidos (sin fin, duración fuera de 0.5–120 h o calas fuera del viaje)",
                int((~viajes["Valido"]).sum())))

    viajes = viajes.sort_values(["Embarcacion", "ZarpeCorregido"]).reset_index(drop=True)
    viajes.insert(0, "IdViaje", viajes.index + 1)
    c = c.merge(viajes[["IdViaje"] + clave], on=clave)
    c["NumCala"] = c.groupby("IdViaje").cumcount() + 1
    c = _tiempo_disponible(c[["IdViaje", "NumCala", "IdFaena", "HoraRegistrada", "FuenteCala"]], viajes)
    return viajes, c, pd.DataFrame(obs, columns=["observacion", "filas"])


def _tiempo_disponible(c: pd.DataFrame, viajes: pd.DataFrame) -> pd.DataFrame:
    """Minutos desde cada cala hasta la siguiente (o hasta el fin del viaje)."""
    fin = c["IdViaje"].map(viajes.set_index("IdViaje")["FinViaje"])
    sig = c.groupby("IdViaje")["HoraRegistrada"].shift(-1).fillna(fin)
    c = c.copy()
    c["MaxDuracionMin"] = (sig - c["HoraRegistrada"]).dt.total_seconds() / 60
    return c


def unir_solapados(viajes: pd.DataFrame, calas: pd.DataFrame):
    """Une viajes válidos de una misma embarcación cuyos intervalos se cruzan
    (p. ej. una salida registrada partida a medianoche)."""
    v = viajes[viajes["Valido"]].sort_values(["Embarcacion", "ZarpeCorregido"]).copy()
    fin_previo = v.groupby("Embarcacion")["FinViaje"].transform(lambda s: s.cummax().shift())
    v["Grupo"] = (v["ZarpeCorregido"] > fin_previo).fillna(True).groupby(v["Embarcacion"]).cumsum()

    agg = v.groupby(["Embarcacion", "Grupo"]).agg(
        IdViaje=("IdViaje", "first"),
        IdsViajeOriginal=("IdViaje", list),
        IdsFaena=("IdsFaena", lambda s: sorted(sum(s, []))),
        IND_IdEmbarcacion=("IND_IdEmbarcacion", "first"),
        PuertoZarpe=("PuertoZarpe", "first"),
        EstadoFaena=("EstadoFaena", "last"),
        ZarpeCorregido=("ZarpeCorregido", "min"),
        FinViaje=("FinViaje", "max"),
        FuenteFin=("FuenteFin", lambda s: "real" if (s == "real").all() else "estimado"),
    ).reset_index().drop(columns="Grupo")

    mapa = {o: n for n, lst in zip(agg["IdViaje"], agg["IdsViajeOriginal"]) for o in lst}
    c = calas[calas["IdViaje"].isin(mapa)].copy()
    c["IdViaje"] = c["IdViaje"].map(mapa)
    c = c.drop_duplicates(["IdViaje", "HoraRegistrada"]).sort_values(["IdViaje", "HoraRegistrada"])
    c["NumCala"] = c.groupby("IdViaje").cumcount() + 1
    c = _tiempo_disponible(c.drop(columns="MaxDuracionMin"), agg)

    res = c.groupby("IdViaje")["HoraRegistrada"].agg(PrimeraCala="min", UltimaCala="max", NCalas="size")
    agg = agg.merge(res, on="IdViaje", how="left")
    agg["NCalas"] = agg["NCalas"].fillna(0).astype(int)
    agg["DuracionH"] = (agg["FinViaje"] - agg["ZarpeCorregido"]).dt.total_seconds() / 3600
    return agg.drop(columns="IdsViajeOriginal"), c.reset_index(drop=True)