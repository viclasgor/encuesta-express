"""Logica pura de analisis (sin Streamlit). Testeable con pytest."""
from __future__ import annotations
import pandas as pd


def cargar_csv(path_o_buffer) -> pd.DataFrame:
    # CSV estandar Google Forms: UTF-8, coma, primera fila cabecera.
    # Todo se lee como texto para no romper con vacios ni rangos tipo "10-20 €".
    return pd.read_csv(path_o_buffer, encoding="utf-8", sep=",", dtype=str, keep_default_na=False)


def _es_columna_email(nombre: str) -> bool:
    n = nombre.lower()
    return ("mail" in n) or ("correo" in n) or ("e-mail" in n)


def _es_columna_temporal(nombre: str, serie: pd.Series) -> bool:
    n = nombre.lower()
    if ("marca temporal" in n) or ("timestamp" in n) or (n.strip() in ("fecha", "hora")):
        return True
    # Generico solo si parecen fechas (evita confundir escala 1-5 con fechas).
    vals = [v.strip() for v in serie.tolist() if v.strip() != ""]
    if not vals:
        return False
    if not any(("/" in v or "-" in v or ":" in v) for v in vals):
        return False
    try:
        conv = pd.to_datetime(vals, errors="coerce", format="mixed")
        ok = conv.notna().mean()
        return bool(ok > 0.8)
    except Exception:
        return False


def _es_escala(no_vacios: list[str]) -> bool:
    # S2: escala = 100% numerica entera 1-5. Se comprueba ANTES que fechas.
    try:
        nums = pd.to_numeric(pd.Series(no_vacios), errors="coerce")
        return bool(nums.notna().all() and ((nums >= 1) & (nums <= 5)).all())
    except Exception:
        return False


def detectar_tipo(nombre: str, serie: pd.Series) -> str:
    """Devuelve: temporal | email | escala | multiple | texto | categorica."""
    vals = [v for v in serie.tolist()]
    no_vacios = [v.strip() for v in vals if v.strip() != ""]

    if _es_columna_email(nombre):
        return "email"
    if not no_vacios:
        return "categorica"
    if _es_escala(no_vacios):
        return "escala"
    if _es_columna_temporal(nombre, serie):
        return "temporal"

    # Multiple: al menos 2 celdas con ", " (evita confundir un texto con una coma).
    n_multi = sum(1 for v in no_vacios if ", " in v)
    if n_multi >= 2:
        return "multiple"

    # Texto abierto: respuestas largas y muy variadas.
    media_len = sum(len(v) for v in no_vacios) / len(no_vacios)
    ratio_unicas = len(set(no_vacios)) / len(no_vacios)
    if media_len > 18 and ratio_unicas > 0.6 and len(no_vacios) >= 4:
        return "texto"

    return "categorica"


def detectar_tipos(df: pd.DataFrame) -> dict[str, str]:
    return {col: detectar_tipo(col, df[col]) for col in df.columns}


def sugerir_ignorar(tipo: str) -> bool:
    # Timestamp y emails no aportan al informe; se sugiere ignorarlos (S3).
    return tipo in ("temporal", "email")


def tabla_frecuencias(serie: pd.Series) -> pd.DataFrame:
    """Tabla n y % sobre n valido. Vacios excluidos del % (pero contados fuera)."""
    no_vacios = serie[serie.astype(str).str.strip() != ""]
    n_valido = int(len(no_vacios))
    n_total = int(len(serie))
    conteo = no_vacios.value_counts()
    tabla = pd.DataFrame({"categoria": conteo.index, "n": conteo.values})
    tabla["pct"] = (tabla["n"] / n_valido * 100).round(1) if n_valido else 0.0
    tabla.attrs["n_valido"] = n_valido
    tabla.attrs["n_total"] = n_total
    return tabla
