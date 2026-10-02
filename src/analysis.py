"""Logica pura de analisis (sin Streamlit). Testeable con pytest."""
from __future__ import annotations
import csv
import io
import re
import unicodedata
from pathlib import Path
import pandas as pd
from streamlit import cache_data

SEPS = [",", ";", "\t", "|"]


def _decodificar(raw: bytes) -> tuple[str, str]:
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"


def _detectar_sep(muestra: str) -> str:
    try:
        d = csv.Sniffer().sniff(muestra, delimiters="".join(SEPS))
        if d.delimiter in SEPS:
            return d.delimiter
    except Exception:
        pass
    return ","


@cache_data(show_spinner=False)
def leer_csv_bytes(data: bytes) -> tuple[pd.DataFrame, dict]:
    """CSV desde bytes: detecta encoding (utf-8, cae a latin-1) y separador
    (`,`, `;`, tab o `|`). Todo a texto para no romper con vacíos ni rangos."""
    texto, enc = _decodificar(data)
    texto = texto.lstrip("\ufeff")
    sep = _detectar_sep(texto[:20000])
    df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df, {"sep": sep, "encoding": enc}


def cargar_csv(path_o_buffer) -> pd.DataFrame:
    # Ruta o archivo subido; devuelve solo el DataFrame (info en leer_csv_bytes).
    if hasattr(path_o_buffer, "read"):
        data = path_o_buffer.read()
        try:
            path_o_buffer.seek(0)
        except Exception:
            pass
        df, _ = leer_csv_bytes(bytes(data))
        return df
    df, _ = leer_csv_bytes(Path(path_o_buffer).read_bytes())
    return df


def _es_columna_email(nombre: str) -> bool:
    n = nombre.lower()
    return ("mail" in n) or ("correo" in n) or ("e-mail" in n)


def _es_columna_id(nombre: str, serie: pd.Series) -> bool:
    # Identificador (id_respuesta, participante nº X...): nombre que lo sugiere
    # Y valores unicos por fila. Las dos condiciones a la vez (S17).
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", nombre.lower())
        if unicodedata.category(c) != "Mn")
    es_nombre_id = (
        re.search(r"(^|[\W_])(id|codigo|participante|folio|clave|registro|numero|num)(s|es)?([\W_]|$)",
                  sin_acentos) is not None
        or any(s in nombre.lower() for s in ("nº", "n°", "#")))
    if not es_nombre_id:
        return False
    vals = [v.strip() for v in serie.tolist() if v.strip() != ""]
    return len(vals) > 0 and len(set(vals)) / len(vals) > 0.95


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
    """Devuelve: temporal | email | escala | multiple | texto | categorica | id."""
    vals = [v for v in serie.tolist()]
    no_vacios = [v.strip() for v in vals if v.strip() != ""]

    if _es_columna_email(nombre):
        return "email"
    if _es_columna_id(nombre, serie):
        return "id"
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


@cache_data(show_spinner=False)
def detectar_tipos(df: pd.DataFrame) -> dict[str, str]:
    return {col: detectar_tipo(col, df[col]) for col in df.columns}


def sugerir_ignorar(tipo: str) -> bool:
    # Timestamp, emails e identificadores no aportan al informe (S3, S17).
    return tipo in ("temporal", "email", "id")


@cache_data(show_spinner=False)
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


@cache_data(show_spinner=False)
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


@cache_data(show_spinner=False)
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


def listar_texto(serie: pd.Series) -> list[str]:
    """Respuestas no vacías de texto abierto, en orden de llegada."""
    return [v.strip() for v in serie.astype(str).tolist() if v.strip() != ""]


def perfil_muestra(df: pd.DataFrame) -> dict:
    """n total y n válido por columna."""
    return {
        "n_total": int(len(df)),
        "n_valido_por_columna": {
            col: int((df[col].astype(str).str.strip() != "").sum()) for col in df.columns
        },
    }


@cache_data(show_spinner=False)
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


@cache_data(show_spinner=False)
def cruce_cat_cat(s_filas: pd.Series, s_columnas: pd.Series, base: str = "fila") -> dict:
    """Tabla cruzada n + % con totales. Vacios excluidos (se informa cuantos)."""
    f = s_filas.astype(str).str.strip()
    c = s_columnas.astype(str).str.strip()
    mask = (f != "") & (c != "")
    excluidos = int((~mask).sum())
    ct = pd.crosstab(f[mask], c[mask])
    n = ct.copy()
    n["Total"] = n.sum(axis=1)
    n.loc["Total"] = n.sum(axis=0)
    if base == "columna":
        pct = (ct.div(ct.sum(axis=0), axis=1) * 100).round(1)
    else:
        pct = (ct.div(ct.sum(axis=1), axis=0) * 100).round(1)
    return {"n": n, "pct": pct, "excluidos": excluidos, "base": base}


@cache_data(show_spinner=False)
def cruce_escala_cat(s_escala: pd.Series, s_grupo: pd.Series) -> dict:
    """Media, DT y n de la escala por cada grupo. Vacios excluidos."""
    e = pd.to_numeric(s_escala.astype(str).str.strip(), errors="coerce")
    g = s_grupo.astype(str).str.strip()
    mask = e.notna() & (g != "")
    excluidos = int((~mask).sum())
    agg = e[mask].groupby(g[mask]).agg(["mean", "std", "count"]).round(3)
    agg.columns = ["media", "dt", "n"]
    tabla = agg.reset_index()
    tabla.columns = ["grupo", "media", "dt", "n"]
    tabla["dt"] = tabla["dt"].fillna(0.0)  # n=1: sin dispersión que mostrar
    return {"tabla": tabla, "excluidos": excluidos}


@cache_data(show_spinner=False)
def cruce_multiple_cat(s_multiple: pd.Series, s_grupo: pd.Series, sep: str = ", ") -> dict:
    """Múltiple x categórica: por opción y grupo, menciones y % sobre
    respondientes del grupo. Solo descriptivo, sin test (S5)."""
    m = s_multiple.astype(str).str.strip()
    g = s_grupo.astype(str).str.strip()
    mask = (m != "") & (g != "")
    excluidos = int((~mask).sum())
    cols = ["grupo", "opcion", "menciones", "n_grupo", "pct"]
    if int(mask.sum()) == 0:
        return {"tabla": pd.DataFrame(columns=cols), "excluidos": excluidos}
    mm, gg = m[mask], g[mask]
    n_grupo = gg.value_counts()
    pares = [(gg.loc[i], op) for i, v in mm.items()
             for op in [p.strip() for p in v.split(sep) if p.strip() != ""]]
    ct = pd.crosstab(pd.Series([p[0] for p in pares]), pd.Series([p[1] for p in pares]))
    pct = (ct.div(n_grupo, axis=0) * 100).round(1)
    pct = pct.rename_axis(index="grupo", columns="opcion").reset_index()
    largo = pct.melt(id_vars="grupo", var_name="opcion", value_name="pct")
    largo["menciones"] = [int(ct.loc[r["grupo"], r["opcion"]]) for _, r in largo.iterrows()]
    largo["n_grupo"] = largo["grupo"].map(n_grupo).astype(int).tolist()
    return {"tabla": largo.sort_values(["grupo", "opcion"]).reset_index(drop=True),
            "excluidos": excluidos}


def aplicar_filtro(df: pd.DataFrame, columna: str | None, valor: str | None) -> pd.DataFrame:
    """Un valor de una columna filtra todas las filas (S6); 'Todos' no filtra."""
    if not columna or columna == "(sin filtro)" or valor in (None, "", "Todos"):
        return df.copy()
    sel = df[columna].astype(str).str.strip() == str(valor).strip()
    return df[sel].reset_index(drop=True)


def cargar_excel(path_o_buffer, hoja: int | str = 0) -> pd.DataFrame:
    """Lee .xlsx (primera hoja por defecto, S12) y normaliza todo a texto
    como en el CSV, para que la detección funcione igual aunque Excel tipe."""
    df = pd.read_excel(path_o_buffer, sheet_name=hoja, header=0, engine="openpyxl")

    def a_texto(v) -> str:
        if pd.isna(v):
            return ""
        if isinstance(v, bool):
            return str(v)
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip()

    df.columns = [str(c).strip() for c in df.columns]
    return df.apply(lambda col: col.map(a_texto)).astype(str)


STOP_ES = frozenset(
    "el la los las un una unos unas de del en y a ante con por para como más mas "
    "que qué es son hay fue eran sea sean esto esta estos estas ese esa esos esas "
    "aquel aquello mi mis tu tus su sus nuestro nuestra al o u pero sino sinoque "
    "muy tan tanto tanta sin sobre entre hasta desde donde cuando cual cuales "
    "quien quienes porque pues todo toda todos todas mucho mucha muchos muchas "
    "otro otra otros otras mismo misma ese sí no ni ya le les lo me te se nos os "
    "este".split())


def frecuencia_palabras(textos: list[str], top: int = 15) -> pd.DataFrame:
    """Top de palabras en texto abierto (minúsculas, sin stopwords, len>=3)."""
    from collections import Counter
    c: Counter[str] = Counter()
    for t in textos:
        for w in re.findall(r"[a-záéíóúñü]+", str(t).lower()):
            if len(w) >= 3 and w not in STOP_ES:
                c[w] += 1
    top_n = c.most_common(top)
    return pd.DataFrame(top_n, columns=["palabra", "n"])
