# DESPLIEGUE — EncuestaExpress en Streamlit Community Cloud

> Cambio 30/09: antes era solo local; ahora Cloud como opción documentada (ver `docs/ALCANCE.md`).

## Requisitos previos
- Repo en GitHub con: `app.py` en raíz, `requirements.txt`, `data/ejemplo_encuesta.csv`, `src/`.
- Sin secretos ni datos reales (ver AGENTS.md regla 9).
- Cuenta en https://share.streamlit.io con GitHub conectado.

## Paso a paso (5 min)
1. Sube el proyecto a GitHub (rama `main`).
   ```powershell
   git add app.py requirements.txt src/ data/ docs/ README.md AGENTS.md PROMPT-LOG.md
   git commit -m "EncuestaExpress Incremento 1 (US-01+US-02)"
   git push origin main
   ```
2. Entra en https://share.streamlit.io → **New app** → **Deploy a public app from GitHub**.
3. Elige: Repository = tu repo, Branch = `main`, Main file path = `app.py`.
4. **Advanced settings**: Python version = 3.10+ (3.11 recomendado). No añadas secrets.
5. Pulsa **Deploy**. Espera 2-5 min. Si falla, revisa que `requirements.txt` lleve versiones fijadas (van todas con `==`).
6. Verifica en la URL pública:
   - Activa "Usar CSV de ejemplo" → debe mostrar n total 8, preview 5 filas.
   - Elige `Rango de edad` → tabla n/% suma ~100% + barras horizontales.
   - Sube tu propio CSV Forms → mismo comportamiento, vacíos no rompen.
7. Comparte la URL para la demo del 13/10 (plan B: local con `streamlit run app.py`).

## Fallos típicos
- `No module named streamlit`: revisa `requirements.txt` en raíz y redeploy (Reboot app).
- CSV con `;` o Latin-1: la app muestra error legible; reexporta desde Forms en UTF-8/coma.
- App dormida (sleep): abre la URL 5 min antes de la presentación para despertarla.

## Qué NO desplegar
- No subas CSV con emails/datos personales reales. Usa `data/ejemplo_encuesta.csv`.
