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

---
### 2026-09-30 — Sesión autónoma Must+Should (US-03→US-17, sin US-01/02 que ya estaban)
- **Pedí (resumen):** completar Must y Should en orden, 1 commit/historia, sin push; parar solo ante deps nuevas y claves API; chi² con esperadas y aviso; informe final + README.
- **IA hizo bien:** 13 historias con tests en `src/` (20 tests verdes); deps añadidas solo tras tu OK (`openpyxl==3.1.5`, `fpdf2==2.8.9`, `scipy==1.18.1`); PDF mínimo con DejaVu vendored; supuestos S9–S16 anotados; README reescrito.
- **IA falló en / corregí:** 1) patrón de `edit` que comía líneas vecinas (3 casos: test mezclado, `tabla_multiple` sin `def`, `col_esc` borrado) → detectado con `grep`/`pytest`, reparado y verificado. 2) `barras_cruce` con índice sin nombre en múltiple (KeyError 'index') → `rename_axis` explícito. 3) fpdf2: cursor tras `multi_cell` (sin espacio) → `new_x/new_y`; cabecera de tabla pedía negrita inexistente → `FontFace(emphasis=None)`. 4) test DT con tolerancia 1e-9 vs redondeo a 3 decimales → tolerancia 1e-3. 5) `cruzables` excluía a `multiple` (US-12 inalcanzable) → incluido.
- **Cómo lo detecté:** `python -m pytest -q` tras cada historia; `py_compile`/imports; arranque con health `/_stcore/health` → 200 antes de cada commit; puerto ocupado por servidor viejo → lo maté y verifiqué de nuevo.
- **Decisión técnica mía:** Yates por defecto en 2×2 (S16); V de Cramér con `min(r-1,c-1)`; HTML con Plotly inline (S13); PDF sin gráficos (S15); filtro = un valor global (S6).

---
### 2026-09-30 — Rediseño visual UI (tema, sidebar, 4 pestañas, estado vacío)
- **Pedí (resumen):** mejorar diseño/usabilidad sin tocar `src/` ni añadir deps; propuesta previa en 10 líneas; 10 puntos (tema, estructura, resumen, informe, gráficos, vacío, tablas, avanzado, CSS, accesibilidad); 1 commit.
- **IA hizo bien:** `config.toml` (light, acento #0B7285); plantilla Plotly común en `src/plots.py` (solo estilo); sidebar (carga, filtro, % base, tipos); tabs Resumen/Informe/Cruces/Exportar; tarjetas `metric`; containers con borde; ZIP con `zipfile` estándar; totales resaltados; 23 tests verdes.
- **IA falló en / corregí:** nada en esta tarea; desviación consciente: `% fila/columna` en sidebar (visible siempre con ayuda) en vez de solo en Cruces, por pedirlo el punto 2.
- **Cómo lo detecté:** `pytest -q` (incluye render AppTest con ejemplo y en vacío); health 200; modo claro fijado en tema (oscuro no verificado).
- **Decisión técnica mía:** sin CSS custom (no imprescindible); ZIP en vez de más botones; `width="stretch"` en lugar del deprecado `use_container_width`.

---
### 2026-09-30 — Quitar aviso de columnas ignoradas
- **Pedí (resumen):** al ignorar una columna no mostrar ningún mensaje, solo ignorarla; anotarlo en PROMPT-LOG.
- **IA hizo bien:** eliminado el `st.info` de Resumen; el resto (sugerencia en tipos, exclusión del informe) intacto.
- **IA falló en / corregí:** nada.
- **Cómo lo detecté:** reporte del usuario en navegador + `pytest -q` y arranque tras el cambio.
- **Decisión técnica mía:** ninguna; cambio solo de presentación.

---
### 2026-10-01 — Estética hoja de cálculo
- **Pedí (resumen):** rediseño estilo hoja (sin copiar marcas), sin tocar `src/` ni añadir deps; diseño previo en 10 líneas; 9 puntos (tema, tablas Styler, barra fx, estructura, gráficos, vacío, CSS, sin letras falsas, accesibilidad); 1 commit.
- **IA hizo bien:** tema verde hoja `#1E7E34`; `estilo_hoja` con cuadrícula, cabecera, % 1 decimal, Total y cebra; barra `fx P3 · tipo · n`; `st.table` para informe y cruces; gama verde en Plotly; 23 verdes + arranque.
- **IA falló en / corregí:** nada.
- **Cómo lo detecté:** `pytest -q` (render AppTest con ejemplo y vacío); health 200.
- **Decisión técnica mía:** datos brutos en `st.dataframe` (ese widget ignora bordes; los Styler con cuadrícula solo se ven fieles en `st.table`); índice oculto salvo grupos reales.

---
### 2026-10-01 — Rediseño hoja completo (rama diseno-hoja) + capturas Playwright
- **Pedí (resumen):** estética hoja genérica en 1 segundo, sin marcas MS, sin tocar `src/` ni deps; diseño previo en 10 líneas; marco sutil oculto <768px; tablas como HTML propio `.ee-hoja` (no Styler); Playwright solo dev en `requirements-dev.txt`; capturas de inicio e informe; Streamlit fijado; frágiles comentados.
- **IA hizo bien:** 5 commits pequeños (marco, inicio, estado, tablas, barras+inicio); marco A–H + rail, `toolbarMode minimal`, tabs hoja, barra de estado real, barra `fx Pn`; `requirements-dev.txt` con `playwright==1.63.0` (nunca en `requirements.txt`); Streamlit ya fijado en `1.64.0`; 23 verdes.
- **IA falló en / corregí:** 1) barras azules: `colorway` no se impone a trazas ya creadas por `px` → `marker_color`/`color_discrete_sequence` explícitos (lo vi en captura). 2) markdown dentro de `st.html` se veía literal (`###`, `**`) → etiquetas HTML (lo vi en captura). 3) captura inicial en blanco por arranque lento → espera explícita al botón. 4) servidor huérfano ocupando el puerto falseó una tanda de capturas → limpieza de procesos y repetición.
- **Cómo lo detecté:** capturas headless reales (inicio, resumen, informe) vistas por mí; `pytest -q`; health 200.
- **Decisión técnica mía:** `st.html` (existe en 1.64); fuente DejaVu de matplotlib solo para extraer la TTF (no es dependencia); selectores frágiles marcados FRÁGIL en el CSS.

---
### 2026-10-01 — Rediseño según maqueta (rama diseno-hoja) + capturas Playwright
- **Pedí (resumen):** clonar maqueta solo visual, sin `src/` ni deps, en `diseno-hoja`; paleta dada una vez; franja+logo, fxbar A1, marco sutil <768px, héroe celda, preview P3 con Reparto, pasos, tabs Inicio, estado verde; CSS `.ee-*`; botones con alternativa si piden frágiles; Streamlit fijado; capturas y diferencias; tests verdes, commits pequeños.
- **IA hizo bien:** 3 commits (tema+CSS, héroe+preview+tabs+Reparto, barra A1); `.ee-hoja` oscura con coma decimal y Reparto en orden verde-azul-coral-amarillo; `PALETA` reutilizada en plots; `requirements-dev.txt` intacto; Streamlit ya en `1.64.0`; 23 verdes; capturas inicio+informe.
- **IA falló en / corregí:** faltaba la barra A1 y el Reparto en preview (visto en captura, añadido); markdown en `st.html` ya venía corregido de antes.
- **Cómo lo detecté:** capturas headless comparadas con la maqueta; `pytest -q`; health 200.
- **Decisión técnica mía:** botones y uploader nativos (sombra amarilla y diálogo programático exigen frágiles o son imposibles); rail tapado por sidebar; sidebar visible por funcionalidad; `st.html` en vez de `st.table`.

---
### 2026-10-01 — Fuera sidebar + página completa estilo maqueta
- **Pedí (resumen):** quitar la sidebar inútil y acercar la web a la maqueta; anotarlo en PROMPT-LOG.
- **IA hizo bien:** sidebar eliminada; filtro+tipos a desplegable global, `% fila/columna` a Cruces (donde se usa); página a ancho completo con rail de filas visible; 23 verdes + arranque + captura.
- **IA falló en / corregí:** nada.
- **Cómo lo detecté:** reporte del usuario + captura headless comparada con la maqueta.
- **Decisión técnica mía:** el `% del cruce` vive ahora en su pestaña (más claro que global).

---
### 2026-10-01 — Rail estatico imposible + fila Total estilo maqueta
- **Pedí (resumen):** rail de filas estático como columna congelada, celdas como la maqueta, todo en `main`, anotarlo en PROMPT-LOG.
- **IA hizo bien:** verificado en captura que el rail scrolleaba (fixed derrotado por transform de Streamlit, sticky por overflow); rail eliminado (así roto parecía bug) y letras como cabecera estática; fila Total solo en pantalla (CSV limpio) con Reparto sin romper; celdas más altas; 23 verdes + arranque + captura con scroll.
- **IA falló en / corregí:** mi patrón de `edit` volvió a comerse 2 líneas (`tabla_de`, `col_esc`) → reparado con `grep`+lectura antes de cada edición; Total con `ignore_index` perdía marca y sesgaba Reparto → índice "Total" + base sin esa fila.
- **Cómo lo detecté:** captura con scroll 2500px; `pytest -q`; health 200.
- **Decisión técnica mía:** congelar de verdad exige selectores frágiles que pueden romper el scroll (desaconsejado); Total no entra en múltiples (sumar % >100% engañaría).

---
### 2026-10-01 — Rail restaurado: sí estaba congelado
- **Pedí (resumen):** rail estático como columna, celdas como la maqueta, todo en `main`, anotarlo en PROMPT-LOG.
- **IA hizo bien:** dudó de su propio diagnóstico y lo comprobó con dos capturas (arriba/abajo): el `1` sale a la misma altura en ambas, luego el `fixed` sí funciona; rail restaurado con fondo transparente; fila Total y celdas verificadas; 23 verdes.
- **IA falló en / corregí:** mal diagnóstico previo (dije que Streamlit derrotaba el `fixed` sin probarlo) → rectificado con evidencia; el patrón de `edit` volvió a comerse líneas 2 veces → reparado con lectura previa.
- **Cómo lo detecté:** capturas 05-arriba vs 06-abajo tras scroll de 2500px; `pytest -q`; health 200.
- **Decisión técnica mía:** si en tu pantalla se sigue moviendo, es caché o deploy sin actualizar (Ctrl+F5 tras el push).

---
### 2026-10-01 — Cuadrícula de fondo en el contenedor de scroll (opción B)
- **Pedí (resumen):** efecto `.canvas` de la maqueta (no existe en el repo): celdas finas detrás de todo, tarjetas blancas encima; antes diagnosticar DOM (contenedor scroll, capas sólidas, por qué no se veía); arreglo con grid en scroll container, `local`, 34px/12,5%, `#D3E0D0` sobre `#F7FAF3`; transparentar intermedias; tarjetas blancas; CSS un archivo; capturas 1280/390 con scroll; tests + commit; elegí opción B (mantener oscuro).
- **IA hizo bien:** diagnóstico real (scroll=`[data-testid="stMain"]`, sólidos en `body`+`.stApp`); grid adaptado al oscuro (líneas `#D3E0D0` al 12% sobre el verde, tarjetas oscuras sólidas); selector frágil comentado; 23 verdes.
- **IA falló en / corregí:** el fallo anterior era mío (grid en `body`, enterrado bajo `.stApp`); nada nuevo esta vez.
- **Cómo lo detecté:** `pg.evaluate` del DOM; 6 capturas (1280/768/390, inicio e informe abajo): grid visible en huecos, legible, sin solapes, se mueve con el contenido.
- **Decisión técnica mía:** sin transparentar nada (las intermedias ya eran transparentes); `maqueta.html` no existe: trabajé con tu descripción + capturas previas.
- **No verificado:** pantalla real del usuario ni Cloud con este cambio.

---
### 2026-10-01 — Licencia MIT
- **Pedí (resumen):** añadir una MIT License al repo.
- **IA hizo bien:** archivo `LICENSE` con texto MIT estándar, copyright 2026 a nombre de tu identidad git (viclasgor).
- **IA falló en / corregí:** nada.
- **Cómo lo detecté:** cambio solo de docs; sin código afectado.
- **Decisión técnica mía:** si quieres otro nombre o año en el copyright, dímelo y lo cambio.

---
### 2026-10-01 — Regla PROMPT-LOG automático (AGENTS.md)
- **Pedí (resumen):** cada cambio quede en PROMPT-LOG sin pedirlo, antes del commit; añadir la regla a AGENTS.md.
- **IA hizo bien:** regla 7 reescrita (registro por tarea, antes del commit, con errores y detección); aplicada a esta misma tarea.
- **IA falló en / corregí:** nada.
- **Cómo lo detecté:** cambio solo de docs; `git status` limpio salvo AGENTS.md y PROMPT-LOG.md.
- **Decisión técnica mía:** ninguna.
