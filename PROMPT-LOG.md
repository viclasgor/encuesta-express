# PROMPT-LOG — EncuestaExpress

> 1 entrada por sesión importante. Sirve para demostrar dirección de la IA en la defensa. Plantilla obligatoria:

| Fecha | Objetivo | Prompt resumido | Qué hizo la IA | Qué corregí yo | Errores IA detectados |
|---|---|---|---|---|---|
| _ | _ | _ | _ | _ | _ |

## Detalle por sesión
### Plantilla detalle
- **Fecha / objetivo:**
- **Pedí (resumen):**
- **IA hizo bien:**
- **IA falló en / corregí:**
- **Cómo lo detecté (prueba/lectura):**
- **Decisión técnica mía:**

---
### 2026-09-30 — Planificación sin código (PROBLEMA, ALCANCE, BACKLOG, AGENTS)
- **Pedí:** actuar como tech lead, máx 5 preguntas, luego crear docs/PROBLEMA, docs/ALCANCE, docs/BACKLOG, AGENTS.md y PROMPT-LOG sin escribir código, esperando aprobación.
- **IA hizo bien:** preguntó antes de escribir (CSV, tipos, exportación, cruce, deploy); generó 5 docs alineados a respuestas (UTF-8/coma, tipos 4 salidas, cruce cat×cat y escala×cat sin tests, HTML autónomo, solo local); anotó supuestos S1-S4.
- **IA falló en / corregí:** pendiente de tu revisión — valida si backlog/incrementos y supuestos te valen antes de implementar.
- **Cómo lo detecté:** leer docs generados vs tus respuestas; falta crear `data/ejemplo_encuesta.csv` (aprobación pendiente).
- **Decisión técnica mía (propuesta):** Streamlit+pandas+Plotly+pytest, `src/analysis.py` puro separado de `app.py`; primer incremento US-01+US-02 E2E.

---
### 2026-09-30 — Incremento 1 (US-01+US-02) + CSV ejemplo + test tipos + Cloud
- **Pedí (resumen):** aprobar orden y S1-S4; crear `data/ejemplo_encuesta.csv` + test detección; empezar Incremento 1; correr tests, arrancar app, preparar Cloud; dejar el log solo con este proyecto.
- **IA hizo bien:** CSV 8 filas; `src/analysis.py` puro (`cargar_csv`, `detectar_tipo`, `tabla_frecuencias`); `tests/test_analysis.py` (carga, tipos, frecuencias); `app.py` mínimo E2E; `docs/DESPLIEGUE.md`; ALCANCE actualizado (Cloud pasa de FUERA a opción documentada).
- **IA falló en / corregí:** 1) `pd.to_numeric(list)` devuelve ndarray sin `.notna` → escala caía a categórica; corregido con `pd.Series`. 2) `pip install` cortado por timeout y `python -m streamlit` sin módulo; reinstalado con `python -m pip`. 3) Arranque inicial falló; verificado tras reinstalar (health 200).
- **Cómo lo detecté:** `python -m pytest -q` (1 fallo en escala); `python -m streamlit run` (No module named streamlit); health check `/_stcore/health` → 200.
- **Decisión técnica mía:** validada la tuya (Must→Should, S1-S4, Cloud ahora documentado); heurística múltiple exige ≥2 celdas con ", " para no confundir texto con coma.
