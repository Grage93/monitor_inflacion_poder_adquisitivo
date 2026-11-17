"""Descarga el IPC armonizado (HICP) mensual de Eurostat para varios países."""
import re
from pathlib import Path

import eurostat
import pandas as pd

DATASET = "prc_hicp_minr"                      # IPC armonizado, ECOICOP v2 (desde 2026)
PAISES = ["ES", "DE", "FR", "IT", "PT", "EA"]  # EA = zona euro
RUTA_SALIDA = Path(__file__).resolve().parent.parent / "data" / "ipc_raw.csv"


def descargar_ipc() -> pd.DataFrame:
    """Pide a Eurostat el índice general de precios de cada país."""
    filtros = {
        "freq": "M",            # mensual
        "unit": "I15",          # índice con base 2015 = 100
        "coicop18": "TOTAL",    # todos los productos (índice general)
        "geo": PAISES,
    }
    df = eurostat.get_data_df(DATASET, filter_pars=filtros)
    if df is None or df.empty:
        raise ValueError(
            "Eurostat no devolvió datos. Revisa los filtros (unit, geo) "
            "o si el dataset ha cambiado."
        )
    return df


def a_formato_largo(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte una columna por mes en filas: país, fecha, valor del IPC."""
    # La columna del país se llama distinto según la versión de la librería
    col_geo = [c for c in df.columns if str(c).startswith("geo")][0]
    df = df.rename(columns={col_geo: "geo"})

    # Las columnas de fechas tienen formato AAAA-MM; el resto son identificadores
    id_cols = [c for c in df.columns if not re.fullmatch(r"\d{4}-\d{2}", str(c))]

    largo = df.melt(id_vars=id_cols, var_name="fecha", value_name="ipc")
    largo["fecha"] = pd.to_datetime(largo["fecha"])
    largo = largo.dropna(subset=["ipc"]).sort_values(["geo", "fecha"])
    return largo.reset_index(drop=True)


def main() -> None:
    bruto = descargar_ipc()
    datos = a_formato_largo(bruto)

    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    datos.to_csv(RUTA_SALIDA, index=False)

    print(f"Guardado en {RUTA_SALIDA}")
    print(datos.groupby("geo")["fecha"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
    