import pandas as pd
from src.analysis import cargar_csv, cruce_cat_cat
from src.chi2 import chi_cuadrado_cat

CSV = "data/ejemplo_encuesta.csv"


def _sin_totales(tabla):
    return tabla.drop(index="Total", errors="ignore").drop(columns="Total", errors="ignore")


def test_chi2_asociacion_clara():
    # [[30,10],[10,30]] con Yates: chi2=18.05, gl=1, V=0.475
    t = pd.DataFrame([[30, 10], [10, 30]], index=["a", "b"], columns=["x", "y"])
    r = chi_cuadrado_cat(t)
    assert r["aplicable"] is True
    assert r["gl"] == 1 and r["n"] == 80
    assert abs(r["chi2"] - 18.05) < 0.01
    assert r["p"] < 0.05
    assert abs(r["v_cramer"] - 0.475) < 0.01
    assert "Hay evidencia" in r["veredicto"] and "NO significa" in r["veredicto"]


def test_chi2_independencia():
    t = pd.DataFrame([[20, 20], [20, 20]], index=["a", "b"], columns=["x", "y"])
    r = chi_cuadrado_cat(t)
    assert r["aplicable"] is True
    assert r["chi2"] == 0.0 and r["p"] == 1.0 and r["v_cramer"] == 0.0
    assert "No hay evidencia" in r["veredicto"]


def test_chi2_no_aplicable_con_muestra_pequena():
    df = cargar_csv(CSV)  # n=8: esperadas demasiado bajas
    r = cruce_cat_cat(df["Rango de edad"], df["¿Con qué frecuencia compras café fuera de casa?"])
    out = chi_cuadrado_cat(_sin_totales(r["n"]))
    assert out["aplicable"] is False
    assert "esperadas" in out["motivo"]


def test_chi2_casos_limite_sin_fallar():
    assert chi_cuadrado_cat(pd.DataFrame([[5, 5]], index=["a"], columns=["x", "y"]))["aplicable"] is False
    assert chi_cuadrado_cat(pd.DataFrame(columns=["x", "y"]))["aplicable"] is False
