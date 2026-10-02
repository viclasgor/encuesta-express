from datetime import date
from src.analysis import cargar_csv, tabla_frecuencias
from src.plots import barras_horizontales
from src.export_html import generar_informe_html, tabla_a_csv, tablas_a_xlsx

CSV = "data/ejemplo_encuesta.csv"


def test_html_autonomo_con_tablas_y_grafico(tmp_path):
    df = cargar_csv(CSV)
    t = tabla_frecuencias(df["Rango de edad"])
    bloques = [
        {"pregunta": "Rango de edad", "tipo": "categorica",
         "resumen": "n válido: 8",
         "tabla_html": t.to_html(index=False),
         "fig": barras_horizontales(t)},
        {"pregunta": "¿Qué mejorarías?", "tipo": "texto",
         "resumen": "5 respuestas", "tabla_html": "", "fig": None},
    ]
    html = generar_informe_html("EncuestaExpress: demo", str(date.today()), 8, bloques)
    assert "<html" in html and "plotly" in html
    assert "Rango de edad" in html and "25-34" in html
    out = tmp_path / "informe.html"
    out.write_text(html, encoding="utf-8")
    assert out.stat().st_size > 50_000  # lleva Plotly embebido (offline)


def test_csv_de_tabla_con_n_y_pct():
    import io
    import pandas as pd
    df = cargar_csv(CSV)
    t = tabla_frecuencias(df["Rango de edad"])
    texto = tabla_a_csv(t)
    assert texto.splitlines()[0] == "categoria,n,pct"
    de_vuelta = pd.read_csv(io.StringIO(texto))
    assert de_vuelta["n"].sum() == 8


def test_xlsx_con_hojas_recuperables():
    import io
    import pandas as pd
    df = cargar_csv(CSV)
    data = tablas_a_xlsx({"Edades: 1/2": tabla_frecuencias(df["Rango de edad"]),
                          "Texto? *[]": pd.DataFrame({"respuesta": ["hola"]})})
    assert data[:4] == b"PK\x03\x04"  # zip = xlsx
    de_vuelta = pd.read_excel(io.BytesIO(data), sheet_name=None)
    assert de_vuelta["Edades_ 1_2"]["n"].sum() == 8
    assert list(de_vuelta["Texto_ ___"].columns) == ["respuesta"]
