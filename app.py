"""EncuestaExpress - informe automatico de encuestas Google Forms (calculos en src/)."""
from datetime import date
import streamlit as st
import pandas as pd
from src.analysis import (
    cargar_csv, cargar_excel, detectar_tipos, sugerir_ignorar, resumen_escala,
    distribucion_escala, listar_texto, perfil_muestra,
    tabla_frecuencias, tabla_multiple, cruce_cat_cat, cruce_escala_cat,
    cruce_multiple_cat, aplicar_filtro,
)
from src.plots import barras_horizontales, barras_verticales, barras_cruce, barras_medias
from src.export_html import generar_informe_html, tabla_a_csv
from src.export_pdf import generar_pdf
from src.chi2 import chi_cuadrado_cat

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

archivo = st.file_uploader("CSV o Excel de Google Forms", type=["csv", "xlsx"])
usar_ejemplo = st.checkbox("Usar CSV de ejemplo", value=archivo is None)

try:
    if archivo is not None:
        if archivo.name.lower().endswith(".xlsx"):
            df = cargar_excel(archivo)
        elif archivo.name.lower().endswith(".csv"):
            df = cargar_csv(archivo)
        else:
            st.error("Formato no soportado: usa .csv o .xlsx (el .xls antiguo no vale).")
            st.stop()
    elif usar_ejemplo:
        df = cargar_csv("data/ejemplo_encuesta.csv")
    else:
        st.stop()
except Exception as e:
    st.error(f"No pude leer el archivo. Revisa que sea .csv (UTF-8, comas) o .xlsx "
             f"con la primera fila de preguntas. Detalle: {e}")
    st.stop()

# US-03: revision manual de tipos detectados + ignorar columnas.
tipos_auto = detectar_tipos(df)

# US-13: filtro por segmento (un valor de una categórica filtra TODO, S6).
st.subheader("Filtro por segmento")
cat_filtro = [c for c in df.columns if tipos_auto[c] == "categorica"]
f_col_f, f_val_f = None, "Todos"
if cat_filtro:
    f_col_f = st.selectbox("Columna de segmento", ["(sin filtro)"] + cat_filtro,
                           key="filtro_col")
    if f_col_f != "(sin filtro)":
        f_val_f = st.selectbox("Valor", ["Todos"] + sorted(
            {v.strip() for v in df[f_col_f].astype(str) if v.strip() != ""}),
            key="filtro_val")
n_antes = len(df)
df = aplicar_filtro(df, f_col_f if f_col_f != "(sin filtro)" else None, f_val_f)
if len(df) < n_antes:
    st.info(f"Segmento {f_col_f} = {f_val_f}: {len(df)} de {n_antes} respuestas.")
if len(df) == 0:
    st.warning("El filtro no deja respuestas. Elige otro valor.")
    st.stop()

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
    import re
    st.subheader(col)
    slug = re.sub(r"[^a-z0-9]+", "_", col.lower()).strip("_")[:40] or "pregunta"

    def boton_csv(tabla, sufijo: str) -> None:
        st.download_button("Descargar CSV", tabla_a_csv(tabla), f"{slug}_{sufijo}.csv",
                           "text/csv", key=f"csv_{slug}_{sufijo}")
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
        boton_csv(pd.DataFrame({"respuesta": respuestas}), "texto")
    elif tipo == "escala":
        r = resumen_escala(df[col])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Media", r["media"])
        c2.metric("Mediana", r["mediana"])
        c3.metric("DT", r["dt"])
        c4.metric("n válido / total", f"{r['n_valido']} / {r['n_total']}")
        dist = distribucion_escala(df[col])
        st.dataframe(dist)
        boton_csv(dist, "escala")
        st.plotly_chart(barras_verticales(dist), use_container_width=True)
    elif tipo == "multiple":
        tabla = tabla_multiple(df[col])
        st.write(
            f"n respondientes: {tabla.attrs['n_respondientes']} · "
            f"n total: {tabla.attrs['n_total']} · % sobre respondientes"
        )
        st.dataframe(tabla)
        boton_csv(tabla, "multiple")
        st.plotly_chart(
            barras_horizontales(tabla.rename(columns={"opcion": "categoria", "menciones": "n"})),
            use_container_width=True,
        )
    else:  # categorica (y cualquier otro caso, lo mas simple)
        tabla = tabla_frecuencias(df[col])
        st.write(f"n válido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
        st.dataframe(tabla)
        boton_csv(tabla, "frecuencias")
        st.plotly_chart(barras_horizontales(tabla), use_container_width=True)


tab_informe, tab_cruces, tab_datos = st.tabs(["Informe", "Cruces", "Datos"])

with tab_informe:
    for col in analizables:
        mostrar_pregunta(col, tipos_final[col])

    # US-09: exportar el informe visible (con filtro y tipos corregidos).
    def bloque_pregunta(col: str, tipo: str) -> dict:
        if tipo == "texto":
            resp = listar_texto(df[col])
            return {"pregunta": col, "tipo": tipo,
                    "resumen": f"{len(resp)} respuestas de {len(df)}",
                    "tabla_html": pd.DataFrame({"respuesta": resp}).to_html(index=False),
                    "fig": None}
        if tipo == "escala":
            r = resumen_escala(df[col])
            dist = distribucion_escala(df[col])
            return {"pregunta": col, "tipo": tipo,
                    "resumen": (f"media {r['media']}, mediana {r['mediana']}, "
                                f"DT {r['dt']}, n {r['n_valido']}/{r['n_total']}"),
                    "tabla_html": dist.to_html(index=False),
                    "fig": barras_verticales(dist)}
        if tipo == "multiple":
            t = tabla_multiple(df[col])
            return {"pregunta": col, "tipo": tipo,
                    "resumen": (f"{t.attrs['n_respondientes']} respondientes, "
                                "% sobre respondientes"),
                    "tabla_html": t.to_html(index=False),
                    "fig": barras_horizontales(
                        t.rename(columns={"opcion": "categoria", "menciones": "n"}))}
        t = tabla_frecuencias(df[col])
        return {"pregunta": col, "tipo": tipo,
                "resumen": f"n válido {t.attrs['n_valido']}/{t.attrs['n_total']}",
                "tabla_html": t.to_html(index=False),
                "fig": barras_horizontales(t)}

    def bloque_cruce() -> dict | None:
        f_col = st.session_state.get("cruce_filas")
        c_col = st.session_state.get("cruce_cols")
        if not f_col or not c_col or f_col == c_col:
            return None
        if f_col not in df.columns or c_col not in df.columns:
            return None
        tf, tc = tipos_final.get(f_col), tipos_final.get(c_col)
        if tf == "categorica" and tc == "categorica":
            r = cruce_cat_cat(df[f_col], df[c_col])
            return {"titulo": f"Cruce: {f_col} × {c_col}",
                    "tablas_html": [r["n"].to_html(), r["pct"].to_html()],
                    "fig": barras_cruce(r["pct"], "apiladas")}
        if {tf, tc} == {"escala", "categorica"}:
            col_esc = f_col if tf == "escala" else c_col
            col_cat = c_col if tf == "escala" else f_col
            r = cruce_escala_cat(df[col_esc], df[col_cat])
            return {"titulo": f"Cruce: {col_esc} × {col_cat}",
                    "tablas_html": [r["tabla"].to_html(index=False)],
                    "fig": barras_medias(r["tabla"])}
        return None

    html_doc = generar_informe_html(
        "Informe EncuestaExpress", str(date.today()), len(df),
        [bloque_pregunta(c, tipos_final[c]) for c in analizables], bloque_cruce())
    st.download_button("Descargar informe HTML", html_doc,
                       "informe_encuestaexpress.html", "text/html")

    # US-16 (spike): PDF mínimo, solo portada + tablas, sin gráficos.
    def bloque_pdf(col: str, tipo: str) -> dict:
        if tipo == "texto":
            resp = listar_texto(df[col])
            return {"pregunta": col, "resumen": f"{len(resp)} respuestas",
                    "tabla": pd.DataFrame({"respuesta": resp})}
        if tipo == "escala":
            r = resumen_escala(df[col])
            return {"pregunta": col,
                    "resumen": (f"media {r['media']}, mediana {r['mediana']}, "
                                f"DT {r['dt']}, n {r['n_valido']}/{r['n_total']}"),
                    "tabla": distribucion_escala(df[col])}
        if tipo == "multiple":
            return {"pregunta": col, "resumen": "% sobre respondientes",
                    "tabla": tabla_multiple(df[col])}
        t = tabla_frecuencias(df[col])
        return {"pregunta": col,
                "resumen": f"n válido {t.attrs['n_valido']}/{t.attrs['n_total']}",
                "tabla": t}

    pdf_doc = generar_pdf("Informe EncuestaExpress", str(date.today()), len(df),
                          [bloque_pdf(c, tipos_final[c]) for c in analizables])
    st.download_button("Descargar PDF (beta, sin gráficos)", pdf_doc,
                       "informe_encuestaexpress.pdf", "application/pdf")

with tab_cruces:
    cruzables = [c for c in analizables
                 if tipos_final[c] in ("categorica", "escala", "multiple")]
    if len(cruzables) < 2:
        st.info("Necesitas al menos 2 preguntas cruzables (categóricas, escala o múltiples).")
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
            st.download_button("Descargar CSV (n)", tabla_a_csv(r["n"].reset_index()),
                               "cruce_n.csv", "text/csv", key="csv_cruce_n")
            st.dataframe(r["pct"])
            st.download_button("Descargar CSV (%)", tabla_a_csv(r["pct"].reset_index()),
                               "cruce_pct.csv", "text/csv", key="csv_cruce_pct")
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
            # US-17: chi-cuadrado solo aquí (nunca en múltiples/escala/texto).
            with st.expander("Test chi-cuadrado (¿hay asociación?)"):
                sin_tot = r["n"].drop(index="Total").drop(columns="Total")
                t = chi_cuadrado_cat(sin_tot)
                if not t["aplicable"]:
                    st.warning(f"Sin veredicto: {t['motivo']}")
                    if "chi2" in t:
                        st.write(f"chi²={t['chi2']} · gl={t['gl']} · p={t['p']} (orientativo)")
                else:
                    st.write(f"n={t['n']} · chi²={t['chi2']} · gl={t['gl']} · "
                             f"p={t['p']} · V de Cramér={t['v_cramer']} · α={t['alfa']}")
                    st.success(t["veredicto"])
                    with st.expander("Frecuencias esperadas"):
                        st.dataframe(t["esperadas"])
        elif ((tipos_final[f_col], tipos_final[c_col]).count("escala") == 1
                and (tipos_final[f_col], tipos_final[c_col]).count("categorica") == 1):
            col_esc = f_col if tipos_final[f_col] == "escala" else c_col
            col_cat = c_col if tipos_final[f_col] == "escala" else f_col
            r = cruce_escala_cat(df[col_esc], df[col_cat])
            if r["excluidos"]:
                st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
            st.dataframe(r["tabla"])
            st.download_button("Descargar CSV", tabla_a_csv(r["tabla"]),
                               "cruce_medias.csv", "text/csv", key="csv_cruce_medias")
            if (r["tabla"]["n"] < 5).any():
                st.warning("Algún grupo tiene menos de 5 respuestas: interpreta con cautela.")
            st.plotly_chart(barras_medias(r["tabla"]), use_container_width=True)
        elif ((tipos_final[f_col], tipos_final[c_col]).count("multiple") == 1
                and (tipos_final[f_col], tipos_final[c_col]).count("categorica") == 1):
            col_mul = f_col if tipos_final[f_col] == "multiple" else c_col
            col_cat = c_col if tipos_final[f_col] == "multiple" else f_col
            r = cruce_multiple_cat(df[col_mul], df[col_cat])
            st.caption("% sobre respondientes de cada grupo. Solo descriptivo, sin test (S5).")
            if r["excluidos"]:
                st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
            st.dataframe(r["tabla"])
            st.download_button("Descargar CSV", tabla_a_csv(r["tabla"]),
                               "cruce_multiple.csv", "text/csv", key="csv_cruce_mul")
            ancho = r["tabla"].pivot(index="grupo", columns="opcion", values="pct")
            st.plotly_chart(barras_cruce(ancho, "agrupadas", ylabel="% resp."),
                            use_container_width=True)
        else:
            st.info("Elige dos categóricas, una escala con una categórica, o una múltiple con una categórica.")

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
