"""EncuestaExpress - informe automatico de encuestas Google Forms (calculos en src/)."""
import io
import re
import zipfile
from datetime import date
from html import escape as _esc
from pathlib import Path
import streamlit as st
import pandas as pd
from src.analysis import (
    cargar_csv, cargar_excel, detectar_tipos, sugerir_ignorar, resumen_escala,
    distribucion_escala, listar_texto, perfil_muestra,
    tabla_frecuencias, tabla_multiple, cruce_cat_cat, cruce_escala_cat,
    cruce_multiple_cat, aplicar_filtro,
)
from src.plots import (barras_horizontales, barras_verticales, barras_cruce,
                       barras_medias, PALETA)
from src.export_html import generar_informe_html, tabla_a_csv
from src.export_pdf import generar_pdf
from src.chi2 import chi_cuadrado_cat

TIPOS = ["categorica", "multiple", "escala", "texto", "temporal", "email", "id", "ignorar"]
ETIQUETAS_TIPO = {"categorica": "Opción única", "multiple": "Casillas múltiples",
                  "escala": "Escala 1–5", "texto": "Texto abierto"}
SERIES = PALETA["gama"]  # misma paleta que los graficos: verde, azul, coral, amarillo
GITHUB_URL = "https://github.com/TU_USUARIO/TU_REPO"  # TODO: rellenar (ver informe)
README_URL = "https://github.com/TU_USUARIO/TU_REPO#readme"  # TODO: rellenar

st.set_page_config(page_title="EncuestaExpress", layout="wide",
                   page_icon="📊",
                   menu_items={"About": "EncuestaExpress: del CSV de tu encuesta al informe en minutos."})

_css = (Path(__file__).parent / "assets" / "estilos.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

def slug_de(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", col.lower()).strip("_")[:40] or "pregunta"

def estilo_hoja(tabla: pd.DataFrame, mostrar_indice: bool = False,
                reparto: bool = False) -> str:
    """Tabla como HTML propio .ee-hoja: cuadricula, cabecera, numeros a la
    derecha, % con coma decimal, Total resaltado y columna Reparto opcional."""
    num_cols = set(tabla.select_dtypes(include="number").columns)
    ncols = len(tabla.columns) + (1 if mostrar_indice else 0) + (1 if reparto else 0)
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    h = ["<div class='ee-hoja-wrap'><table class='ee-hoja'><thead>"]
    h.append("<tr class='ee-col'><th class='ee-rn'></th>"
             + "".join(f"<th>{letras[j % 26]}</th>" for j in range(ncols - 1))
             + "</tr>")
    h.append("<tr>")
    h.append("<th class='ee-rn'></th>")
    if mostrar_indice:
        h.append("<th></th>")
    h += [f"<th>{_esc(str(c))}</th>" for c in tabla.columns]
    if reparto:
        h.append("<th>Reparto</th>")
    h.append("</tr></thead><tbody>")
    base = None
    if reparto:
        ref = "pct" if "pct" in tabla.columns else ("pct_resp" if "pct_resp" in tabla.columns else "n")
        datos = tabla[tabla.index != "Total"] if "Total" in tabla.index else tabla
        base = float(datos[ref].max()) or 1.0
    for i, (idx, fila) in enumerate(tabla.iterrows()):
        cls = " class='ee-total'" if idx == "Total" else ""
        h.append(f"<tr{cls}>")
        h.append(f"<td class='ee-rn'>{i + 1}</td>")
        if mostrar_indice:
            h.append(f"<th>{_esc(str(idx))}</th>")
        for c in tabla.columns:
            v = fila[c]
            if pd.isna(v):
                h.append("<td>—</td>")
            elif str(c).lower().startswith("pct"):
                h.append(f"<td class='num'>{float(v):.1f}%</td>".replace(".", ","))
            elif c in num_cols:
                num_txt = str(v)
                try:
                    f = float(v)
                    num_txt = str(int(f)) if f.is_integer() else str(v)
                except (TypeError, ValueError):
                    pass
                h.append(f"<td class='num'>{_esc(num_txt)}</td>")
            else:
                h.append(f"<td>{_esc(str(v))}</td>")
        if reparto:
            if idx == "Total":
                h.append("<td></td>")
            else:
                ref = "pct" if "pct" in tabla.columns else ("pct_resp" if "pct_resp" in tabla.columns else "n")
                ancho = float(fila[ref]) / base * 100
                color = SERIES[i % len(SERIES)]
                h.append(f"<td><div class='ee-reparto' style='width:{ancho:.1f}%;"
                         f"background:{color}'></div></td>")
        h.append("</tr>")
    return "".join(h) + "</tbody></table></div>"

def con_total(tabla: pd.DataFrame) -> pd.DataFrame:
    """Fila Total solo para mostrar (el CSV descargado no la lleva)."""
    fila = pd.DataFrame([{"categoria": "Total", "n": int(tabla["n"].sum()),
                           "pct": round(float(tabla["pct"].sum()), 1)}], index=["Total"])
    return pd.concat([tabla, fila])

def tabla_de(df: pd.DataFrame, col: str, tipo: str) -> pd.DataFrame | None:
    """La tabla que se muestra (y descarga) para una pregunta."""
    if tipo == "texto":
        return pd.DataFrame({"respuesta": listar_texto(df[col])})
    if tipo == "escala":
        return distribucion_escala(df[col])
    if tipo == "multiple":
        return tabla_multiple(df[col])
    return tabla_frecuencias(df[col])

def barra_formula(num: int, col: str, tipo: str, n_valido: int, n_total: int) -> None:
    etiqueta = ETIQUETAS_TIPO.get(tipo, tipo)
    st.html(f"<div class='ee-formula'><span class='ee-fx'>fx</span>"
            f"P{num} · {etiqueta} · n = {n_valido}/{n_total} · {_esc(col)}</div>")

def n_valido_total(df: pd.DataFrame, col: str) -> tuple[int, int]:
    return int((df[col].astype(str).str.strip() != "").sum()), len(df)

def numero_pregunta(df: pd.DataFrame, col: str) -> int:
    return list(df.columns).index(col) + 1  # P1, P2... en orden de columna

def limpiar_datos() -> None:
    """Vuelve al estado vacío (para 'Subir otro archivo' / 'Dejar el ejemplo')."""
    st.session_state["up_key"] = st.session_state.get("up_key", 0) + 1
    st.session_state["usar_ejemplo"] = False
    st.session_state["resaltar_carga"] = False

# --- Lectura de estado (widgets aún no dibujados; mismo estado que verán) ---
uk = st.session_state.get("up_key", 0)
arch_hero = st.session_state.get(f"up_hero_{uk}")
arch_mas = st.session_state.get(f"up_mas_{uk}")
archivo = arch_hero or arch_mas
usa_ejemplo = bool(st.session_state.get("usar_ejemplo"))
df = None
if archivo is not None:
    try:
        if str(archivo.name).lower().endswith(".xlsx"):
            df = cargar_excel(archivo)
        else:
            df = cargar_csv(archivo)
    except Exception as e:
        st.error(f"No pude leer el archivo ({_esc(str(archivo.name))}). "
                 "Usa .csv (UTF-8, comas) o .xlsx con la primera fila de preguntas. "
                 f"Detalle: {e}")
elif usa_ejemplo:
    df = cargar_csv("data/ejemplo_encuesta.csv")

tipos_final: dict[str, str] = {}
f_col_f, f_val_f, n_antes = None, "Todos", 0
analizables: list[str] = []
perfil = {"n_total": 0, "n_valido_por_columna": {}}
completitud, hay_calidad = 1.0, False
if df is not None:
    tipos_auto = detectar_tipos(df)
    for col in df.columns:
        clave = f"tipo_{col}"
        det = tipos_auto[col]
        tipos_final[col] = (st.session_state.get(clave, det)
                            if st.session_state.get(clave) in TIPOS else det)
    cat_filtro = [c for c in df.columns if tipos_auto[c] == "categorica"]
    if st.session_state.get("filtro_col") in (["(sin filtro)"] + cat_filtro):
        f_col_f = st.session_state.get("filtro_col")
    if f_col_f not in (None, "(sin filtro)"):
        vals = ["Todos"] + sorted({v.strip() for v in df[f_col_f].astype(str)
                                   if v.strip() != ""})
        if st.session_state.get("filtro_val") in vals:
            f_val_f = st.session_state.get("filtro_val")
    n_antes = len(df)
    df = aplicar_filtro(df, f_col_f if f_col_f != "(sin filtro)" else None, f_val_f)
    if len(df) == 0:
        st.warning("El filtro no deja respuestas. Elige otro valor.")
        df = None
    else:
        analizables = [c for c in df.columns
                       if tipos_final[c] not in ("ignorar", "temporal", "email", "id")]
        perfil = perfil_muestra(df)
        if len(df) and analizables:
            vacias = sum((df[c].astype(str).str.strip() == "").sum() for c in analizables)
            completitud = 1 - vacias / (len(df) * len(analizables))
        hay_calidad = (completitud < 0.8) or (len(df) < 30)
base_cruce = st.session_state.get("pct_base", "fila")
if base_cruce not in ("fila", "columna"):
    base_cruce = "fila"

def nombre_archivo() -> str:
    if archivo is not None:
        return str(archivo.name)
    if usa_ejemplo and df is not None:
        return "datos de ejemplo"
    return "Sin archivo"

@st.dialog("Formato esperado del CSV")
def ayuda_dialog() -> None:
    st.markdown("- Exportado de **Google Forms**: primera fila = preguntas.\n"
                "- Codificación **UTF-8**, separador **coma** (o Excel `.xlsx`).\n"
                "- Múltiples como `Opción A, Opción B` en una celda.\n"
                "- Vacíos = sin respuesta; email/fecha/id se pueden ignorar.")

def _bloques_informe() -> tuple[list[dict], dict | None]:
    bloques = []
    for c in analizables:
        t = tipos_final[c]
        if t == "texto":
            resp = listar_texto(df[c])
            bloques.append({"pregunta": c, "tipo": t,
                            "resumen": f"{len(resp)} respuestas de {len(df)}",
                            "tabla_html": pd.DataFrame({"respuesta": resp}).to_html(index=False),
                            "fig": None})
        elif t == "escala":
            r = resumen_escala(df[c])
            dist = distribucion_escala(df[c])
            bloques.append({"pregunta": c, "tipo": t,
                            "resumen": (f"media {r['media']}, mediana {r['mediana']}, "
                                        f"DT {r['dt']}, n {r['n_valido']}/{r['n_total']}"),
                            "tabla_html": dist.to_html(index=False),
                            "fig": barras_verticales(dist)})
        elif t == "multiple":
            m = tabla_multiple(df[c])
            bloques.append({"pregunta": c, "tipo": t,
                            "resumen": (f"{m.attrs['n_respondientes']} respondientes, "
                                        "% sobre respondientes"),
                            "tabla_html": m.to_html(index=False),
                            "fig": barras_horizontales(
                                m.rename(columns={"opcion": "categoria", "menciones": "n"}))})
        else:
            f = tabla_frecuencias(df[c])
            bloques.append({"pregunta": c, "tipo": t,
                            "resumen": f"n válido {f.attrs['n_valido']}/{f.attrs['n_total']}",
                            "tabla_html": f.to_html(index=False),
                            "fig": barras_horizontales(f)})
    f_c = st.session_state.get("cruce_filas")
    c_c = st.session_state.get("cruce_cols")
    cruce = None
    if (df is not None and f_c in list(df.columns) and c_c in list(df.columns)
            and f_c != c_c):
        tf, tc = tipos_final.get(f_c), tipos_final.get(c_c)
        if tf == "categorica" and tc == "categorica":
            r = cruce_cat_cat(df[f_c], df[c_c])
            cruce = {"titulo": f"Cruce: {f_c} × {c_c}",
                     "tablas_html": [r["n"].to_html(), r["pct"].to_html()],
                     "fig": barras_cruce(r["pct"], "apiladas")}
    return bloques, cruce

def _html_doc() -> str:
    bloques, cruce = _bloques_informe()
    return generar_informe_html("Informe EncuestaExpress", str(date.today()),
                                len(df), bloques, cruce)

# --- Cabecera en contenedor con key (primer elemento visual) ---
with st.container(key="ee_header"):
    st.html("<div class='ee-topbar'><span class='ee-logo'>E</span>"
            "<span class='ee-nombre'>EncuestaExpress</span>"
            f"<span class='ee-lema'>Informes de encuestas sin pelearte con Excel</span>"
            f"<span class='ee-archivo'>{_esc(nombre_archivo())}"
            + (f" · {len(df)} filas × {len(df.columns)} columnas" if df is not None else "")
            + "</span></div>")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        with st.popover("Archivo"):
            if st.button("Subir otro archivo", key="m_arch_nuevo"):
                limpiar_datos()
                st.rerun()
            if st.button("Probar con datos de ejemplo", key="m_arch_ej"):
                st.session_state["usar_ejemplo"] = True
                st.rerun()
            if usa_ejemplo and st.button("Dejar el ejemplo", key="m_arch_quitar"):
                limpiar_datos()
                st.rerun()
    with m2:
        with st.popover("Datos", disabled=df is None):
            if df is not None:
                st.subheader("Filtro por segmento")
                if cat_filtro:
                    f_col_f = st.selectbox("Columna", ["(sin filtro)"] + cat_filtro,
                                           key="filtro_col")
                    if f_col_f != "(sin filtro)":
                        f_val_f = st.selectbox("Valor", ["Todos"] + sorted(
                            {v.strip() for v in df[f_col_f].astype(str)
                             if v.strip() != ""}),
                            key="filtro_val",
                            help="Filtra todo el informe por este valor.")
                with st.expander("Revisar tipos detectados", expanded=True):
                    st.caption("Corrige el tipo o ignora columnas (id, email, fecha...).")
                    for col in df.columns:
                        det = tipos_auto[col]
                        if sugerir_ignorar(det):
                            st.caption(f"Sugerencia: ignorar '{col}' ({det}).")
                        tipos_final[col] = st.selectbox(
                            col, TIPOS, index=TIPOS.index(tipos_final[col]),
                            key=f"tipo_{col}")
            else:
                st.caption("Carga datos para ver opciones.")
    with m3:
        with st.popover("Informe", disabled=df is None or not analizables):
            if df is not None and analizables:
                st.download_button("Descargar HTML", _html_doc(), "informe.html",
                                   "text/html", key="m_dl_html")
            else:
                st.caption("Carga datos para descargar.")
    with m4:
        if st.button("Ayuda", key="m_ayuda"):
            ayuda_dialog()

# --- Barra de herramientas con botones reales + estado ---
with st.container(key="ee_toolbar"):
    t1, t2, t3, t4, t_est = st.columns([1, 1, 1, 1, 2])
    with t1:
        if st.button("Subir archivo", key="tb_subir"):
            limpiar_datos()
            st.rerun()
    with t2:
        if st.button("Datos de ejemplo", key="tb_ejemplo"):
            st.session_state["usar_ejemplo"] = True
            st.rerun()
    with t3:
        if df is not None and analizables:
            bloques_tb, cruce_tb = _bloques_informe()
            st.download_button("Descargar informe",
                               generar_informe_html("Informe EncuestaExpress",
                                                    str(date.today()), len(df),
                                                    bloques_tb, cruce_tb),
                               "informe.html", "text/html", key="tb_dl")
        else:
            st.button("Descargar informe", key="tb_dl_off", disabled=True,
                      help="Carga datos para activar la descarga.")
    with t4:
        if df is not None:
            base_cruce = st.radio("% sobre", ["fila", "columna"], key="pct_base",
                                  help="Base del cruce categórica×categórica.",
                                  horizontal=True)
    with t_est:
        if df is None:
            st.html("<div class='ee-estado-top'><span class='ee-dot'></span>Listo</div>")
        else:
            st.html("<div class='ee-estado-top'><span class='ee-dot ee-ok'></span>"
                    f"Datos cargados · n={len(df)}"
                    + (" · ⚠ revisa calidad" if hay_calidad else "") + "</div>")

_sel = st.session_state.get("cruce_filas")
if df is not None and _sel in list(df.columns):
    st.html("<div class='ee-fxbar'><span class='ee-a1'>A1</span>"
            f"<span class='ee-fx'>fx</span><span>P{numero_pregunta(df, _sel)} · "
            f"{ETIQUETAS_TIPO.get(tipos_final.get(_sel, ''), '')} · {_esc(_sel)}</span></div>")
else:
    st.html("<div class='ee-fxbar'><span class='ee-a1'>A1</span>"
            "<span class='ee-fx'>fx</span><span>=ANALIZAR(encuesta.csv)</span></div>")

tab_inicio, tab_informe, tab_cruces, tab_exportar, tab_mas = st.tabs(
    ["Inicio", "Informe", "Cruces", "Exportar", "+"])

with tab_inicio:
    st.html("<div class='ee-hero'><h1>Sube tu encuesta.<br>Obtén el "
            "<mark>informe</mark>.</h1>"
            "<p>Arrastra el CSV de Google Forms y la app genera tablas, gráficos y "
            "cruces entre preguntas. Los números los calcula código, no un modelo de IA.</p>"
            "</div>")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Subir mi encuesta", type="primary"):
            st.session_state["resaltar_carga"] = True
    with col_b:
        if st.button("Probar con datos de ejemplo"):
            st.session_state["usar_ejemplo"] = True
            st.rerun()
    st.html("<div class='ee-drop'>Suelta aquí el archivo. Se queda en tu navegador "
            "mientras trabajas con él.</div>")
    up1 = st.file_uploader("CSV o Excel de Google Forms", type=["csv", "xlsx"],
                           label_visibility="collapsed", key=f"up_hero_{uk}")
    if up1 is not None and archivo is None:
        st.rerun()
    if st.session_state.get("resaltar_carga") and archivo is None and not usa_ejemplo:
        st.info("⬆ Elige el archivo en la zona de arriba (el botón no puede abrir "
                "el diálogo del sistema; el navegador solo lo abre desde el uploader).")
    df_ej = cargar_csv("data/ejemplo_encuesta.csv")
    tipos_ej = detectar_tipos(df_ej)
    col_prev = next(c for c in df_ej.columns if tipos_ej[c] == "categorica"
                    and "frecuencia" in c.lower())
    nv, nt = n_valido_total(df_ej, col_prev)
    barra_formula(numero_pregunta(df_ej, col_prev), col_prev, "categorica", nv, nt)
    st.html(estilo_hoja(con_total(tabla_frecuencias(df_ej[col_prev])), reparto=True))
    st.html("<div class='ee-pasos'><div class='ee-paso'><b>Sube el archivo</b>"
            "<span>CSV de Google Forms o Excel (xlsx).</span></div>"
            "<div class='ee-paso'><b>Revisa los tipos</b>"
            "<span>La app detecta cada pregunta; puedes corregirla.</span></div>"
            "<div class='ee-paso'><b>Explora y descarga</b>"
            "<span>Informe, cruces y exportación en HTML.</span></div></div>")

def mostrar_pregunta(col: str, tipo: str) -> None:
    """Una pregunta con barra de fórmulas, tabla estilo hoja y gráfico."""
    with st.container(border=True):
        nv, nt = n_valido_total(df, col)
        barra_formula(numero_pregunta(df, col), col, tipo, nv, nt)
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
                st.html(estilo_hoja(dist))
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
                st.html(estilo_hoja(tabla, reparto=True))
                boton_csv(tabla, "multiple")
            with t2:
                st.plotly_chart(
                    barras_horizontales(
                        tabla.rename(columns={"opcion": "categoria", "menciones": "n"})),
                    width="stretch", key=f"chart_{slug}_multiple")
            return
        tabla = tabla_frecuencias(df[col])
        t1, t2 = st.columns([1, 1.2])
        with t1:
            st.html(estilo_hoja(con_total(tabla), reparto=True))
            boton_csv(tabla, "frecuencias")
        with t2:
            st.plotly_chart(barras_horizontales(tabla), width="stretch",
                            key=f"chart_{slug}_cat")

with tab_informe:
    if df is None or not analizables:
        st.info("Sube un archivo en la pestaña Inicio para ver el informe.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Respuestas", len(df))
        m2.metric("Preguntas analizadas", len(analizables))
        m3.metric("% completitud", f"{completitud:.0%}")
        if completitud < 0.8:
            st.warning(f"Completitud baja ({completitud:.0%}): revisa si alguna pregunta "
                       "se entendió mal.")
        if len(df) < 30:
            st.info("Muestra pequeña (n<30): el chi-cuadrado casi nunca será aplicable.")
        for col in analizables:
            mostrar_pregunta(col, tipos_final[col])
        with st.expander("Perfil de la muestra"):
            st.html(estilo_hoja(pd.DataFrame(
                {"pregunta": list(perfil["n_valido_por_columna"].keys()),
                 "n_válido": list(perfil["n_valido_por_columna"].values())})))
        with st.expander("Ver datos"):
            st.dataframe(df)

with tab_cruces:
    if df is None or not analizables:
        st.info("Sube un archivo en la pestaña Inicio para cruzar variables.")
    else:
        cruzables = [c for c in analizables
                     if tipos_final[c] in ("categorica", "escala", "multiple")]
        if len(cruzables) < 2:
            st.info("Necesitas al menos 2 preguntas cruzables.")
        else:
            f_col = st.selectbox("Filas", cruzables, key="cruce_filas")
            c_col = st.selectbox("Columnas", [c for c in cruzables if c != f_col],
                                 key="cruce_cols")
            # (% fila/columna vive en la toolbar; aquí se usa su valor.)
            if tipos_final[f_col] == "categorica" and tipos_final[c_col] == "categorica":
                r = cruce_cat_cat(df[f_col], df[c_col], base=base_cruce)
                if r["excluidos"]:
                    st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
                st.html(estilo_hoja(r["n"], mostrar_indice=True))
                st.download_button("Descargar CSV (n)", tabla_a_csv(r["n"].reset_index()),
                                   "cruce_n.csv", "text/csv", key="csv_cruce_n")
                st.html(estilo_hoja(r["pct"], mostrar_indice=True))
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
                            st.html(estilo_hoja(t["esperadas"], mostrar_indice=True))
            elif ((tipos_final[f_col], tipos_final[c_col]).count("escala") == 1
                    and (tipos_final[f_col], tipos_final[c_col]).count("categorica") == 1):
                col_esc = f_col if tipos_final[f_col] == "escala" else c_col
                col_cat = c_col if tipos_final[f_col] == "escala" else f_col
                r = cruce_escala_cat(df[col_esc], df[col_cat])
                if r["excluidos"]:
                    st.warning(f"{r['excluidos']} respuestas excluidas por vacíos.")
                st.html(estilo_hoja(r["tabla"]))
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
                st.html(estilo_hoja(r["tabla"]))
                st.download_button("Descargar CSV", tabla_a_csv(r["tabla"]),
                                   "cruce_multiple.csv", "text/csv", key="csv_cruce_mul")
                ancho = r["tabla"].pivot(index="grupo", columns="opcion", values="pct")
                st.plotly_chart(barras_cruce(ancho, "agrupadas", ylabel="% resp."),
                                width="stretch", key="chart_cruce_mul")
            else:
                st.info("Elige dos categóricas, una escala con una categórica, "
                        "o una múltiple con una categórica.")

with tab_exportar:
    if df is None or not analizables:
        st.info("Sube un archivo en la pestaña Inicio para descargar el informe.")
    else:
        st.markdown("### Descargar el informe")
        st.caption("Se exporta lo visible: filtro y tipos corregidos aplicados; "
                   "el cruce si lo configuraste en su pestaña.")
        bloques, cruce = _bloques_informe()
        html_doc = generar_informe_html("Informe EncuestaExpress", str(date.today()),
                                        len(df), bloques, cruce)
        st.download_button("Descargar informe HTML", html_doc,
                           "informe_encuestaexpress.html", "text/html")
        out = []
        for c in analizables:
            t = tipos_final[c]
            if t == "texto":
                resp = listar_texto(df[c])
                out.append({"pregunta": c, "resumen": f"{len(resp)} respuestas",
                            "tabla": pd.DataFrame({"respuesta": resp}),
                            "grafico": None})
            elif t == "escala":
                r = resumen_escala(df[c])
                dist = distribucion_escala(df[c])
                out.append({"pregunta": c,
                            "resumen": (f"media {r['media']}, mediana {r['mediana']}, "
                                        f"DT {r['dt']}, n {r['n_valido']}/{r['n_total']}"),
                            "tabla": dist,
                            "grafico": {"kind": "vbar",
                                         "etiquetas": [str(v) for v in dist["valor"]],
                                         "valores": [float(v) for v in dist["n"]]}})
            elif t == "multiple":
                m = tabla_multiple(df[c])
                out.append({"pregunta": c, "resumen": "% sobre respondientes",
                            "tabla": m,
                            "grafico": {"kind": "hbar",
                                         "etiquetas": list(m["opcion"]),
                                         "valores": [float(v) for v in m["menciones"]],
                                         "pcts": [float(v) for v in m["pct_resp"]]}})
            else:
                f = tabla_frecuencias(df[c])
                out.append({"pregunta": c,
                            "resumen": f"n válido {f.attrs['n_valido']}/{f.attrs['n_total']}",
                            "tabla": f,
                            "grafico": {"kind": "hbar",
                                         "etiquetas": list(f["categoria"]),
                                         "valores": [float(v) for v in f["n"]],
                                         "pcts": [float(v) for v in f["pct"]]}})
        f_c = st.session_state.get("cruce_filas")
        c_c = st.session_state.get("cruce_cols")
        cruce_pdf = None
        if (f_c in list(df.columns) and c_c in list(df.columns) and f_c != c_c
                and {tipos_final.get(f_c), tipos_final.get(c_c)} <= {"categorica", "escala"}):
            tf = tipos_final.get(f_c)
            col_esc = f_c if tf == "escala" else (c_c if tipos_final.get(c_c) == "escala" else None)
            if tf == "categorica" and tipos_final.get(c_c) == "categorica":
                r = cruce_cat_cat(df[f_c], df[c_c])
                n = r["n"].drop(index="Total").drop(columns="Total")
                cruce_pdf = {"titulo": f"Cruce: {f_c} × {c_c}",
                             "tabla": r["n"].reset_index(),
                             "grafico": {"kind": "stacked", "filas": list(n.index),
                                          "columnas": list(n.columns),
                                          "pct": r["pct"].values.tolist()}}
            elif col_esc is not None:
                col_cat = c_c if col_esc == f_c else f_c
                r = cruce_escala_cat(df[col_esc], df[col_cat])
                cruce_pdf = {"titulo": f"Cruce: {col_esc} × {col_cat}",
                             "tabla": r["tabla"],
                             "grafico": {"kind": "vbar",
                                          "etiquetas": list(r["tabla"]["grupo"]),
                                          "valores": [float(v) for v in r["tabla"]["media"]]}}
        pdf_doc = None
        try:
            pdf_doc = generar_pdf("Informe EncuestaExpress", str(date.today()), len(df),
                                  out, cruce_pdf)
        except Exception:
            import traceback
            st.error("El PDF ha fallado al generarse. Copia este detalle para diagnosticarlo:")
            st.code(traceback.format_exc(limit=3))
        if pdf_doc is not None:
            st.download_button("Descargar PDF", pdf_doc,
                               "informe_encuestaexpress.pdf", "application/pdf")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for c in analizables:
                z.writestr(f"{slug_de(c)}.csv", tabla_a_csv(tabla_de(df, c, tipos_final[c])))
        st.download_button("Descargar todas las tablas (ZIP)", buf.getvalue(),
                           "tablas_encuestaexpress.zip", "application/zip")

with tab_mas:
    st.markdown("### Subir otro archivo")
    st.caption("CSV de Google Forms o Excel (xlsx). Sustituye al actual.")
    up2 = st.file_uploader("CSV o Excel", type=["csv", "xlsx"],
                           label_visibility="collapsed", key=f"up_mas_{uk}")
    if up2 is not None and archivo is None:
        st.rerun()
    if st.button("Probar con datos de ejemplo", key="mas_ejemplo"):
        st.session_state["usar_ejemplo"] = True
        st.rerun()

# --- Pie en contenedor con key (último elemento; sticky, nunca fixed) ---
with st.container(key="ee_footer"):
    if df is None:
        _estado = ("<span>Listo</span><span>0 respuestas</span>"
                   "<span>0 preguntas</span><span>Esperando archivo</span>")
    else:
        origen = str(archivo.name) if archivo is not None else "datos de ejemplo"
        segmento = (f" · segmento {f_col_f}={f_val_f}"
                    if f_col_f not in (None, "(sin filtro)") and f_val_f != "Todos" else "")
        _estado = (f"<span>Listo</span><span>{len(df)} respuestas</span>"
                   f"<span>{len(analizables)} preguntas</span>"
                   f"<span>{_esc(origen)}{_esc(segmento)}</span>")
    st.html(f"<div class='ee-estado'>{_estado}</div>")
    _sel2 = st.session_state.get("cruce_filas")
    if df is not None and _sel2 in list(df.columns):
        t2 = tipos_final.get(_sel2)
        st.caption(f"Pregunta seleccionada: {_esc(_sel2)}")
        if t2 == "escala":
            r = resumen_escala(df[_sel2])
            d = distribucion_escala(df[_sel2])
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Recuento", r["n_valido"])
            s2.metric("Media", r["media"])
            s3.metric("Mínimo", d["valor"].min())
            s4.metric("Máximo", d["valor"].max())
        elif t2 == "categorica":
            f = tabla_frecuencias(df[_sel2])
            s1, s2, s3 = st.columns(3)
            s1.metric("Recuento", f.attrs["n_valido"])
            s2.metric("Nº categorías", len(f))
            s3.metric("Moda", f.sort_values("n", ascending=False).iloc[0]["categoria"])
        else:
            st.caption("Estadísticas disponibles para escala y categórica única.")
    elif df is not None:
        st.caption("Elige una pregunta en Cruces (Filas) para ver sus estadísticas aquí.")
    st.html("<div class='ee-pie'>"
            f"<a href='{GITHUB_URL}'>GitHub</a> · <a href='{README_URL}'>README</a> · "
            "Tus datos no se guardan: se procesan en memoria y nada se escribe a disco "
            "ni a bases de datos.</div>")
