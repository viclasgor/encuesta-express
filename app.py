"""EncuestaExpress - Incremento 2 (en curso): UI + informe por tipos (calculos en src/)."""
import streamlit as st
import pandas as pd
from src.analysis import cargar_csv, detectar_tipos, sugerir_ignorar, tabla_frecuencias
from src.plots import barras_horizontales

TIPOS = ["categorica", "multiple", "escala", "texto", "temporal", "email", "ignorar"]

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

# US-03: revision manual de tipos detectados + ignorar columnas.
tipos_auto = detectar_tipos(df)
with st.expander("Revisar tipos detectados (puedes corregir o ignorar columnas)"):
    tipos_final = {}
    for col in df.columns:
        det = tipos_auto[col]
        if sugerir_ignorar(det):
            st.caption(f"Sugerencia: ignorar '{col}' (tipo {det}).")
        tipos_final[col] = st.selectbox(
            col, TIPOS,
            index=TIPOS.index(det) if det in TIPOS else 0,
            key=f"tipo_{col}",
        )

analizables = [c for c in df.columns if tipos_final[c] not in ("ignorar", "temporal", "email")]
if not analizables:
    st.warning("Has ignorado todas las columnas. Activa al menos una para ver el informe.")
    st.stop()

# US-02: una categorica unica (por defecto Rango de edad si existe)
candidatas = [c for c in analizables if "edad" in c.lower()] or analizables
col = st.selectbox("Pregunta a analizar", candidatas)
tabla = tabla_frecuencias(df[col])
st.write(f"n valido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
st.dataframe(tabla)
st.plotly_chart(barras_horizontales(tabla), use_container_width=True)
