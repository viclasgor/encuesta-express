# AGENTS.md — EncuestaExpress

## Descripción
EncuestaExpress: app web local en Streamlit donde se sube un CSV de Google Forms y se obtiene informe descriptivo automático (perfil, frecuencias, gráficos, 1 cruce, export HTML). Cálculos deterministas con pandas, nunca con LLM. Usuario: no-programador que necesita resultados en minutos. Detalle en `docs/PROBLEMA.md`, `docs/ALCANCE.md`, `docs/BACKLOG.md`.

## Stack (no añadir sin preguntar)
- Python 3.10+, Streamlit, pandas, Plotly, pytest.
- Sin LLM en runtime, sin backend/BD, sin PDF/Word libs. HTML con Plotly/pandas embebido.

## Estructura propuesta
```
app.py                  # solo UI Streamlit, sin cálculos
src/analysis.py         # lógica pura pandas (detección tipos, frecuencias, cruces) — testeable
src/plots.py            # funciones que devuelven figuras Plotly (sin streamlit dentro)
src/export_html.py      # genera informe autónomo
tests/test_analysis.py  # tests deterministas con CSV ejemplo
data/ejemplo_encuesta.csv # demo café 8 filas (aportada por usuario, anonimizada)
docs/                   # PROBLEMA, ALCANCE, BACKLOG
requirements.txt
README.md
PROMPT-LOG.md
```

## Comandos
```powershell
pip install -r requirements.txt
streamlit run app.py
pytest -q
```

## Convenciones de código (para principiantes)
- Nombres en español de dominio (`frecuencias`, `cruce_cat_cat`), inglés técnico (`df`, `fig`).
- `src/analysis.py` solo recibe/retorna DataFrames/dicts, nunca llama `st.*`.
- Una función = una cosa (ej. `detectar_tipo`, `tabla_frecuencias`, `resumen_escala`).
- Vacios → "sin respuesta", excluidos de % pero contados en n total/válido.
- Comentarios cortos explicando el porqué, no el qué.

## Reglas de trabajo (obligatorias)
1. Incrementos pequeños: una historia de `docs/BACKLOG.md` cada vez; explica antes de implementar qué vas a hacer y espera el OK.
2. Separa lógica de análisis (módulo puro, testeable) de la interfaz (Streamlit).
3. No añadas dependencias, funcionalidades ni archivos fuera del backlog sin preguntar.
4. Si algo es ambiguo, pregunta en vez de suponer. Si es detalle menor que no cambia alcance/stack, elige lo más simple, anótalo como Supuesto en `docs/ALCANCE.md` y sigue.
5. Tras cada cambio: ejecuta la app o los tests y dime qué has verificado y qué no.
6. Explica decisiones técnicas en lenguaje sencillo (usuario principiante).
7. Al final de cada sesión, propón la entrada para `PROMPT-LOG.md`, incluyendo errores cometidos.
8. Incluye `data/ejemplo_encuesta.csv` para la demo (usar el ejemplo aportado).
9. No hardcodees secretos ni claves; no subas datos personales reales; ofrece ignorar columnas email.

## Definition of Done (por historia)
- [ ] Cumple criterios de aceptación del backlog y `docs/ALCANCE.md`.
- [ ] Lógica en `src/` con test pytest que pasa; UI solo presenta resultados.
- [ ] Verificado con `pytest -q` y/o `streamlit run` con CSV ejemplo; se indica qué se probó y qué queda sin probar.
- [ ] Sin deps/archivos extra; README actualizado si cambia instalación; PROMPT-LOG propuesto.
