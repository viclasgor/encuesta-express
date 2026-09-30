import pandas as pd
from src.analysis import (
    cargar_csv, detectar_tipos, sugerir_ignorar, resumen_escala,
    distribucion_escala, listar_texto, perfil_muestra,
    tabla_frecuencias, tabla_multiple, cruce_cat_cat, cruce_escala_cat,
    cruce_multiple_cat, aplicar_filtro,
)

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


def test_sugerir_ignorar_solo_temporal_y_email():
    assert sugerir_ignorar("temporal") is True
    assert sugerir_ignorar("email") is True
    for t in ("categorica", "multiple", "escala", "texto"):
        assert sugerir_ignorar(t) is False


def test_frecuencias_rango_edad_suman_100():
    df = cargar_csv(CSV)
    t = tabla_frecuencias(df["Rango de edad"])
    assert t.attrs["n_valido"] == 8
    assert t.attrs["n_total"] == 8
    assert abs(t["pct"].sum() - 100.0) < 0.2
    # 25-34 aparece 3 veces -> 37.5%
    fila = t[t["categoria"] == "25-34"].iloc[0]
    assert fila["n"] == 3


def test_multiple_pct_sobre_respondientes():
    df = cargar_csv(CSV)
    t = tabla_multiple(df["¿Qué factores influyen en tu elección?"])
    assert t.attrs["n_respondientes"] == 8
    assert t.attrs["n_total"] == 8
    d = dict(zip(t["opcion"], t["menciones"]))
    assert d == {"Precio": 5, "Ubicación": 4, "Calidad": 4, "Ambiente": 3}
    assert t[t["opcion"] == "Precio"].iloc[0]["pct_resp"] == 62.5
    assert t["pct_resp"].sum() > 100  # % sobre respondientes, no sobre menciones


def test_escala_media_mediana_dt_y_distribucion():
    df = cargar_csv(CSV)
    col = "Valora de 1 a 5 tu satisfacción con las cafeterías de tu zona"
    r = resumen_escala(df[col])
    assert r["media"] == 3.625
    assert r["mediana"] == 4.0
    assert abs(r["dt"] - float(pd.Series([4, 3, 4, 5, 2, 4, 3, 4]).std())) < 1e-3  # se muestran 3 decimales
    assert r["n_valido"] == 8 and r["n_total"] == 8
    d = distribucion_escala(df[col])
    assert dict(zip(d["valor"], d["n"])) == {2: 1, 3: 2, 4: 4, 5: 1}
    assert abs(d["pct"].sum() - 100.0) < 0.2


def test_texto_lista_sin_vacios_y_perfil():
    df = cargar_csv(CSV)
    respuestas = listar_texto(df["¿Qué mejorarías?"])
    assert len(respuestas) == 5  # 3 vacíos de 8
    assert respuestas[0] == "Más opciones de leche vegetal"
    p = perfil_muestra(df)
    assert p["n_total"] == 8
    assert p["n_valido_por_columna"]["¿Qué mejorarías?"] == 5
    assert p["n_valido_por_columna"]["Rango de edad"] == 8


def test_cruce_cat_cat_con_totales_y_pct():
    df = cargar_csv(CSV)
    r = cruce_cat_cat(df["Rango de edad"], df["¿Con qué frecuencia compras café fuera de casa?"])
    assert r["excluidos"] == 0
    assert r["n"].loc["Total", "Total"] == 8
    assert r["pct"].sum(axis=1).round(0).tolist() == [100.0] * 4
    rb = cruce_cat_cat(df["Rango de edad"], df["¿Con qué frecuencia compras café fuera de casa?"],
                       base="columna")
    assert rb["pct"].sum(axis=0).round(0).tolist() == [100.0] * 4


def test_cruce_excluye_vacios_e_informa():
    df = cargar_csv(CSV)
    r = cruce_cat_cat(df["Rango de edad"], df["¿Qué mejorarías?"])
    assert r["excluidos"] == 3
    assert r["n"].loc["Total", "Total"] == 5


def test_cruce_escala_cat_medias_por_grupo():
    df = cargar_csv(CSV)
    col_esc = "Valora de 1 a 5 tu satisfacción con las cafeterías de tu zona"
    r = cruce_escala_cat(df[col_esc], df["Rango de edad"])
    assert r["excluidos"] == 0
    d = dict(zip(r["tabla"]["grupo"], r["tabla"]["media"]))
    assert d == {"18-24": 3.0, "25-34": 3.667, "35-44": 4.0, "45-54": 4.0}
    assert dict(zip(r["tabla"]["grupo"], r["tabla"]["n"])) == {
        "18-24": 2, "25-34": 3, "35-44": 2, "45-54": 1}


def test_cruce_multiple_cat_pct_sobre_grupo():
    df = cargar_csv(CSV)
    r = cruce_multiple_cat(df["¿Qué factores influyen en tu elección?"], df["Rango de edad"])
    assert r["excluidos"] == 0
    t = r["tabla"]
    prow = t[(t["grupo"] == "18-24") & (t["opcion"] == "Precio")].iloc[0]
    assert (prow["menciones"], prow["n_grupo"], prow["pct"]) == (2, 2, 100.0)
    urow = t[(t["grupo"] == "45-54") & (t["opcion"] == "Ubicación")].iloc[0]
    assert (urow["menciones"], urow["n_grupo"], urow["pct"]) == (1, 1, 100.0)


def test_filtro_global_por_valor():
    df = cargar_csv(CSV)
    f = aplicar_filtro(df, "Rango de edad", "25-34")
    assert len(f) == 3
    assert len(aplicar_filtro(df, "Rango de edad", "Todos")) == 8
    assert len(aplicar_filtro(df, None, None)) == 8
    assert len(aplicar_filtro(df, "Rango de edad", "18-24")) == 2
