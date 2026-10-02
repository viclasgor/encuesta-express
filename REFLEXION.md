# Informe de reflexión — EncuestaExpress

## 1. De dónde salió la idea
Estudié Marketing e Investigación de Mercados, y las encuestas me daban
quebraderos de cabeza de verdad: exportar de Google Forms a Excel y pasarme
horas contando respuestas, con las de opción múltiple siempre mal calculadas.
La idea de la web fue mía: subir el CSV y que salga el informe solo. Yo además
le pasé a la IA el maquetado de cómo quería que se viera (la estética de hoja
de cálculo con la franja verde, la barra de fórmulas, las tablas con su
columna de reparto), y fue ella la que lo convirtió en la página.

## 2. Cómo trabajamos
Yo conducía con prompts que preparaba con ayuda de Claude para que salieran
bien: le pedía una cosa cada vez (primero una tabla, luego un gráfico, luego
un cruce) y no avanzábamos hasta que eso funcionaba. Mi regla era no creerme
nada sin probarlo: mientras programábamos yo iba haciendo push al repo de
GitHub y comprobando en Streamlit, y cuando algo fallaba lo analizaba, se lo
decía y lo corregíamos juntos. Así pillamos fallos que en local no salían,
como el error del PDF en la nube o los gráficos que salían azules en vez de
verdes. Al final, la prueba de que todo cuadra es `pytest -q` en verde:
27 pruebas que comprueban los cálculos.

## 3. Qué hizo cada uno
La IA escribió el código (los cálculos con pandas y scipy, los tests, la
interfaz y los informes descargables). Lo mío fue dirigir: definir qué tenía
que hacer la app, el orden (primero lo básico que funcionara, los adornos
después), la maqueta visual, y decidir cosas como que los porcentajes de las
preguntas múltiples se calculan sobre personas y no sobre respuestas, o que
el chi-cuadrado se niegue a dar veredicto con muestras pequeñas. También
fui yo quien probó cada entrega en el navegador y quien decidió qué entraba
antes de la congelación del 6/10.

## 4. Lo más importante que aprendí (y mi defensa en 5 minutos)
Lo que de verdad entendí haciendo esto: los números no los calcula ningún
modelo de IA, los calcula código normal (pandas), y por eso se pueden
comprobar con tests. En un curso donde todos enseñan una llamada a un modelo,
yo explico por qué decidí no meter el modelo donde están los números. Si el
profesor me pregunta algo técnico, mi respuesta honesta es esa: yo no programo
como un senior, pero sé pedir, probar y decidir, y el `pytest -q` en verde
lo demuestra en pantalla.
