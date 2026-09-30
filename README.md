# EncuestaExpress

Sube el CSV de tu encuesta (Google Forms) y obtén un informe automático: perfil de muestra, tablas + gráficos por pregunta, cruce entre dos preguntas y descarga en HTML.

Cálculos deterministas con pandas. Sin LLM para calcular. Despliegue en Streamlit Community Cloud; local como plan B.

> URL Cloud: _PEGAR AQUÍ TU URL DE STREAMLIT CLOUD_ (criterio de hecho del MVP).

## Funcionalidades MVP
- Carga CSV estándar Forms (UTF-8, coma) + vista previa y n total.
- Autodetección de tipos (timestamp, escala 1-5, única, múltiple, texto, email) con corrección manual.
- Por pregunta: única → tabla n/% + barras H; múltiple → % sobre respondientes + barras H; escala → media/mediana/DT + barras V; texto → listado.
- Cruce cat×cat y escala×cat con aviso si grupo <5.
- Exporta informe HTML autónomo (abre offline).

## Stack
- Python 3.10+, Streamlit, pandas, Plotly, pytest.

## Ejecutar en local (plan B para la demo)
```powershell
pip install -r requirements.txt
streamlit run app.py
pytest -q
```
Demo con `data/ejemplo_encuesta.csv`.

## Estructura
- `app.py` — UI Streamlit
- `src/analysis.py` — lógica pandas pura
- `src/plots.py`, `src/export_html.py`
- `tests/`, `data/`, `docs/`
- `AGENTS.md`, `PROMPT-LOG.md`

## Docs
- `docs/PROBLEMA.md`, `docs/ALCANCE.md`, `docs/BACKLOG.md`

Estado: Incremento 1 (US-01+US-02) implementado y verificado en local; pendiente tu prueba en navegador + deploy Cloud.
