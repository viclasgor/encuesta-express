"""PDF minimo del informe: portada + una tabla por pregunta (sin graficos).
Spike US-16 con fpdf2 (puro, apto para Cloud) y fuente DejaVu vendored (S15)."""
from __future__ import annotations
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

FUENTE = "fonts/DejaVuSans.ttf"


def _linea(pdf: FPDF, texto: str, tam: int = 11, alto: int = 7) -> None:
    pdf.set_font("DejaVu", size=tam)
    pdf.multi_cell(0, alto, texto, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generar_pdf(titulo: str, fecha: str, n_total: int, bloques: list[dict]) -> bytes:
    """bloques: [{pregunta, resumen, tabla: DataFrame|None}]. Devuelve bytes PDF."""
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
            pdf.set_font("DejaVu", size=9)
            datos = [[str(c) for c in tabla.columns]]
            datos += [[str(v) for v in fila] for fila in tabla.itertuples(index=False)]
            with pdf.table(first_row_as_headings=True, width=190,
                            headings_style=FontFace(emphasis=None)) as t:
                for fila in datos:
                    fila_pdf = t.row()
                    for celda in fila:
                        fila_pdf.cell(celda)
    return bytes(pdf.output())
