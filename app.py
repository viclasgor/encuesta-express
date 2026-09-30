"""EncuestaExpress - Incremento 1: US-01 + US-02 (solo UI, calculos en src/)."""
import streamlit as st
import pandas as pd
from src.analysis import cargar_csv, tabla_frecuencias
from src.plots import barras_horizontales

st.title("EncuestaExpress")
st.caption("Sube tu CSV de Google Forms (UTF-8, coma) y ve una tabla + grafico.")

archivo = st.file_uploader("CSV de Google Forms", type=["csv"])
usar_ejemplo = st.checkbox("Usar CSV de ejemplo", value=archivo is None)

try:
    if archivo is not None:
        df = cargar_csv(archivo)
    elif usar_ejemplo:
        df = cargar_csv("data/ejemplo_encuesta.csv")
    else:
        st.stop()
except Exception as e:
    st.error(f"No pude leer el CSV. Revisa que sea UTF-8 con comas. Detalle: {e}")
    st.stop()

st.success(f"n total: {len(df)} · columnas: {len(df.columns)}")
st.dataframe(df.head(5))

# US-02: una categorica unica (por defecto Rango de edad si existe)
candidatas = [c for c in df.columns if "edad" in c.lower()] or list(df.columns)
col = st.selectbox("Pregunta a analizar", candidatas)
tabla = tabla_frecuencias(df[col])
st.write(f"n valido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
st.dataframe(tabla)
st.plotly_chart(barras_horizontales(tabla), use_container_width=True)
