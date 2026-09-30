# BACKLOG — EncuestaExpress (alcance ampliado, aprobado 30/09/2026)

Fechas: entrega 9/10 · congelación de funcionalidades 6/10 · demo 5 min 13/10.
Priorización: Must = sin esto no hay MVP; Should = valor comprometido si da tiempo; Could = solo si sobra antes del 6/10.
Estimación: S <2h, M medio día, L >1 día.
Reglas: cada incremento deja la app desplegable en Cloud y con `pytest -q` en verde; cálculos siempre en `src/` con tests; ninguna dependencia nueva sin confirmación explícita.

## Incremento 1 — E2E mínimo ✅ HECHO
> Subir CSV → ver una tabla y un gráfico.

- **US-01 [Must|S] ✅ Cargar CSV Forms y ver muestra**
  - CA: acepta UTF-8/coma del ejemplo (8 filas); muestra n total=8 + preview 5 filas; vacíos no rompen; error legible si otro separador/encoding.
- **US-02 [Must|M] ✅ Tabla + gráfico de 1 categórica única**
  - CA: para `Rango de edad` muestra tabla n y % (suma 100% sobre n válido), n válido/total, barras horizontales; coincide con cálculo pandas.

## Incremento 2 — Must: informe completo + UI cuidada
> Sin esto no hay "informe automático". Al terminar, la app muestra TODAS las preguntas.

- **US-03 [Must|M] Autodetección + corrección manual + privacidad**
  - CA: los 7 tipos del ejemplo se detectan bien (temporal, 3×categórica, múltiple, escala, texto); dropdown por columna para corregir o ignorar; email→sugerir ignorar; rangos "10-20 €" quedan como categoría.
- **US-04 [Must|M] Multirrespuesta correcta**
  - CA: `¿Qué factores...?` hace split por `", "`, cuenta menciones, % sobre respondientes (puede >100%), barras horizontales; se indica la base (n respondientes).
- **US-05 [Must|S] Escala 1-5**
  - CA: `Valora 1-5...` muestra media, mediana, DT, n válido/total + distribución en barras verticales; valores coinciden con pandas.
- **US-06 [Must|S] Texto abierto + perfil muestra**
  - CA: `¿Qué mejorarías?` lista paginada sin gráfico; vacíos excluidos; cabecera global con n total y n válido por pregunta.
- **US-11 [Must|M] UI cuidada**
  - CA: layout ancho; pestañas Informe / Cruces / Datos; tarjetas con n total, n válido y % válidos; ayuda expandible sobre el formato CSV esperado; sin cálculos en `app.py`.

## Incremento 3 — Must: cruces (incl. múltiples) + filtro
> Cruces de dos variables + segmentación global.

- **US-07 [Must|M] Cruce cat×cat**
  - CA: dos selects; tabla n y % con totales; toggle %fila (defecto)/columna; barras apiladas 100% (defecto)/agrupadas; informa nº excluidos por vacíos; aviso si algún grupo <5.
- **US-08 [Must|S] Cruce escala×cat**
  - CA: ej. satisfacción media por edad: tabla media+DT+n por grupo y barras de medias; mismo manejo de vacíos y aviso <5.
- **US-12 [Must|M] Cruce con casillas múltiples (solo descriptivo)**
  - CA: múltiple×categórica como indicadores binarios por opción, % sobre respondientes de cada grupo; sin test estadístico, con nota que lo explica (S5).
- **US-13 [Must|M] Filtro por segmento aplicado a todo el informe**
  - CA: un valor de una categórica filtra TODO (tablas, gráficos y cruces); n filtrado siempre visible; "sin filtro" por defecto.

## Incremento 4 — Should: lectura y exportación
> Puerta de salida del PDF: el spike decide antes del 6/10.

- **US-14 [Should|S] Lectura .xlsx** (dep nueva: `openpyxl`)
  - CA: mismo informe desde un Excel con igual estructura; error legible si falta la hoja o el formato.
- **US-09 [Should|M] Descargar informe HTML autónomo**
  - CA: un botón genera HTML con título, fecha, n total, tablas+gráficos y cruces configurados; abre offline idéntico a pantalla; solo pandas/Plotly.
- **US-15 [Should|S] Descarga CSV de tablas**
  - CA: cada tabla visible se descarga en CSV con n y %; nombres de archivo por pregunta.
- **US-16 [Should|S] Spike PDF + decisión go/no-go** (dep condicional: `fpdf2`)
  - CA: veredicto documentado antes del 6/10; si no es viable en Cloud con una sola dependencia pura, PDF se descarta y el HTML se imprime a PDF desde el navegador.

## Incremento 5 — Should: chi-cuadrado
- **US-17 [Should|M] Chi² en cruces cat×cat de respuesta única** (dep nueva: `scipy`)
  - CA: muestra estadístico, gl y p-valor + tabla de frecuencias esperadas; interpretación en lenguaje llano; aviso de muestra pequeña; se bloquea con aviso si <80% de esperadas ≥5 o alguna <1 (S7); nunca se aplica a múltiples.

## Incremento 6 — Could (solo con margen antes del 6/10)
- **US-18 [Could|S] Frecuencia de palabras en texto abierto** (sin deps nuevas)
  - CA: top-N palabras con stopwords en español; gráfico de barras; excluye vacíos.
- **US-19 [Could|M] Resumen con LLM** (dep condicional: `openai`; clave solo en `st.secrets`)
  - CA: redacta SOLO a partir de números ya calculados (nunca calcula); botón desactivado sin clave; si falla la API, la app sigue funcionando (S8).

## Dependencias nuevas (confirmar una a una antes de añadir)
| Dep | Para | Historia | Estado |
|---|---|---|---|
| `openpyxl` | leer .xlsx con pandas | US-14 | pendiente de confirmación |
| `scipy` | chi² + frecuencias esperadas | US-17 | pendiente de confirmación |
| `fpdf2` | PDF (solo si el spike sale bien) | US-16 | condicional |
| `openai` | resumen LLM (solo Could) | US-19 | condicional |

## Riesgos (revisar antes del 6/10)
1. **PDF en Cloud**: si el spike falla, se descarta sin drama (plan B: imprimir el HTML).
2. **Python de Cloud vs versiones fijadas** (local 3.14; Cloud suele ir en 3.11–3.12): re-verificar el deploy tras añadir `scipy`/`openpyxl`; posible `runtime.txt`.
3. **Chi² con n=8**: casi nunca será válido → tests con fixture sintética de n≈200, no con el ejemplo.
4. **Congelación 6/10**: el Inc 6 cae primero; después, chi² y PDF; los Must no se tocan.
5. **LLM**: clave, coste y demo sin internet → botón opcional y degradado elegante.

Orden de implementación: Inc 1 ✅ → Inc 2 (US-03→US-04→US-05→US-06→US-11) → Inc 3 (US-07→US-08→US-12→US-13) → Inc 4 (US-14→US-09→US-15→US-16) → Inc 5 (US-17) → Inc 6 (US-18→US-19).
