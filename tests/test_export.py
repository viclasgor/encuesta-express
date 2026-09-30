from datetime import date
from src.analysis import cargar_csv, tabla_frecuencias
from src.plots import barras_horizontales
from src.export_html import generar_informe_html

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
