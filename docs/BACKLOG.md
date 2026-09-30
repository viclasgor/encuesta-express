# BACKLOG — EncuestaExpress

Priorización: Must = sin esto no hay MVP; Should = valor comprometido si da tiempo; Could = solo si sobra. Estimación S <2h, M medio día, L >1 día (con poco tiempo diario).

## Incremento 1 — E2E mínimo (desplegable en local)
> Subir CSV → ver una tabla y un gráfico. Todo lo demás es mejora.

- **US-01 [Must|S] Cargar CSV Forms y ver muestra**
  - CA: acepta UTF-8/coma del ejemplo (8 filas); muestra n total=8 + preview 5 filas; vacíos no rompen; error legible si otro separador/encoding.
- **US-02 [Must|M] Tabla + gráfico de 1 categórica única**
  - CA: para `Rango de edad` muestra tabla n y % (suma 100% sobre n válido), n válido/total, barras horizontales; coincide con cálculo pandas.

## Incremento 2 — Todos los tipos + perfil (app útil)
- **US-03 [Must|M] Autodetección + corrección manual + privacidad**
  - CA: detecta timestamp→ignorar, escala 1-5, única, múltiple (con ", "), texto, email→sugerir ignorar; dropdown por columna para corregir/ignorar; rangos "10-20 €" quedan como categoría.
- **US-04 [Must|M] Multirrespuesta correcta**
  - CA: `¿Qué factores...?` hace split por ", ", cuenta menciones, % sobre respondientes (puede >100%), barras horizontales; se indica base.
- **US-05 [Must|S] Escala 1-5**
  - CA: `Valora 1-5...` muestra media, mediana, DT, n válido/total + distribución en barras verticales.
- **US-06 [Must|S] Texto abierto + perfil muestra**
  - CA: `¿Qué mejorarías?` lista paginada sin gráfico; vacíos excluidos; cabecera global con n total y n válido por pregunta.

## Incremento 3 — Cruce (Should)
- **US-07 [Should|M] Cruce cat×cat**
  - CA: dos selects solo con categóricas/escala; tabla n y % con totales, toggle %fila(defecto)/columna; barras apiladas 100%(defecto)/agrupadas; excluye múltiples/texto; informa nº excluidos por vacíos; aviso si grupo <5.
- **US-08 [Should|S] Cruce escala×cat**
  - CA: ej. satisfacción media por edad: tabla media+DT+n por grupo y barras de medias; mismo manejo de vacíos y aviso <5.

## Incremento 4 — Exportar y cerrar demo (Should/Could)
- **US-09 [Should|M] Descargar informe HTML autónomo**
  - CA: un botón genera HTML con título, fecha, n total, todas las tablas+gráficos visibles y cruces configurados; abre offline idéntico a pantalla; solo pandas/Plotly, sin deps nuevas.
- **US-10 [Could|S] Pulido demo local**
  - CA: `data/ejemplo_encuesta.csv` incluido (8 filas café); README con `pip install -r requirements.txt` + `streamlit run app.py`; opcional descarga tablas en CSV; sin secretos/datos reales.

Orden de implementación: US-01 → US-02 → US-03 → US-04 → US-05 → US-06 → US-07 → US-08 → US-09 → US-10.
