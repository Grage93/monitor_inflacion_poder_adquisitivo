"""Análisis econométrico sencillo del poder adquisitivo en Europa."""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

DATA = Path("data")
DOCS = Path("docs")


def cargar_indicadores() -> pd.DataFrame:
    con = sqlite3.connect(DATA / "monitor.db")
    df = pd.read_sql_query("SELECT * FROM indicadores", con)
    con.close()
    df["trimestre"] = pd.PeriodIndex(df["trimestre"], freq="Q")
    return df.sort_values(["geo", "trimestre"]).reset_index(drop=True)


def tendencia_salario_real(df: pd.DataFrame) -> pd.DataFrame:
    """Crecimiento anual medio del salario real: log(salario_real) ~ tiempo."""
    filas = []
    for geo, g in df.groupby("geo"):
        anios = np.arange(len(g)) / 4          # tiempo medido en años
        X = sm.add_constant(anios)
        y = np.log(g["salario_real"].to_numpy())
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
        filas.append({
            "geo": geo,
            "crecimiento_anual_%": res.params[1] * 100,
            "p_valor": res.pvalues[1],
            "r2": res.rsquared,
        })
    return pd.DataFrame(filas).round(3)


def traslado_inflacion_salarios(df: pd.DataFrame) -> pd.DataFrame:
    """Regresión: salario_nominal_yoy ~ inflacion_yoy (por país)."""
    filas = []
    for geo, g in df.dropna(subset=["inflacion_yoy", "salario_nominal_yoy"]).groupby("geo"):
        X = sm.add_constant(g["inflacion_yoy"])
        res = sm.OLS(g["salario_nominal_yoy"], X).fit(
            cov_type="HAC", cov_kwds={"maxlags": 4}
        )
        filas.append({
            "geo": geo,
            "traslado": res.params["inflacion_yoy"],
            "p_valor": res.pvalues["inflacion_yoy"],
            "r2": res.rsquared,
        })
    return pd.DataFrame(filas).round(3)


def grafico_salario_real(df: pd.DataFrame) -> None:
    DOCS.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    for geo, g in df[df["trimestre"].dt.year >= 2015].groupby("geo"):
        ax.plot(g["trimestre"].dt.to_timestamp(), g["salario_real"], label=geo)
    ax.axhline(100, color="grey", linestyle="--", linewidth=0.8)
    ax.set_title("Salario real (índice 2020 = 100)")
    ax.set_ylabel("Índice")
    ax.legend()
    fig.tight_layout()
    fig.savefig(DOCS / "salario_real.png", dpi=150)
    plt.close(fig)


def main() -> None:
    df = cargar_indicadores()

    tendencia = tendencia_salario_real(df)
    traslado = traslado_inflacion_salarios(df)

    print("\nCrecimiento anual medio del salario real (log-lineal, errores HAC):")
    print(tendencia.to_string(index=False))
    print("\nTraslado de la inflación a los salarios nominales:")
    print(traslado.to_string(index=False))

    tendencia.to_csv(DATA / "resultado_tendencia.csv", index=False)
    traslado.to_csv(DATA / "resultado_traslado.csv", index=False)
    grafico_salario_real(df)
    print(f"\nGráfico guardado en {DOCS / 'salario_real.png'}")


if __name__ == "__main__":
    main()