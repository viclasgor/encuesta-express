"""Chi-cuadrado solo para categórica×categórica de respuesta única.
Nunca para múltiples, texto o escala (eso lo garantiza la UI)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from streamlit import cache_data

ALFA = 0.05


@cache_data(show_spinner=False)
def chi_cuadrado_cat(tabla_n: pd.DataFrame, alfa: float = ALFA) -> dict:
    """tabla_n: conteos SIN totales. Devuelve stats + veredicto en llano,
    o aplicable=False con el motivo (S7)."""
    vals = tabla_n.to_numpy(dtype=float)
    n = float(vals.sum())
    if vals.size == 0 or n == 0:
        return {"aplicable": False, "motivo": "No hay respuestas válidas para cruzar.",
                "n": 0}
    if vals.shape[0] < 2 or vals.shape[1] < 2:
        return {"aplicable": False,
                "motivo": "El test necesita al menos 2 filas y 2 columnas con datos.",
                "n": int(n)}
    # S16: en 2×2 scipy aplica la corrección de Yates por defecto.
    chi2, p, gl, esperadas = chi2_contingency(vals)
    if (esperadas < 1).any() or (esperadas < 5).mean() > 0.2:
        return {"aplicable": False,
                "motivo": ("Frecuencias esperadas demasiado bajas "
                           "(alguna <1 o más del 20% <5): el test no es fiable con esta muestra."),
                "n": int(n), "chi2": round(float(chi2), 3), "gl": int(gl),
                "p": round(float(p), 4),
                "esperadas": pd.DataFrame(esperadas, index=tabla_n.index,
                                          columns=tabla_n.columns)}
    k = min(vals.shape[0] - 1, vals.shape[1] - 1)
    v = float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0
    if p < alfa:
        veredicto = (f"Hay evidencia de asociación (p={p:.4f} < α={alfa}). "
                     "Esto NO significa que una cause la otra.")
    else:
        veredicto = (f"No hay evidencia de asociación (p={p:.4f} ≥ α={alfa}).")
    return {"aplicable": True, "n": int(n), "chi2": round(float(chi2), 3),
            "gl": int(gl), "p": round(float(p), 4), "v_cramer": round(v, 3),
            "alfa": alfa, "veredicto": veredicto,
            "esperadas": pd.DataFrame(esperadas, index=tabla_n.index,
                                      columns=tabla_n.columns)}
