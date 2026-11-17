"""Carga los CSV en una base de datos SQLite y lanza una consulta de prueba."""
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
DB = DATA / "monitor.db"


def main() -> None:
    ipc = pd.read_csv(DATA / "ipc_raw.csv", parse_dates=["fecha"])
    ipc = ipc[["geo", "fecha", "ipc"]]
    ipc["fecha"] = ipc["fecha"].dt.strftime("%Y-%m-%d")

    salarios = pd.read_csv(DATA / "salarios_raw.csv")[["geo", "trimestre", "salario_idx"]]
    indicadores = pd.read_csv(DATA / "datos_procesados.csv")

    con = sqlite3.connect(DB)
    ipc.to_sql("ipc_mensual", con, if_exists="replace", index=False)
    salarios.to_sql("salarios_trimestral", con, if_exists="replace", index=False)
    indicadores.to_sql("indicadores", con, if_exists="replace", index=False)

    consulta = """
        SELECT geo, trimestre, inflacion_yoy, salario_nominal_yoy, salario_real_yoy
        FROM indicadores
        WHERE trimestre = (SELECT MAX(trimestre) FROM indicadores)
        ORDER BY salario_real_yoy DESC
    """
    print(f"Base de datos creada en {DB}\n")
    print(pd.read_sql_query(consulta, con).round(2).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()