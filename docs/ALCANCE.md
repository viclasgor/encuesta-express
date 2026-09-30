# ALCANCE — EncuestaExpress MVP

> Fuente: respuestas usuario 30/09/2026. Si un criterio contradice BACKLOG, manda este archivo.

## DENTRO del MVP
1. **Carga CSV estándar Google Forms:** UTF-8, separador coma, primera fila = preguntas. Muestra n total y vista previa. Vacíos = "sin respuesta", no rompen nada.
2. **Detección automática de tipos + corrección manual:** marca temporal (se ignora), escala numérica 1-5, categórica única (incluye rangos tipo "10-20 €" como categoría), casillas múltiples (split por `", "`), texto abierto, email (ofrecer ignorar por privacidad). Usuario puede cambiar tipo por columna e ignorar columnas.
3. **Descriptivo por pregunta:**
   - Única: tabla n y % + barras horizontales.
   - Múltiple: menciones por opción, % sobre nº respondientes (puede sumar >100%) + barras horizontales.
   - Escala 1-5: media, mediana, DT y distribución + barras verticales.
   - Texto: listado paginado sin gráfico.
   - En todas: n válido y n total; vacíos fuera de %.
4. **Cruce dirigido (1 a la vez):** dos desplegables (filas/columnas), solo categórica×categórica y escala×categórica. Excluye múltiples y texto.
   - Cat×Cat: tabla n y % con totales, selector % fila (defecto) / columna, barras apiladas 100% (defecto) / agrupadas.
   - Escala×Cat: tabla media + DT + n por grupo, barras de medias. Aviso si grupo <5. Informa excluidos por vacíos.
5. **Exportación HTML (Should, tras tablas/gráficos):** un botón descarga un HTML autónomo con título, fecha, n total, cada tabla+gráfico y cruces configurados. Hecho con pandas/Plotly, sin dependencias nuevas. Debe abrir offline idéntico a pantalla.
6. **Despliegue en Streamlit Community Cloud (DENTRO, criterio de hecho) + local como plan B:** app desplegada en Cloud con `requirements.txt` versionado; `README.md` enlaza la URL pública. En local (`pip install + streamlit run`) queda como plan B para la demo. CSV ejemplo en `data/ejemplo_encuesta.csv` (encuesta café, 8 filas). Entrega 9/10, demo 5 min 13/10. (Cambio 30/09: Cloud pasa de FUERA/opción a DENTRO; local pasa a plan B.)

## FUERA del MVP (explícitamente)
- Otros formatos: Excel, Typeform, SurveyMonkey, matrices de preguntas.
- Convertir rangos a números; ponderación; filtros por segmentos.
- Gráficos circulares, nubes de palabras, análisis sentimiento, tests estadísticos (chi², p-valor).
- Cruces de >2 variables, cruces con múltiples/texto.
- Exportación PDF/Word/PowerPoint (el usuario imprime el HTML a PDF); descarga CSV de tablas es solo Could.
- Login, base de datos, LLM para cálculos.

## Criterios de "hecho" medibles
- [ ] CSV ejemplo (8 filas café) carga sin error, muestra n=8 y preview de 7 columnas.
- [ ] Cada tipo detectado es correcto o corregible en <2 clics; email/timestamp ignorables.
- [ ] Única: % suman 100% sobre n válido; múltiple: % sobre respondientes; escala: media/mediana/DT coinciden con pandas; texto: no genera gráfico.
- [ ] Cruce cat×cat cambia fila/columna correctamente; escala×cat muestra n por grupo y aviso <5.
- [ ] HTML exportado abre sin internet y contiene mismas tablas/gráficos que pantalla.
- [ ] Despliegue Cloud: app pública en Streamlit Community Cloud abre el ejemplo (n=8) y acepta un CSV Forms; URL enlazada en `README.md`.
- [ ] Plan B local: `pip install -r requirements.txt && streamlit run app.py` funciona siguiendo README; sin secretos ni datos reales.

## Supuestos (decisiones simples que no cambian alcance/stack)
- S1: Separador múltiple exactamente `", "`; si no hay coma, se trata como única.
- S2: Escala = columna 100% numérica 1-5; si hay texto, cae a categórica.
- S3: Email = nombre columna contiene "mail/correo/e-mail"; solo sugerencia de ignorar.
- S4: HTML usa figuras Plotly embebidas (sin CDN obligatorio para offline).
