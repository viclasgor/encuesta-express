"""Portada + una tabla por pregunta + graficos dibujados con fpdf2 puro
(rectangulos y texto; sin Kaleido, sin matplotlib, apto para Cloud)."""
from __future__ import annotations
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

from src.pdf_report import dibujar_grafico

FUENTE = "fonts/DejaVuSans.ttf"


def _linea(pdf: FPDF, texto: str, tam: int = 11, alto: int = 7) -> None:
    pdf.set_font("DejaVu", size=tam)
    pdf.multi_cell(0, alto, texto, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _tabla(pdf: FPDF, tabla) -> None:
    pdf.set_font("DejaVu", size=9)
    datos = [[str(c) for c in tabla.columns]]
    datos += [[str(v) for v in fila] for fila in tabla.itertuples(index=False)]
    with pdf.table(first_row_as_headings=True, width=190,
                    headings_style=FontFace(emphasis=None)) as t:
        for fila in datos:
            fila_pdf = t.row()
            for celda in fila:
                fila_pdf.cell(celda)


def generar_pdf(titulo: str, fecha: str, n_total: int, bloques: list[dict],
                cruce: dict | None = None) -> bytes:
    """bloques: [{pregunta, resumen, tabla, grafico?}]; cruce opcional
    {titulo, tabla, grafico?}. Cada pregunta: titulo + tabla + grafico."""
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_font("DejaVu", "", FUENTE)
    pdf.add_page()
    _linea(pdf, titulo, tam=18, alto=10)
    _linea(pdf, f"Fecha: {fecha} · Respuestas totales: {n_total}")
    for b in bloques:
        pdf.add_page()
        _linea(pdf, b["pregunta"], tam=14, alto=9)
        if b.get("resumen"):
            _linea(pdf, b["resumen"], tam=10, alto=6)
        tabla = b.get("tabla")
        if tabla is not None and len(tabla):
            _tabla(pdf, tabla)
        dibujar_grafico(pdf, b.get("grafico"))
    if cruce:
        pdf.add_page()
        _linea(pdf, cruce["titulo"], tam=14, alto=9)
        if cruce.get("tabla") is not None and len(cruce["tabla"]):
            _tabla(pdf, cruce["tabla"])
        if not dibujar_grafico(pdf, cruce.get("grafico")):
            _linea(pdf, "(Cruce solo con tabla.)", tam=9, alto=6)
    return bytes(pdf.output())
