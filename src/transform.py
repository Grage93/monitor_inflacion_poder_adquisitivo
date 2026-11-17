"""Cruza IPC y salarios y calcula el salario real y su evolución."""
from pathlib import Path

import pandas as pd

DATA = Path("data")


def cargar_ipc_trimestral() -> pd.DataFrame:
    """IPC mensual -> media trimestral (solo trimestres con 3 meses)."""
    ipc = pd.read_csv(DATA / "ipc_raw.csv", parse_dates=["fecha"])
    ipc["trimestre"] = ipc["fecha"].dt.to_period("Q")

    trimestral = (
        ipc.groupby(["geo", "trimestre"])
        .agg(ipc=("ipc", "mean"), meses=("ipc", "count"))
        .reset_index()
    )
    return trimestral[trimestral["meses"] == 3].drop(columns="meses")


def rebasar_2020(df: pd.DataFrame) -> pd.DataFrame:
    """Reexpresa el IPC con base 2020 = 100 (media de los 4 trimestres de 2020)."""
    base = df[df["trimestre"].dt.year == 2020].groupby("geo")["ipc"].mean()
    df = df.copy()
    df["ipc_2020"] = df["ipc"] / df["geo"].map(base) * 100
    return df.drop(columns="ipc")


def cargar_salarios() -> pd.DataFrame:
    sal = pd.read_csv(DATA / "salarios_raw.csv")
    sal["trimestre"] = pd.PeriodIndex(sal["trimestre"], freq="Q")
    return sal[["geo", "trimestre", "salario_idx"]]


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["geo", "trimestre"]).copy()

    # Salario real: salario nominal deflactado por los precios
    df["salario_real"] = df["salario_idx"] / df["ipc_2020"] * 100

    # Variaciones interanuales (%) respecto al mismo trimestre del año anterior
    for origen, destino in [
        ("ipc_2020", "inflacion_yoy"),
        ("salario_idx", "salario_nominal_yoy"),
        ("salario_real", "salario_real_yoy"),
    ]:
        df[destino] = df.groupby("geo")[origen].pct_change(4) * 100

    return df.reset_index(drop=True)


def main() -> None:
    ipc = rebasar_2020(cargar_ipc_trimestral())
    salarios = cargar_salarios()

    datos = ipc.merge(salarios, on=["geo", "trimestre"], how="inner")
    datos = calcular_indicadores(datos)

    salida = DATA / "datos_procesados.csv"
    datos.to_csv(salida, index=False)

    print(f"Guardado en {salida} ({len(datos)} filas)")
    resumen = datos.groupby("geo").tail(2).copy()
    resumen["trimestre"] = resumen["trimestre"].astype(str)
    print(resumen.round(2).to_string(index=False))


if __name__ == "__main__":
    main()