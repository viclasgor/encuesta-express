"""Figuras Plotly (sin Streamlit dentro)."""
from __future__ import annotations
import pandas as pd
import plotly.express as px


def barras_horizontales(tabla: pd.DataFrame, x_col: str = "categoria") -> object:
    # Espera columnas categoria/n/pct de tabla_frecuencias.
    fig = px.bar(tabla, x="n", y=x_col, orientation="h", text="n")
    fig.update_layout(xaxis_title="n", yaxis_title="", height=320)
    return fig


def barras_verticales(tabla: pd.DataFrame, x_col: str = "valor") -> object:
    # Espera columnas valor/n/pct de distribucion_escala.
    fig = px.bar(tabla, x=x_col, y="n", text="n")
    fig.update_layout(xaxis_title=x_col, yaxis_title="n", height=320)
    return fig
