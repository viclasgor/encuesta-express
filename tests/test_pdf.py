import os
import re
from src.analysis import (cargar_csv, detectar_tipos, tabla_frecuencias, tabla_multiple,
                          resumen_escala, distribucion_escala, listar_texto, cruce_cat_cat)
from src.export_pdf import generar_pdf, FUENTE

CSV = "data/ejemplo_encuesta.csv"


def _paginas(pdf: bytes) -> int:
    return len(re.findall(rb"/Type /Page[^s]", pdf))


def test_pdf_no_vacio_con_portada_y_tablas():
    assert os.path.exists(FUENTE)  # tildes y € necesitan la TTF vendored
    df = cargar_csv(CSV)
    t = tabla_frecuencias(df["Rango de edad"])
    bloques = [
        {"pregunta": "Rango de edad", "resumen": "n válido: 8",
         "tabla": t[["categoria", "n", "pct"]]},
        {"pregunta": "¿Qué mejorarías? — Más opciones de leche vegetal, 10-20 €",
         "resumen": "5 respuestas", "tabla": None},
    ]
    pdf = generar_pdf("EncuestaExpress: demo", "2026-09-30", 8, bloques)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 3_000


def test_pdf_con_graficos_y_cruce_no_vacio():
    import pandas as pd
    df = cargar_csv(CSV)
    tipos = detectar_tipos(df)
    bloques = []
    for col in df.columns:
        t = tipos[col]
        if t in ("temporal", "email", "id", "ignorar"):
            continue
        if t == "texto":
            bloques.append({"pregunta": col, "resumen": "", "tabla": None,
                            "grafico": None})
        elif t == "escala":
            d = distribucion_escala(df[col])
            bloques.append({"pregunta": col, "resumen": "", "tabla": d,
                            "grafico": {"kind": "vbar",
                                         "etiquetas": [str(v) for v in d["valor"]],
                                         "valores": [float(v) for v in d["n"]]}})
        elif t == "multiple":
            m = tabla_multiple(df[col])
            bloques.append({"pregunta": col, "resumen": "", "tabla": m,
                            "grafico": {"kind": "hbar",
                                         "etiquetas": list(m["opcion"]),
                                         "valores": [float(v) for v in m["menciones"]],
                                         "pcts": [float(v) for v in m["pct_resp"]]}})
        else:
            f = tabla_frecuencias(df[col])
            bloques.append({"pregunta": col, "resumen": "", "tabla": f,
                            "grafico": {"kind": "hbar",
                                         "etiquetas": list(f["categoria"]),
                                         "valores": [float(v) for v in f["n"]],
                                         "pcts": [float(v) for v in f["pct"]]}})
    r = cruce_cat_cat(df["Rango de edad"], df["¿Con qué frecuencia compras café fuera de casa?"])
    n = r["n"].drop(index="Total").drop(columns="Total")
    cruce = {"titulo": "Cruce demo", "tabla": r["n"].reset_index(),
             "grafico": {"kind": "stacked", "filas": list(n.index),
                         "columnas": list(n.columns), "pct": r["pct"].values.tolist()}}
    pdf = generar_pdf("EncuestaExpress: demo gráficos", "2026-09-30", 8, bloques, cruce)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 15_000  # tablas + graficos dibujados
    assert _paginas(pdf) >= 3  # portada + preguntas + cruce
