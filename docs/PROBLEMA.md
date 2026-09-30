# PROBLEMA — EncuestaExpress

## Problema
Quien hace una encuesta pequeña en Google Forms (estudiante, profe, autónomo, ONG) obtiene un CSV crudo y tarda horas en limpiarlo en Excel/Sheets para sacar 3 tablas y 2 gráficos presentables. Sin conocimientos de análisis, mezcla porcentajes, rompe los multirrespuesta y no documenta cuántos no respondieron.

## Usuario objetivo
Graduado/docente/pequeño negocio que lanza encuestas de 20–200 respuestas (ej. satisfacción cafeterías) y necesita un informe descriptivo en 10 minutos, sin programar ni pagar SPSS/Typeform de pago.

## Situación actual (cómo lo hacen hoy)
1. Exportan CSV de Forms → lo abren en Sheets/Excel.
2. Hacen `CONTAR.SI` por pregunta, sufren con celdas múltiples tipo `"Precio, Ubicación"` y con vacíos.
3. Copian-pegan gráficos de Sheets a Word/Canva. Los % de multirrespuesta suelen estar mal (dividen por menciones, no por respondientes) y no indican n válido/total.
4. Si quieren cruzar (ej. satisfacción media por edad) no saben hacerlo.

## Propuesta de valor
Subes el CSV y obtienes en local, sin enviar datos a ningún LLM: perfil de muestra (n total/válido), tabla + gráfico por pregunta según su tipo, 1 cruce dirigido y descarga de informe HTML autónomo que abre offline. Cálculos deterministas con pandas; el usuario corrige el tipo detectado y excluye emails por privacidad.
