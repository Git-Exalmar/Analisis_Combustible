"""Limpia faenas y calas de Silver y guarda los viajes en data/processed/.

Uso (desde la raíz del proyecto, después de extraer_datos):
    py -m scripts.preparar_viajes
"""
import pandas as pd

from src.config import DIR_DATA_PROC, DIR_DATA_RAW
from src.faenas import construir_viajes, unir_solapados


def main() -> None:
    faenas = pd.read_parquet(DIR_DATA_RAW / "silver" / "faenas.parquet")
    calas = pd.read_parquet(DIR_DATA_RAW / "silver" / "calas.parquet")
    print(f"Entrada: {len(faenas):,} faenas, {len(calas):,} calas")

    viajes, calas_v, obs = construir_viajes(faenas, calas)
    viajes_ok, calas_ok = unir_solapados(viajes, calas_v)
    unidos = int(viajes["Valido"].sum()) - len(viajes_ok)
    obs.loc[len(obs)] = ["viajes solapados unidos (cortes a medianoche)", unidos]

    print("\nLimpieza aplicada:")
    print(obs.to_string(index=False))
    print(f"\nSalida: {len(viajes_ok):,} viajes válidos, {len(calas_ok):,} calas")

    DIR_DATA_PROC.mkdir(parents=True, exist_ok=True)
    viajes_ok.to_parquet(DIR_DATA_PROC / "viajes.parquet", index=False)
    calas_ok.to_parquet(DIR_DATA_PROC / "calas.parquet", index=False)
    obs.to_csv(DIR_DATA_PROC / "limpieza_viajes.csv", index=False)
    # los inválidos también se guardan, para poder revisarlos
    viajes[~viajes["Valido"]].to_parquet(DIR_DATA_PROC / "viajes_invalidos.parquet", index=False)
    print(f"Guardado en {DIR_DATA_PROC}")


if __name__ == "__main__":
    main()