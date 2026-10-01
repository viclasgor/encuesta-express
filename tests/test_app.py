"""Smoke test: la app se dibuja entera sin excepciones (p. ej. IDs duplicados)."""
from streamlit.testing.v1 import AppTest


def test_app_renderiza_ejemplo_sin_errores():
    at = AppTest.from_file("../app.py")
    at.session_state["usar_ejemplo"] = True
    at.run(timeout=90)
    assert not at.exception, at.exception
    # Un grafico por pregunta no-texto del ejemplo (3 cat + 1 multiple + 1 escala)
    assert len(at.get("plotly_chart")) >= 5
    # Las cuatro pestañas existen (Inicio en vez de Resumen)
    assert [t.label for t in at.tabs] == ["Inicio", "Informe", "Cruces", "Exportar"]


def test_app_vacia_muestra_heroe_y_pasos_sin_errores():
    at = AppTest.from_file("../app.py")
    at.run(timeout=90)
    assert not at.exception, at.exception
    assert [t.label for t in at.tabs] == ["Inicio", "Informe", "Cruces", "Exportar"]
    html = " ".join(str(h.value) for h in at.get("html"))
    assert "Sube tu encuesta" in html and "Explora y descarga" in html
