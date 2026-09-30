import pandas as pd
from src.analysis import cargar_csv, detectar_tipos, tabla_frecuencias

CSV = "data/ejemplo_encuesta.csv"


def test_carga_8_filas_7_columnas():
    df = cargar_csv(CSV)
    assert len(df) == 8
    assert len(df.columns) == 7


def test_deteccion_tipos_columnas():
    df = cargar_csv(CSV)
    tipos = detectar_tipos(df)
    assert tipos["Marca temporal"] == "temporal"
    assert tipos["Rango de edad"] == "categorica"
    assert tipos["¿Con qué frecuencia compras café fuera de casa?"] == "categorica"
    assert tipos["¿Qué factores influyen en tu elección?"] == "multiple"
    assert tipos["Valora de 1 a 5 tu satisfacción con las cafeterías de tu zona"] == "escala"
    # Rangos como categorias, no numeros
    assert tipos["¿Cuánto gastas al mes en café fuera de casa?"] == "categorica"
    assert tipos["¿Qué mejorarías?"] == "texto"


def test_frecuencias_rango_edad_suman_100():
    df = cargar_csv(CSV)
    t = tabla_frecuencias(df["Rango de edad"])
    assert t.attrs["n_valido"] == 8
    assert t.attrs["n_total"] == 8
    assert abs(t["pct"].sum() - 100.0) < 0.2
    # 25-34 aparece 3 veces -> 37.5%
    fila = t[t["categoria"] == "25-34"].iloc[0]
    assert fila["n"] == 3
