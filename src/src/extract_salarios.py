"""Descarga el índice de salarios (costes laborales) trimestral de Eurostat."""
import re
from pathlib import Path

import eurostat
import pandas as pd

DATASET = "lc_lci_r2_q"
PAISES = ["ES", "DE", "FR", "IT", "PT", "EA"]
RUTA_SALIDA = Path("data") / "salarios_raw.csv"


def descargar_salarios() -> pd.DataFrame:
    filtros = {
        "freq": "Q",
        "s_adj": "SCA",        # ajustado por estacionalidad y calendario
        "unit": "I20",         # índice, base 2020 = 100
        "nace_r2": "B-S",      # industria, construcción y servicios
        "lcstruct": "D11",     # sueldos y salarios
        "geo": PAISES,
    }
    df = eurostat.get_data_df(DATASET, filter_pars=filtros)
    if df is None or df.empty:
        raise ValueError("Eurostat no devolvió datos. Revisa los filtros.")
    return df


def a_formato_largo(df: pd.DataFrame) -> pd.DataFrame:
    """Una columna por trimestre -> una fila por país y trimestre."""
    col_geo = [c for c in df.columns if str(c).startswith("geo")][0]
    df = df.rename(columns={col_geo: "geo"})

    # Las columnas de periodo tienen formato AAAA-Q1, AAAA-Q2...
    id_cols = [c for c in df.columns if not re.fullmatch(r"\d{4}-Q[1-4]", str(c))]

    largo = df.melt(id_vars=id_cols, var_name="trimestre", value_name="salario_idx")
    largo["trimestre"] = pd.PeriodIndex(
        largo["trimestre"].str.replace("-", ""), freq="Q"
    )
    largo = largo.dropna(subset=["salario_idx"]).sort_values(["geo", "trimestre"])
    return largo.reset_index(drop=True)


def main() -> None:
    datos = a_formato_largo(descargar_salarios())

    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    datos.to_csv(RUTA_SALIDA, index=False)

    print(f"Guardado en {RUTA_SALIDA}")
    print(datos.groupby("geo")["trimestre"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()