"""Dibujo de graficos de barras con fpdf2 puro (rectangulos + texto).
Sin Kaleido, sin navegador, sin matplotlib: apto para Streamlit Cloud.
Solo presentacion; los numeros vienen calculados de src/analysis y src/chi2."""
from __future__ import annotations
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Misma paleta de la app (ver assets/estilos.css): verde, azul, coral, amarillo.
SERIES = [(20, 160, 91), (58, 111, 232), (255, 111, 89), (255, 210, 63)]
TINTA = (18, 38, 28)
GRIS = (110, 117, 125)
LINEA = (211, 224, 208)

ALTO_BARRA = 6
PASO = 9


def _cabe(pdf: FPDF, alto_necesario: float) -> None:
    """Salta de pagina si el bloque no cabe entero (no partir graficos)."""
    if pdf.get_y() + alto_necesario > pdf.page_break_trigger:
        pdf.add_page()


def _texto(pdf: FPDF, x: float, y: float, ancho: float, txt: str,
           tam: int = 9, gris: bool = False) -> None:
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu", size=tam)
    pdf.set_text_color(*GRIS if gris else TINTA)
    pdf.cell(ancho, ALTO_BARRA, txt)


def _corta(txt: str, maximo: int = 26) -> str:
    txt = str(txt)
    return txt if len(txt) <= maximo else txt[:maximo - 1] + "…"


def barras_horizontales(pdf: FPDF, etiquetas: list[str], valores: list[float],
                        pcts: list[float] | None = None, x: float = 15,
                        ancho: float = 180) -> bool:
    """Barras H con etiqueta izq. y 'n (p %)' der. Siempre cabe por filas."""
    n = len(etiquetas)
    if n == 0:
        return False
    col_et, col_bar, col_val = 62, 78, 40
    _cabe(pdf, n * PASO + 4)
    y0 = pdf.get_y()
    maxv = max(valores) or 1.0
    for i, et in enumerate(etiquetas):
        y = y0 + i * PASO
        _texto(pdf, x, y, col_et, _corta(et))
        largo = valores[i] / maxv * col_bar
        pdf.set_fill_color(*SERIES[i % len(SERIES)])
        pdf.rect(x + col_et + 2, y + 0.5, largo, ALTO_BARRA - 1, style="F")
        der = f"{valores[i]:g}"
        if pcts is not None:
            der += f" ({pcts[i]:.1f}%)".replace(".", ",")
        _texto(pdf, x + col_et + col_bar + 4, y, col_val, der)
    pdf.set_y(y0 + n * PASO + 4)
    return True


def barras_verticales(pdf: FPDF, etiquetas: list[str], valores: list[float],
                      x: float = 15, ancho: float = 180, alto: float = 62) -> bool:
    """Barras V para escala 1-5, con valor encima."""
    if not etiquetas:
        return False
    _cabe(pdf, alto + 16)
    y0, y_base = pdf.get_y() + 8, pdf.get_y() + 8 + alto
    maxv = max(valores) or 1.0
    paso = ancho / len(etiquetas)
    bw = min(22.0, paso * 0.55)
    for i, et in enumerate(etiquetas):
        h = valores[i] / maxv * alto
        bx = x + i * paso + (paso - bw) / 2
        pdf.set_fill_color(*SERIES[i % len(SERIES)])
        pdf.rect(bx, y_base - h, bw, h, style="F")
        pdf.set_xy(bx - 8, y_base - h - 6)
        pdf.set_font("DejaVu", size=9)
        pdf.set_text_color(*TINTA)
        pdf.cell(bw + 16, 5, f"{valores[i]:g}", align="C")
        pdf.set_xy(bx - 8, y_base + 2)
        pdf.set_font("DejaVu", size=9)
        pdf.set_text_color(*GRIS)
        pdf.cell(bw + 16, 5, _corta(et, 12), align="C")
    pdf.set_y(y_base + 10)
    return True


def barras_apiladas(pdf: FPDF, filas: list[str], columnas: list[str],
                    pct: list[list[float]], x: float = 15,
                    ancho: float = 180) -> bool:
    """Apiladas 100% para cruces; si no caben, False (solo tabla)."""
    if not filas or not columnas or len(filas) > 10 or len(columnas) > 6:
        return False
    col_et = 52
    _cabe(pdf, len(filas) * PASO + 14)
    y0 = pdf.get_y()
    ancho_bar = ancho - col_et - 24
    for i, f in enumerate(filas):
        y = y0 + i * PASO
        _texto(pdf, x, y, col_et, _corta(f, 20))
        xx = x + col_et + 2
        for j in range(len(columnas)):
            w = pct[i][j] / 100 * ancho_bar
            if w > 0.5:
                pdf.set_fill_color(*SERIES[j % len(SERIES)])
                pdf.rect(xx, y + 0.5, w, ALTO_BARRA - 1, style="F")
            xx += w
        _texto(pdf, x + col_et + ancho_bar + 4, y, 20, "100%", gris=True)
    pdf.set_y(y0 + len(filas) * PASO + 2)
    pdf.set_font("DejaVu", size=8)
    pdf.set_text_color(*GRIS)
    with pdf.unbreakable() as doc:
        doc.set_x(x + col_et + 2)
        for j, c in enumerate(columnas):
            doc.set_fill_color(*SERIES[j % len(SERIES)])
            doc.rect(doc.get_x(), doc.get_y(), 4, 4, style="F")
            doc.set_x(doc.get_x() + 6)
            doc.cell(34, 5, _corta(c, 14))
    pdf.ln(8)
    return True


def dibujar_grafico(pdf: FPDF, spec: dict | None) -> bool:
    """Entrada única según spec {'kind': ...}. Nunca falla: si no cabe, False."""
    if not spec:
        return False
    kind = spec.get("kind")
    try:
        if kind == "hbar":
            return barras_horizontales(pdf, spec["etiquetas"], spec["valores"],
                                       spec.get("pcts"))
        if kind == "vbar":
            return barras_verticales(pdf, spec["etiquetas"], spec["valores"])
        if kind == "stacked":
            return barras_apiladas(pdf, spec["filas"], spec["columnas"], spec["pct"])
    except Exception:
        return False
    return False
