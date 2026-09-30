"""EncuestaExpress - informe automatico de encuestas Google Forms (calculos en src/)."""
import io
import re
import zipfile
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

TIPOS = ["categorica", "multiple", "escala", "texto", "temporal", "email", "id", "ignorar"]

st.set_page_config(page_title="EncuestaExpress", layout="wide",
                   page_icon="📊",
                   menu_items={"About": "EncuestaExpress: del CSV de tu encuesta al informe en minutos."})
st.title("EncuestaExpress")
st.caption("Sube tu CSV o Excel de Google Forms y obtén un informe automático: tablas, gráficos, cruces y descargas.")


def slug_de(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", col.lower()).strip("_")[:40] or "pregunta"


def tabla_de(df: pd.DataFrame, col: str, tipo: str) -> pd.DataFrame | None:
    """La tabla que se muestra (y descarga) para una pregunta."""
    if tipo == "texto":
        return pd.DataFrame({"respuesta": listar_texto(df[col])})
    if tipo == "escala":
        return distribucion_escala(df[col])
    if tipo == "multiple":
        return tabla_multiple(df[col])
    return tabla_frecuencias(df[col])


def con_totales_resaltados(tabla: pd.DataFrame):
    def estilo(fila):
        color = "background-color: #E3F2F2" if fila.name == "Total" else ""
        return [color] * len(fila)
    return tabla.style.apply(estilo, axis=1)


# --- Barra lateral: carga y opciones globales ---
with st.sidebar:
    st.header("Datos y opciones")
    archivo = st.file_uploader("CSV o Excel de Google Forms", type=["csv", "xlsx"])
    if st.button("Probar con datos de ejemplo"):
        st.session_state["usar_ejemplo"] = True
        st.rerun()
    if archivo is None and st.session_state.get("usar_ejemplo"):
        st.caption("Usando datos de ejemplo.")
        if st.button("Dejar el ejemplo"):
            st.session_state["usar_ejemplo"] = False
            st.rerun()

# --- Carga o estado vacío ---
try:
    if archivo is not None:
        if archivo.name.lower().endswith(".xlsx"):
            df = cargar_excel(archivo)
        elif archivo.name.lower().endswith(".csv"):
            df = cargar_csv(archivo)
        else:
            st.error("Formato no soportado: usa .csv o .xlsx (el .xls antiguo no vale).")
            st.stop()
    elif st.session_state.get("usar_ejemplo"):
        df = cargar_csv("data/ejemplo_encuesta.csv")
    else:
        st.markdown("### Empieza en 3 pasos")
        st.markdown("1. **Sube tu CSV/Excel** desde la barra lateral (o prueba el ejemplo).\n"
                    "2. **Revisa los tipos detectados** y corrige si hace falta.\n"
                    "3. **Explora el informe**, cruza variables y descarga el resultado.")
        if st.button("Probar con datos de ejemplo", type="primary"):
            st.session_state["usar_ejemplo"] = True
            st.rerun()
        st.stop()
except Exception as e:
    st.error(f"No pude leer el archivo. Revisa que sea .csv (UTF-8, comas) o .xlsx "
             f"con la primera fila de preguntas. Detalle: {e}")
    st.stop()

tipos_auto = detectar_tipos(df)

with st.sidebar:
    # US-13: filtro por segmento (un valor filtra TODO, S6).
    st.subheader("Filtro por segmento")
    cat_filtro = [c for c in df.columns if tipos_auto[c] == "categorica"]
    f_col_f, f_val_f = None, "Todos"
    if cat_filtro:
        f_col_f = st.selectbox("Columna", ["(sin filtro)"] + cat_filtro, key="filtro_col")
        if f_col_f != "(sin filtro)":
            f_val_f = st.selectbox("Valor", ["Todos"] + sorted(
                {v.strip() for v in df[f_col_f].astype(str) if v.strip() != ""}),
                key="filtro_val", help="Filtra todo el informe por este valor.")
    # % del cruce categórico (opción global del informe).
    st.subheader("Cruce categórico")
    base_cruce = st.radio("% sobre", ["fila", "columna"], key="pct_base",
                          help="Base de los porcentajes del cruce categórica×categórica.")

    # US-03: revisión manual de tipos + ignorar columnas.
    with st.expander("Revisar tipos detectados"):
        st.caption("Corrige el tipo o ignora columnas (id, email, fecha...).")
        tipos_final = {}
        for col in df.columns:
            det = tipos_auto[col]
            if sugerir_ignorar(det):
                st.caption(f"Sugerencia: ignorar '{col}' ({det}).")
            tipos_final[col] = st.selectbox(col, TIPOS,
                                            index=TIPOS.index(det) if det in TIPOS else 0,
                                            key=f"tipo_{col}")

n_antes = len(df)
df = aplicar_filtro(df, f_col_f if f_col_f != "(sin filtro)" else None, f_val_f)
if len(df) < n_antes:
    st.info(f"Segmento {f_col_f} = {f_val_f}: {len(df)} de {n_antes} respuestas.")
if len(df) == 0:
    st.warning("El filtro no deja respuestas. Elige otro valor.")
    st.stop()

analizables = [c for c in df.columns
               if tipos_final[c] not in ("ignorar", "temporal", "email", "id")]
perfil = perfil_muestra(df)
if not analizables:
    st.warning("Has ignorado todas las columnas. Activa al menos una para ver el informe.")
    st.stop()


def mostrar_pregunta(col: str, tipo: str) -> None:
    """Una pregunta con su tabla/grafico segun tipo."""
    with st.container(border=True):
        st.subheader(col)
        slug = slug_de(col)

        def boton_csv(tabla: pd.DataFrame, sufijo: str) -> None:
            st.download_button("Descargar CSV", tabla_a_csv(tabla), f"{slug}_{sufijo}.csv",
                               "text/csv", key=f"csv_{slug}_{sufijo}")

        if tipo == "texto":
            respuestas = listar_texto(df[col])
            st.write(f"{len(respuestas)} respuestas (de {len(df)} totales, resto vacías). Sin gráfico.")
            por_pag, n_pag = 10, 1
            if len(respuestas) > por_pag:
                n_pag = st.number_input("Página", min_value=1,
                                        max_value=(len(respuestas) - 1) // por_pag + 1,
                                        value=1, key=f"pag_{slug}")
            for r in respuestas[(n_pag - 1) * por_pag:n_pag * por_pag]:
                st.markdown(f"- {r}")
            boton_csv(pd.DataFrame({"respuesta": respuestas}), "texto")
            return
        if tipo == "escala":
            r = resumen_escala(df[col])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Media", r["media"])
            c2.metric("Mediana", r["mediana"])
            c3.metric("DT", r["dt"])
            c4.metric("n válido / total", f"{r['n_valido']} / {r['n_total']}")
            dist = distribucion_escala(df[col])
            t1, t2 = st.columns([1, 1.2])
            with t1:
                st.dataframe(dist)
                boton_csv(dist, "escala")
            with t2:
                st.plotly_chart(barras_verticales(dist), width="stretch",
                                key=f"chart_{slug}_escala")
            return
        if tipo == "multiple":
            tabla = tabla_multiple(df[col])
            st.caption(f"n respondientes: {tabla.attrs['n_respondientes']} · "
                       f"n total: {tabla.attrs['n_total']} · % sobre respondientes")
            t1, t2 = st.columns([1, 1.2])
            with t1:
                st.dataframe(tabla)
                boton_csv(tabla, "multiple")
            with t2:
                st.plotly_chart(
                    barras_horizontales(
                        tabla.rename(columns={"opcion": "categoria", "menciones": "n"})),
                    width="stretch", key=f"chart_{slug}_multiple")
            return
        tabla = tabla_frecuencias(df[col])
        st.caption(f"n válido: {tabla.attrs['n_valido']} · n total: {tabla.attrs['n_total']}")
        t1, t2 = st.columns([1, 1.2])
        with t1:
            st.dataframe(tabla)
            boton_csv(tabla, "frecuencias")
        with t2:
            st.plotly_chart(barras_horizontales(tabla), width="stretch",
                            key=f"chart_{slug}_cat")


tab_resumen, tab_informe, tab_cruces, tab_exportar = st.tabs(
    ["Resumen", "Informe", "Cruces", "Exportar"])

with tab_resumen:
    vacias = sum((df[c].astype(str).str.strip() == "").sum() for c in analizables)
    completitud = 1 - vacias / (len(df) * len(analizables)) if len(df) else 1.0
    m1, m2, m3 = st.columns(3)
    m1.metric("Respuestas", len(df),
              help="Filas tras aplicar el filtro de segmento.")
    m2.metric("Preguntas analizadas", len(analizables),
              help="Columnas no ignoradas (ni id, email o fecha).")
    m3.metric("% completitud", f"{completitud:.0%}",
              help="Celdas con respuesta sobre el total de analizables.")
    if completitud < 0.8:
        st.warning(f"Completitud baja ({completitud:.0%}): hay muchas celdas vacías; "
                   "revisa si alguna pregunta se entendió mal.")
    if len(df) < 30:
        st.info("Muestra pequeña (n<30): el chi-cuadrado casi nunca será aplicable; "
                "los cruces se leen como descriptivos.")
    ignoradas = len(df.columns) - len(analizables)
    if ignoradas:
        st.info(f"{ignoradas} columna(s) ignoradas (id, email, fecha o descarte manual).")
    with st.expander("Perfil de la muestra"):
        st.dataframe(pd.DataFrame(
            {"pregunta": list(perfil["n_valido_por_columna"].keys()),
             "n_válido": list(perfil["n_valido_por_columna"].values())}))
    with st.expander("Ver datos"):
        st.dataframe(df)

with tab_informe:
    for col in analizables:
        mostrar_pregunta(col, tipos_final[col])

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
            r = cruce_cat_cat(df[f_col], df[c_col], base=base_cruce)
            if r["excluidos"]:
                st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
            st.dataframe(con_totales_resaltados(r["n"]))
            st.download_button("Descargar CSV (n)", tabla_a_csv(r["n"].reset_index()),
                               "cruce_n.csv", "text/csv", key="csv_cruce_n")
            st.dataframe(r["pct"])
            st.download_button("Descargar CSV (%)", tabla_a_csv(r["pct"].reset_index()),
                               "cruce_pct.csv", "text/csv", key="csv_cruce_pct")
            totales_fila = r["n"].drop(index="Total", errors="ignore")["Total"]
            totales_col = r["n"].drop(columns="Total", errors="ignore").loc["Total"]
            if (totales_fila < 5).any() or (totales_col < 5).any():
                st.warning("Algún grupo tiene menos de 5 respuestas: interpreta con cautela.")
            modo = st.radio("Gráfico", ["apiladas", "agrupadas"], horizontal=True,
                            help="Apiladas = % que suman 100; agrupadas = recuentos.")
            if modo == "apiladas":
                st.plotly_chart(barras_cruce(r["pct"], "apiladas"),
                                width="stretch", key="chart_cruce_apil")
            else:
                st.plotly_chart(
                    barras_cruce(r["n"].drop(index="Total").drop(columns="Total"),
                                 "agrupadas"),
                    width="stretch", key="chart_cruce_agrup")
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
            st.plotly_chart(barras_medias(r["tabla"]), width="stretch",
                            key="chart_cruce_medias")
        elif ((tipos_final[f_col], tipos_final[c_col]).count("multiple") == 1
                and (tipos_final[f_col], tipos_final[c_col]).count("categorica") == 1):
            col_mul = f_col if tipos_final[f_col] == "multiple" else c_col
            col_cat = c_col if tipos_final[f_col] == "multiple" else f_col
            r = cruce_multiple_cat(df[col_mul], df[col_cat])
            st.info("% sobre respondientes de cada grupo. Solo descriptivo, sin test (S5).")
            if r["excluidos"]:
                st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
            st.dataframe(r["tabla"])
            st.download_button("Descargar CSV", tabla_a_csv(r["tabla"]),
                               "cruce_multiple.csv", "text/csv", key="csv_cruce_mul")
            ancho = r["tabla"].pivot(index="grupo", columns="opcion", values="pct")
            st.plotly_chart(barras_cruce(ancho, "agrupadas", ylabel="% resp."),
                            width="stretch", key="chart_cruce_mul")
        else:
            st.info("Elige dos categóricas, una escala con una categórica, "
                    "o una múltiple con una categórica.")


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
    f_c = st.session_state.get("cruce_filas")
    c_c = st.session_state.get("cruce_cols")
    if not f_c or not c_c or f_c == c_c:
        return None
    if f_c not in df.columns or c_c not in df.columns:
        return None
    tf, tc = tipos_final.get(f_c), tipos_final.get(c_c)
    if tf == "categorica" and tc == "categorica":
        r = cruce_cat_cat(df[f_c], df[c_c])
        return {"titulo": f"Cruce: {f_c} × {c_c}",
                "tablas_html": [r["n"].to_html(), r["pct"].to_html()],
                "fig": barras_cruce(r["pct"], "apiladas")}
    if {tf, tc} == {"escala", "categorica"}:
        col_esc = f_c if tf == "escala" else c_c
        col_cat = c_c if tf == "escala" else f_c
        r = cruce_escala_cat(df[col_esc], df[col_cat])
        return {"titulo": f"Cruce: {col_esc} × {col_cat}",
                "tablas_html": [r["tabla"].to_html(index=False)],
                "fig": barras_medias(r["tabla"])}
    return None


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


with tab_exportar:
    st.markdown("### Descargar el informe")
    st.caption("Se exporta lo visible: filtro y tipos corregidos aplicados; "
               "el cruce si lo configuraste en su pestaña.")
    html_doc = generar_informe_html(
        "Informe EncuestaExpress", str(date.today()), len(df),
        [bloque_pregunta(c, tipos_final[c]) for c in analizables], bloque_cruce())
    st.download_button("Descargar informe HTML", html_doc,
                       "informe_encuestaexpress.html", "text/html")
    pdf_doc = generar_pdf("Informe EncuestaExpress", str(date.today()), len(df),
                          [bloque_pdf(c, tipos_final[c]) for c in analizables])
    st.download_button("Descargar PDF (beta, sin gráficos)", pdf_doc,
                       "informe_encuestaexpress.pdf", "application/pdf")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for c in analizables:
            z.writestr(f"{slug_de(c)}.csv", tabla_a_csv(tabla_de(df, c, tipos_final[c])))
    st.download_button("Descargar todas las tablas (ZIP)", buf.getvalue(),
                       "tablas_encuestaexpress.zip", "application/zip")
