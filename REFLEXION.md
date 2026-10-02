# Informe de reflexión — EncuestaExpress (1-2 páginas)

## 1. Qué hizo la IA
Generó la planificación (PROBLEMA, ALCANCE, BACKLOG, AGENTS.md), el CSV de ejemplo,
toda la lógica de análisis en `src/` (carga, detección de tipos, frecuencias,
cruces, chi-cuadrado, exportaciones), la UI en Streamlit, los 27 tests y la
documentación (DESPLIEGUE, README, PROMPT-LOG con 18 sesiones). Propuso la
arquitectura (pandas puro separado de la UI), las dependencias con versiones
fijadas y los supuestos S1–S18 del alcance.

## 2. Qué hice yo (dirección)
Definí el producto y sus reglas: cálculos deterministas, nunca un LLM en la ruta
de cálculo; incrementos pequeños con aprobación; parar ante dependencias y claves;
Cloud como criterio de hecho con local de plan B; congelación el 6/10. Corregí
decisiones de alcance (chi-cuadrado solo con esperadas válidas, PDF sin Kaleido,
múltiples sin test) y todo el diseño visual con maqueta y capturas. Probé la app
en navegador y en Cloud, y aporté los fallos que los tests no veían (rail móvil,
botones duplicados, CSV con punto y coma).

## 3. Errores de la IA y cómo los detecté
- **Edits que comían líneas vecinas** (3+ casos: `tabla_multiple` sin `def`,
  `col_esc` borrado). Detectado con `grep` + lectura antes de cada edición;
  desde entonces verifico el hunk antes de dar por bueno un cambio.
- **`pd.to_numeric(list)`** devuelve ndarray sin `.notna` → la escala caía a
  categórica. Cazado por `pytest` (1 fallo); fix con `pd.Series`.
- **fpdf2**: cursor tras `multi_cell` y cabecera pidiendo negrita inexistente.
  Cazados por el test del PDF; fix con `new_x/new_y` y `FontFace(emphasis=None)`.
- **Barras azules**: `colorway` no se impone a trazas ya creadas → colores
  explícitos. Visto en captura headless, no en tests.
- **Diagnóstico falso del rail**: afirmé que Streamlit derrotaba el `fixed`
  sin probarlo; dos capturas (arriba/abajo) demostraron lo contrario.
  Aprendizaje: verificar con evidencia antes de sentenciar.
- **Puerto ocupado y capturas falseadas** por servidores huérfanos: ahora mato
  el proceso y compruebo el puerto antes de cada tanda.

## 4. Aprendizaje y decisión técnica (defensa, 5 min)
La decisión: **los números no los calcula un modelo, los calcula pandas
(y scipy), y por eso se pueden testear** — `pytest -q` en verde en pantalla,
27 tests. Dirigir a la IA en historias pequeñas y verificables (un commit por
historia, tests + arranque antes de avanzar) rindió más que pedirle todo de
golpe; y los fallos visuales solo salieron con capturas reales, nunca con tests.
