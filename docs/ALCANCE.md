# ALCANCE — EncuestaExpress MVP (ampliado 30/09/2026)

> Fuente: respuestas usuario 30/09/2026 + ampliación aprobada 30/09/2026. Si un criterio contradice BACKLOG, manda este archivo.
> Fechas: entrega 9/10 · congelación de funcionalidades 6/10 · demo 5 min 13/10.

## DENTRO del MVP
1. **Carga CSV estándar Google Forms (+ .xlsx como Should):** UTF-8, separador coma, primera fila = preguntas. Muestra n total y vista previa. Vacíos = "sin respuesta", no rompen nada.
2. **Detección automática de tipos + corrección manual:** marca temporal (se ignora), escala numérica 1-5, categórica única (incluye rangos tipo "10-20 €" como categoría), casillas múltiples (split por `", "`), texto abierto, email (ofrecer ignorar por privacidad). Usuario puede cambiar tipo por columna e ignorar columnas.
3. **Informe automático con todas las preguntas:**
   - Única: tabla n y % + barras horizontales.
   - Múltiple: menciones por opción, % sobre nº respondientes (puede sumar >100%) + barras horizontales.
   - Escala 1-5: media, mediana, DT y distribución + barras verticales.
   - Texto: listado paginado sin gráfico.
   - En todas: n válido y n total; vacíos fuera de %.
4. **Interfaz cuidada (Must):** layout ancho, pestañas Informe / Cruces / Datos, tarjetas de métricas (n total, n válido), ayuda sobre el formato CSV esperado.
5. **Cruces de dos variables, incluyendo múltiples:**
   - Cat×Cat (respuesta única): tabla n y % con totales, selector % fila (defecto) / columna, barras apiladas 100% (defecto) / agrupadas.
   - Escala×Cat: tabla media + DT + n por grupo, barras de medias.
   - Múltiple×Categórica: solo descriptiva (indicadores por opción, % sobre respondientes del grupo), sin test.
   - Aviso si grupo <5. Informa excluidos por vacíos.
6. **Filtro por segmento (Should):** un valor de una categórica filtra TODO el informe; n filtrado siempre visible.
7. **Exportación HTML autónoma (Should):** un botón descarga un HTML con título, fecha, n total, cada tabla+gráfico y cruces configurados. Hecho con pandas/Plotly. Debe abrir offline idéntico a pantalla. Descarga CSV de tablas incluida.
8. **PDF (Should condicional):** solo si el spike previo al 6/10 demuestra que es viable en Cloud con una sola dependencia pura; si no, se descarta (plan B: imprimir el HTML).
9. **Chi-cuadrado (Should):** solo en cat×cat de respuesta única, con estadístico, gl, p-valor, tabla de esperadas, interpretación en lenguaje llano, aviso de muestra pequeña y comprobación de condiciones (S7). Nunca en múltiples.
10. **Could (solo con margen antes del 6/10):** frecuencia de palabras en texto abierto; resumen con LLM solo a partir de números ya calculados (nunca calcula; clave solo en `st.secrets`).
11. **Despliegue en Streamlit Community Cloud (DENTRO, criterio de hecho) + local como plan B:** app desplegada en Cloud con `requirements.txt` versionado; `README.md` enlaza la URL pública. CSV ejemplo en `data/ejemplo_encuesta.csv` (encuesta café, 8 filas).

## FUERA del MVP (explícitamente)
- Gráficos circulares / quesitos (pendiente de decisión; por defecto fuera).
- Nubes de palabras, análisis de sentimiento, ponderación.
- Test de Fisher y otros tests; chi² en múltiples o en más de 2 variables.
- Convertir rangos a números; matrices de preguntas; otros formatos de encuesta (Typeform, SurveyMonkey).
- Exportación Word/PowerPoint.
- Login, base de datos, LLM para calcular.
- PDF si el spike previo al 6/10 falla.

## Criterios de "hecho" medibles
- [ ] CSV ejemplo (8 filas café) carga sin error, muestra n=8 y preview de 7 columnas; .xlsx equivalente también abre.
- [ ] Cada tipo detectado es correcto o corregible en <2 clics; email/timestamp ignorables.
- [ ] Única: % suman 100% sobre n válido; múltiple: % sobre respondientes; escala: media/mediana/DT coinciden con pandas; texto: no genera gráfico.
- [ ] Informe muestra las 7 preguntas con pestañas y tarjetas; ayuda de formato CSV visible.
- [ ] Cruces: cat×cat y escala×cat correctos con aviso <5; múltiple×cat descriptivo sin test; filtro global aplicado y visible.
- [ ] HTML exportado abre sin internet idéntico a pantalla; tablas descargables en CSV.
- [ ] Chi²: con datos suficientes muestra p-valor e interpretación; con n=8 avisa de que no aplica.
- [ ] Despliegue Cloud: app pública abre el ejemplo (n=8) y acepta un CSV Forms; URL enlazada en `README.md`.
- [ ] Plan B local: `pip install -r requirements.txt && streamlit run app.py` funciona; `pytest -q` en verde; sin secretos ni datos reales.

## Supuestos (decisiones simples que no cambian alcance/stack)
- S1: Separador múltiple exactamente `", "`; si no hay coma, se trata como única.
- S2: Escala = columna 100% numérica 1-5; si hay texto, cae a categórica.
- S3: Email = nombre columna contiene "mail/correo/e-mail"; solo sugerencia de ignorar.
- S4: HTML usa figuras Plotly embebidas (sin CDN obligatorio para offline).
- S5: Múltiple en cruces = % sobre respondientes de cada grupo, sin test estadístico.
- S6: Filtro = un solo valor de una categórica, aplicado a todo el informe.
- S7: Chi² solo si ≥80% de frecuencias esperadas ≥5 y ninguna <1; si no, aviso y bloqueo.
- S8: El LLM solo redacta con números calculados; clave solo en `st.secrets`, nunca en el repo.
- S9: La corrección manual de tipos vive en `session_state` y se reinicia al cambiar de archivo.
- S10: El listado de texto abierto se pagina de 10 en 10.
- S11: Pestañas Informe / Cruces / Datos; la de Cruces se rellena en el Incremento 3.
- S12: El .xlsx lee solo la primera hoja y normaliza todo a texto como el CSV.
- S13: El HTML embebe Plotly inline (pesa más, pero abre sin internet).
- S14: Las descargas CSV usan coma como separador, igual que el CSV de entrada.
- S15: El PDF es mínimo (portada + tablas, sin gráficos) con fuente DejaVu vendored.
- S16: En tablas 2×2 se deja la corrección de Yates que scipy aplica por defecto.
