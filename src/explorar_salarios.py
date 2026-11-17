"""Explora qué dimensiones y valores ofrece un dataset de Eurostat."""
import eurostat

DATASET = "lc_lci_r2_q"

print(f"Dimensiones de {DATASET}:\n")
for parametro in eurostat.get_pars(DATASET):
    valores = eurostat.get_par_values(DATASET, parametro)
    print(f"- {parametro}: {valores[:20]}")