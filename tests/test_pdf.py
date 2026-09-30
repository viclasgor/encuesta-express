import os
from src.analysis import cargar_csv, tabla_frecuencias, listar_texto
from src.export_pdf import generar_pdf, FUENTE

CSV = "data/ejemplo_encuesta.csv"


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
