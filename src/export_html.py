"""Informe HTML autonomo (sin Streamlit dentro). Plotly va embebido (S4/S13)."""
from __future__ import annotations
import html as _html
import io
import re

import pandas as pd
from plotly.io import to_html
from plotly.offline import get_plotlyjs


def _fig_div(fig) -> str:
    if fig is None:
        return ""
    return to_html(fig, full_html=False, include_plotlyjs=False)


def tabla_a_csv(tabla) -> str:
    """Una tabla del informe a texto CSV (coma, sin índice)."""
    if not isinstance(tabla, pd.DataFrame):
        tabla = pd.DataFrame(tabla)
    return tabla.to_csv(index=False)


def tablas_a_xlsx(tablas: dict[str, pd.DataFrame]) -> bytes:
    """Todas las tablas del informe en un .xlsx (una hoja por tabla).
    Usa openpyxl, ya fijado en requirements (S18)."""
    buf = io.BytesIO()
    usadas: set[str] = set()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for nombre, t in tablas.items():
            hoja = re.sub(r'[:/\\?*\[\]]', "_", str(nombre))[:31] or "hoja"
            base, k = hoja, 2
            while hoja in usadas:
                hoja = f"{base[:28]}_{k}"
                k += 1
            usadas.add(hoja)
            t.to_excel(w, sheet_name=hoja, index=False)
    return buf.getvalue()


def generar_informe_html(titulo: str, fecha: str, n_total: int,
                         bloques: list[dict], cruce: dict | None = None) -> str:
    """bloques: [{pregunta, tipo, resumen, tabla_html, fig}]; cruce opcional
    {titulo, tablas_html: [...], fig}."""
    partes = [f"<h1>{_html.escape(titulo)}</h1>",
              f"<p>Fecha: {_html.escape(fecha)} · Respuestas totales: {n_total}</p>"]
    for b in bloques:
        partes.append(f"<h2>{_html.escape(b['pregunta'])}</h2>")
        partes.append(f"<p>Tipo: {_html.escape(b.get('tipo', ''))}"
                      + (f" · {b['resumen']}" if b.get("resumen") else "") + "</p>")
        if b.get("tabla_html"):
            partes.append(b["tabla_html"])
        partes.append(_fig_div(b.get("fig")))
    if cruce:
        partes.append(f"<h2>{_html.escape(cruce['titulo'])}</h2>")
        partes.extend(cruce.get("tablas_html", []))
        partes.append(_fig_div(cruce.get("fig")))
    cuerpo = "\n".join(partes)
    return ("<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
            f"<title>{_html.escape(titulo)}</title>"
            f"<script>{get_plotlyjs()}</script></head><body>{cuerpo}</body></html>")
