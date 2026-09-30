"""EncuestaExpress - informe automatico de encuestas Google Forms (calculos en src/)."""
import streamlit as st
import pandas as pd
from src.analysis import (
    cargar_csv, detectar_tipos, sugerir_ignorar, resumen_escala,
    distribucion_escala, listar_texto, perfil_muestra,
    tabla_frecuencias, tabla_multiple, cruce_cat_cat,
)
from src.plots import barras_horizontales, barras_verticales, barras_cruce

TIPOS = ["categorica", "multiple", "escala", "texto", "temporal", "email", "ignorar"]

st.set_page_config(page_title="EncuestaExpress", layout="wide")
st.title("EncuestaExpress")
st.caption("Sube tu CSV de Google Forms y obtén un informe automático.")

with st.expander("Ayuda: ¿qué CSV necesito?"):
    st.markdown(
        "- Exportado de **Google Forms**: primera fila = preguntas, resto = respuestas.\n"
        "- Codificación **UTF-8** y separador **coma**.\n"
        "- Las casillas múltiples llegan como `Opción A, Opción B` en una celda.\n"
        "- Los vacíos se cuentan como sin respuesta y no rompen nada.\n"
        "- Si hay columna de email, se sugiere ignorarla por privacidad."
    )

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
perfil = perfil_muestra(df)

# Tarjetas de métricas.
m1, m2, m3 = st.columns(3)
m1.metric("Respuestas totales", perfil["n_total"])
m2.metric("Preguntas analizadas", len(analizables))
m3.metric("Columnas ignoradas", len(df.columns) - len(analizables))
if not analizables:
    st.warning("Has ignorado todas las columnas. Activa al menos una para ver el informe.")
    st.stop()


def mostrar_pregunta(col: str, tipo: str) -> None:
    """Una pregunta con su tabla/grafico segun tipo (US-02/04/05/06)."""
    st.subheader(col)
    if tipo == "texto":
        respuestas = listar_texto(df[col])
        st.write(f"{len(respuestas)} respuestas (de {len(df)} totales, resto vacías). Sin gráfico.")
        por_pag, n_pag = 10, 1
        if len(respuestas) > por_pag:
            n_pag = st.number_input("Página", min_value=1,
                                    max_value=(len(respuestas) - 1) // por_pag + 1,
                                    value=1, key=f"pag_{col}")
        for r in respuestas[(n_pag - 1) * por_pag:n_pag * por_pag]:
            st.markdown(f"- {r}")
    elif tipo == "escala":
        r = resumen_escala(df[col])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Media", r["media"])
        c2.metric("Mediana", r["mediana"])
        c3.metric("DT", r["dt"])
        c4.metric("n válido / total", f"{r['n_valido']} / {r['n_total']}")
        dist = distribucion_escala(df[col])
        st.dataframe(dist)
        st.plotly_chart(barras_verticales(dist), use_container_width=True)
    elif tipo == "multiple":
        tabla = tabla_multiple(df[col])
        st.write(
            f"n respondientes: {tabla.attrs['n_respondientes']} · "
            f"n total: {tabla.attrs['n_total']} · % sobre respondientes"
        )
        st.dataframe(tabla)
        st.plotly_chart(
            barras_horizontales(tabla.rename(columns={"opcion": "categoria", "menciones": "n"})),
            use_container_width=True,
        )
    else:  # categorica (y cualquier otro caso, lo mas simple)
        tabla = tabla_frecuencias(df[col])
        st.write(f"n válido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
        st.dataframe(tabla)
        st.plotly_chart(barras_horizontales(tabla), use_container_width=True)


tab_informe, tab_cruces, tab_datos = st.tabs(["Informe", "Cruces", "Datos"])

with tab_informe:
    for col in analizables:
        mostrar_pregunta(col, tipos_final[col])

with tab_cruces:
    cruzables = [c for c in analizables if tipos_final[c] in ("categorica", "escala")]
    if len(cruzables) < 2:
        st.info("Necesitas al menos 2 preguntas categóricas o de escala.")
    else:
        f_col = st.selectbox("Filas", cruzables, key="cruce_filas")
        c_col = st.selectbox("Columnas", [c for c in cruzables if c != f_col],
                             key="cruce_cols")
        if tipos_final[f_col] == "categorica" and tipos_final[c_col] == "categorica":
            base = st.radio("% sobre", ["fila", "columna"], horizontal=True)
            r = cruce_cat_cat(df[f_col], df[c_col], base=base)
            if r["excluidos"]:
                st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
            st.dataframe(r["n"])
            st.dataframe(r["pct"])
            totales_fila = r["n"].drop(index="Total", errors="ignore")["Total"]
            totales_col = r["n"].drop(columns="Total", errors="ignore").loc["Total"]
            if (totales_fila < 5).any() or (totales_col < 5).any():
                st.warning("Algún grupo tiene menos de 5 respuestas: interpreta con cautela.")
            modo = st.radio("Gráfico", ["apiladas", "agrupadas"], horizontal=True)
            if modo == "apiladas":
                st.plotly_chart(barras_cruce(r["pct"], "apiladas"),
                                use_container_width=True)
            else:
                st.plotly_chart(
                    barras_cruce(r["n"].drop(index="Total").drop(columns="Total"),
                                 "agrupadas"),
                    use_container_width=True)
        else:
            st.info("El cruce escala×categórica llega en US-08.")

with tab_datos:
    with st.expander("Perfil de la muestra"):
        st.write(f"Respuestas totales: **{perfil['n_total']}**")
        st.dataframe(
            pd.DataFrame(
                {"pregunta": list(perfil["n_valido_por_columna"].keys()),
                 "n_válido": list(perfil["n_valido_por_columna"].values())}
            )
        )
    st.dataframe(df)
