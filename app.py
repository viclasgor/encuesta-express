"""EncuestaExpress - Incremento 2 (en curso): UI + informe por tipos (calculos en src/)."""
import streamlit as st
import pandas as pd
from src.analysis import (
    cargar_csv, detectar_tipos, sugerir_ignorar, resumen_escala,
    distribucion_escala, listar_texto, perfil_muestra,
    tabla_frecuencias, tabla_multiple,
)
from src.plots import barras_horizontales, barras_verticales

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

# US-06: perfil de la muestra (n válido por pregunta).
perfil = perfil_muestra(df)
with st.expander("Perfil de la muestra"):
    st.write(f"Respuestas totales: **{perfil['n_total']}**")
    st.dataframe(
        pd.DataFrame(
            {"pregunta": list(perfil["n_valido_por_columna"].keys()),
             "n_válido": list(perfil["n_valido_por_columna"].values())}
        )
    )

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

# Pregunta a analizar (la vista depende del tipo corregido: US-02/US-04/...).
candidatas = [c for c in analizables if "edad" in c.lower()] or analizables
col = st.selectbox("Pregunta a analizar", candidatas)
if tipos_final[col] == "texto":
    respuestas = listar_texto(df[col])
    st.write(f"{len(respuestas)} respuestas (de {len(df)} totales, resto vacías). Sin gráfico.")
    por_pag, n_pag = 10, 1
    if len(respuestas) > por_pag:
        n_pag = st.number_input("Página", min_value=1,
                                max_value=(len(respuestas) - 1) // por_pag + 1, value=1)
    for r in respuestas[(n_pag - 1) * por_pag:n_pag * por_pag]:
        st.markdown(f"- {r}")
elif tipos_final[col] == "escala":
    r = resumen_escala(df[col])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Media", r["media"])
    c2.metric("Mediana", r["mediana"])
    c3.metric("DT", r["dt"])
    c4.metric("n válido / total", f"{r['n_valido']} / {r['n_total']}")
    dist = distribucion_escala(df[col])
    st.dataframe(dist)
    st.plotly_chart(barras_verticales(dist), use_container_width=True)
elif tipos_final[col] == "multiple":
    tabla = tabla_multiple(df[col])
    st.write(
        f"n respondientes: {tabla.attrs['n_respondientes']} · "
        f"n total: {tabla.attrs['n_total']} · % sobre respondientes"
    )
    st.dataframe(tabla)
    st.plotly_chart(
        barras_horizontales(
            tabla.rename(columns={"opcion": "categoria", "menciones": "n"})
        ),
        use_container_width=True,
    )
else:
    tabla = tabla_frecuencias(df[col])
    st.write(f"n valido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
    st.dataframe(tabla)
    st.plotly_chart(barras_horizontales(tabla), use_container_width=True)
