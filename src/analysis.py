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


def resumen_escala(serie: pd.Series) -> dict:
    """Media, mediana y DT (muestral) sobre valores 1-5; vacios excluidos."""
    nums = pd.to_numeric(serie[serie.astype(str).str.strip() != ""], errors="coerce").dropna()
    return {
        "media": round(float(nums.mean()), 3) if len(nums) else None,
        "mediana": round(float(nums.median()), 3) if len(nums) else None,
        "dt": round(float(nums.std()), 3) if len(nums) > 1 else 0.0,
        "n_valido": int(len(nums)),
        "n_total": int(len(serie)),
    }


def distribucion_escala(serie: pd.Series) -> pd.DataFrame:
    """Frecuencia de cada valor de la escala sobre n valido."""
    nums = pd.to_numeric(serie[serie.astype(str).str.strip() != ""], errors="coerce").dropna()
    n_valido = int(len(nums))
    conteo = nums.value_counts().sort_index()
    tabla = pd.DataFrame({"valor": conteo.index, "n": conteo.values})
    tabla["pct"] = (tabla["n"] / n_valido * 100).round(1) if n_valido else 0.0
    tabla.attrs["n_valido"] = n_valido
    tabla.attrs["n_total"] = int(len(serie))
    return tabla


def tabla_multiple(serie: pd.Series, sep: str = ", ") -> pd.DataFrame:
    """Menciones por opcion; % sobre nº de respondientes (puede sumar >100%)."""
    resp = serie.astype(str).str.strip()
    validas = resp[resp != ""]
    n_resp = int(len(validas))
    n_total = int(len(serie))
    conteo: dict[str, int] = {}
    for v in validas:
        for op in [p.strip() for p in v.split(sep) if p.strip() != ""]:
            conteo[op] = conteo.get(op, 0) + 1
    tabla = pd.DataFrame({"opcion": list(conteo.keys()), "menciones": list(conteo.values())})
    tabla = tabla.sort_values("menciones", ascending=False).reset_index(drop=True)
    tabla["pct_resp"] = (tabla["menciones"] / n_resp * 100).round(1) if n_resp else 0.0
    tabla.attrs["n_respondientes"] = n_resp
    tabla.attrs["n_total"] = n_total
    return tabla
