"""Proceso de scoring. Uso (desde la raíz del proyecto):

    py -m scripts.scoring                    # prueba: guarda el resultado en data/scoring/
    py -m scripts.scoring --destino sql      # producción: escribe en ml.ActividadEmbarcacion
    py -m scripts.scoring --ahora "2026-05-20 14:00"   # repetición: como si fuera esa fecha y hora
"""
import argparse
import datetime as dt

from src.config import RAIZ
from src.scoring import (ahora_peru, cargar_paquete, leer_telemetria_reciente, puntuar,
                         ultimo_por_embarcacion, escribir_sql, registrar_proceso)


def main():
    ap = argparse.ArgumentParser(description="Clasifica la actividad de la flota con la telemetría reciente")
    ap.add_argument("--destino", choices=["archivo", "sql"], default="archivo")
    ap.add_argument("--horas-escribir", type=float, default=6,
                    help="ventana que se reescribe en cada ejecución (cubre datos que llegan tarde)")
    ap.add_argument("--ahora", type=dt.datetime.fromisoformat, default=None,
                    help="simula que el proceso corre en esa fecha y hora de Perú (para probar con temporada pasada)")
    a = ap.parse_args()

    inicio_real = ahora_peru()             # cuándo corre de verdad (para la bitácora)
    inicio = a.ahora or inicio_real        # hora de referencia de los datos (simulada con --ahora)
    paquete = cargar_paquete()
    print(f"[{inicio:%Y-%m-%d %H:%M}] modelo {paquete['version']} · historia {paquete['horas_historia']} h")
    try:
        tel = leer_telemetria_reciente(paquete["horas_historia"], inicio)
        res = puntuar(tel, paquete, inicio)
        desde = inicio - dt.timedelta(hours=a.horas_escribir)
        nuevos = res[res["fecha"] >= desde]
        ret = ultimo_por_embarcacion(res, inicio)

        print(f"Leídos: {len(tel):,} · puntuados: {len(res):,} · a escribir (últimas {a.horas_escribir:g} h): {len(nuevos):,}")
        print("\nÚltimo registro por embarcación (minutos desde el último dato):")
        print(ret.round({"MinDesdeUltimo": 0}).to_string())
        print("\nActividad actual (último registro de cada embarcación):")
        actual = res.sort_values("fecha").groupby("ep").tail(1)
        print(actual[["ep", "fecha", "Velocidad", "Actividad", "Probabilidad"]].round({"Velocidad": 1, "Probabilidad": 2}).to_string(index=False))

        if a.destino == "archivo":
            carpeta = RAIZ / "data" / "scoring"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / f"actividad_{inicio:%Y%m%d_%H%M}.parquet"
            nuevos.to_parquet(ruta, index=False)
            print("\nGuardado:", ruta)
        else:
            n = escribir_sql(nuevos, desde, inicio)
            registrar_proceso(Inicio=inicio_real, Fin=ahora_peru(), RegistrosLeidos=len(tel), RegistrosEscritos=n,
                              UltimoRegistro=res["fecha"].max().to_pydatetime(),
                              MinDesdeUltimo=float(ret["MinDesdeUltimo"].min()),
                              VersionModelo=paquete["version"], Estado="ok")
            print(f"\nEscritos en ml.ActividadEmbarcacion: {n:,}")
    except Exception as e:
        if a.destino == "sql":
            registrar_proceso(Inicio=inicio_real, Fin=ahora_peru(), VersionModelo=paquete["version"],
                              Estado="error", Error=str(e)[:2000])
        raise


if __name__ == "__main__":
    main()