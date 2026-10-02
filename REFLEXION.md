# Informe de reflexión — EncuestaExpress

## 1. Qué hizo la IA
Propuso el stack (Streamlit + pandas + Plotly + pytest, todo fijado con `==`)
y diseñó el alcance por incrementos con criterios de aceptación medibles.
Generó la lógica completa en `src/`: carga con Sniffer (`;`/latin-1),
detección de tipos, frecuencias, multirrespuesta sobre respondientes, cruces,
chi-cuadrado con `scipy` (Yates por defecto en 2×2, bloqueo si <80% de
esperadas ≥5), exportaciones (HTML con Plotly embebido, PDF dibujado con
`rect`+texto vía fpdf2 sin Kaleido, CSV/ZIP/XLSX) y `@st.cache_data` en la
ruta caliente. Generó 27 tests (incluido render headless con AppTest),
README, DESPLIEGUE, licencia MIT y el PROMPT-LOG con modelo por sesión.

## 2. Qué hicimos nosotros
La idea fue mía: estudié Marketing y los Excel de las encuestas me daban
quebraderos de cabeza, así que quise una web donde subir el CSV y obtener el
informe. Yo le di el maquetado (estética de hoja, franja verde, barra `fx`,
tablas con reparto) y la conduje con prompts que preparaba con ayuda de Claude,
una cosa cada vez y sin avanzar hasta que funcionaba. La decisión técnica que
defiendo también fue mía: los números no los calcula ningún modelo, los calcula
código determinista (pandas/scipy), y por eso se pueden testear (`pytest -q`
en verde en pantalla). Mientras programábamos yo hacía push a GitHub y lo
comprobaba en Streamlit; analizaba los errores, se los decía y los corregíamos.

## 3. Qué errores cometió la IA y cómo los detectamos
- **Edits que comían líneas** (`tabla_multiple` sin `def`, `col_esc` borrado).
  Detectado con `grep` + lectura antes de cada edición. Aprendizaje: verificar
  el hunk, no fiarse del "reemplazo correcto".
- **`pd.to_numeric(list)`** devuelve ndarray sin `.notna` → la escala caía a
  categórica. Cazado por `pytest` (1 fallo). Aprendizaje: los tests pillan lo
  que el ojo no ve.
- **Barras azules y markdown literal**: `colorway` no se impone a trazas ya
  creadas; `###` dentro de `st.html` no se interpreta. Vistos en captura
  headless. Aprendizaje: lo visual solo se verifica viendo.
- **Diagnóstico falso del rail**: afirmó que Streamlit derrotaba el `fixed`
  sin probarlo; dos capturas (arriba/abajo) lo desmintieron. Aprendizaje:
  evidencia antes que teoría.
- **Módulos viejos en Cloud**: tras un pull, `sys.modules` conservaba
  `src.analysis` sin `frecuencia_palabras` → `ImportError` de una línea.
  Se arregla con Reboot. Aprendizaje: en Cloud, ante error raro tras push,
  reiniciar antes de tocar código.
- **Alucinación de alcance**: propuso cosas fuera de lo pedido (o con
  dependencias nuevas) sin avisar del coste. Lo frené con la regla de
  "preguntar antes de añadir".

## 4. Conclusión
La IA es rapidísima escribiendo, pero sin dirección entrega cosas que casi
funcionan: yo puse el problema, los límites, la maqueta, los casos de prueba
y la decisión de no meter el modelo donde están los números. Sin esa
dirección tendríamos porcentajes mal calculados y tests que no existen; con
ella, una app útil, desplegada y explicable en 5 minutos: `pytest -q` en verde.
