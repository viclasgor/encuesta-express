"""Figuras Plotly (sin Streamlit dentro). Solo estilo; ningun calculo."""
from __future__ import annotations
import pandas as pd
import plotly.express as px

# Paleta unica de la app (ver .streamlit/config.toml): gama del acento.
PALETA = {
    "acento": "#0B7285",
    "gama": ["#0B7285", "#228E9B", "#3AA99E", "#66C2A5", "#99D5C9", "#C9E9E2"],
    "rejilla": "#E9ECEF",
    "texto": "#212529",
    "fondo": "#FFFFFF",
}
ALTURA = 360


def aplicar_tema(fig, altura: int = ALTURA):
    # Plantilla comun: misma gama, cuadricula suave, sin bordes, altura fija.
    fig.update_layout(
        colorway=PALETA["gama"],
        paper_bgcolor=PALETA["fondo"],
        plot_bgcolor=PALETA["fondo"],
        font=dict(color=PALETA["texto"]),
        xaxis=dict(showgrid=True, gridcolor=PALETA["rejilla"], zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=PALETA["rejilla"], zeroline=False),
        height=altura,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def barras_horizontales(tabla: pd.DataFrame, x_col: str = "categoria") -> object:
    # Espera columnas categoria/n/pct de tabla_frecuencias.
    fig = px.bar(tabla, x="n", y=x_col, orientation="h", text="n")
    fig.update_layout(xaxis_title="n", yaxis_title="")
    return aplicar_tema(fig)


def barras_verticales(tabla: pd.DataFrame, x_col: str = "valor") -> object:
    # Espera columnas valor/n/pct de distribucion_escala.
    fig = px.bar(tabla, x=x_col, y="n", text="n")
    fig.update_layout(xaxis_title=x_col, yaxis_title="n")
    return aplicar_tema(fig)


def barras_cruce(tabla_wide: pd.DataFrame, modo: str = "apiladas",
               ylabel: str | None = None) -> object:
    # Tabla ancha filas x columnas (n o %); modo apiladas (100%) o agrupadas.
    largo = tabla_wide.reset_index().melt(
        id_vars=tabla_wide.index.name or "index", var_name="columna", value_name="y"
    )
    x_col = largo.columns[0]
    fig = px.bar(largo, x=x_col, y="y", color="columna",
                 barmode="stack" if modo == "apiladas" else "group", text="y")
    fig.update_layout(xaxis_title="",
                      yaxis_title=ylabel or ("%" if modo == "apiladas" else "n"))
    return aplicar_tema(fig)


def barras_medias(tabla: pd.DataFrame) -> object:
    # Espera columnas grupo/media de cruce_escala_cat.
    fig = px.bar(tabla, x="grupo", y="media", text="media")
    fig.update_layout(xaxis_title="", yaxis_title="media")
    return aplicar_tema(fig)
