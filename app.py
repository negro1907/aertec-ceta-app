import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ CONFIG Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
st.set_page_config(
    page_title="AERTEC Ã¢ÂÂ Inteligencia CETA",
    page_icon="Ã¢ÂÂÃ¯Â¸Â",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID        = st.secrets.get("BASE_ID",     "appn6Aq6TDGYIEFns")
TABLE_ID       = st.secrets.get("TABLE_ID",    "tbleTsyCIWB9yRTtp")
WEBHOOK_URL    = st.secrets.get("WEBHOOK_URL", "https://abengole.app.n8n.cloud/webhook/ceta-investigar")

AT_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
AT_HDR = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}

# Ã¢ÂÂÃ¢ÂÂ HELPERS Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
def parse_confianza(notas: str) -> str:
    for linea in (notas or "").split("\n"):
        if linea.startswith("Confianza:"):
            return linea.replace("Confianza:", "").strip().split(" ")[0].lower()
    return ""

@st.cache_data(ttl=60, show_spinner="Cargando empresas desde AirtableÃ¢ÂÂ¦")
def cargar_todas():
    recs, offset = [], None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_URL, headers=AT_HDR, params=params)
        data = r.json()
        for rec in data.get("records", []):
            f = rec["fields"]
            notas    = f.get("Notas Base Mercado", "")
            confianza = parse_confianza(notas)
            senales  = f.get("SeÃÂ±ales / Oportunidad", "")
            investigado = bool(f.get("Nombre Comercial") or senales)
            recs.append({
                "id":             rec["id"],
                "RazÃÂ³n Social":   f.get("RazÃÂ³n Social", ""),
                "Nombre Comercial": f.get("Nombre Comercial", ""),
                "Provincia":      f.get("Provincia", ""),
                "Localidad":      f.get("Localidad", ""),
                "Email":          f.get("Email", ""),
                "Website":        f.get("Website", ""),
                "IATA":           f.get("IATA", ""),
                "SeÃÂ±ales":        senales,
                "Notas":          notas,
                "Confianza":      confianza,
                "En Cola":        bool(f.get("En Cola", False)),
                "Servicios":      f.get("Servicios Destacados", ""),
                "Investigado":    investigado,
                "ÃÂlt. Act.":      f.get("ÃÂlt. Act. Base", ""),
            })
        offset = data.get("offset")
        if not offset:
            break
    return pd.DataFrame(recs)

def marcar_en_cola(ids: list, valor: bool):
    """Actualiza el campo En Cola en Airtable (mÃÂ¡x 10 por request)."""
    for i in range(0, len(ids), 10):
        chunk = ids[i:i+10]
        payload = {"records": [{"id": rid, "fields": {"En Cola": valor}} for rid in chunk]}
        requests.patch(AT_URL, headers=AT_HDR, json=payload)

def disparar_webhook(modo: str, filtro_valor: str = "", limite: int = 50):
    """Llama al webhook de n8n para iniciar el proceso de investigaciÃÂ³n."""
    payload = {
        "modo":         modo,
        "filtro_valor": filtro_valor.upper(),
        "limite":       limite,
        "segmento":     "todos",
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ ESTILOS Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #0d2137;
    border-radius: 10px;
    padding: 14px;
}
[data-testid="stMetric"] label { font-size: .75rem; color: #90a4ae; }
</style>
""", unsafe_allow_html=True)

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ HEADER Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("## Ã¢ÂÂÃ¯Â¸Â")
with col_title:
    st.title("AERTEC Ã¢ÂÂ Inteligencia Comercial CETA")
    st.caption(f"Datos actualizados hace menos de 1 minuto ÃÂ· {datetime.now().strftime('%d/%m/%Y %H:%M')}")

df = cargar_todas()

# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ TABS Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
tab1, tab2 = st.tabs(["Ã°ÂÂÂ  Panel de Control", "Ã°ÂÂÂ  Dashboard de Resultados"])


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# TAB 1 Ã¢ÂÂ PANEL DE CONTROL
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
with tab1:

    # Ã¢ÂÂÃ¢ÂÂ MÃÂ©tricas rÃÂ¡pidas Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    m1, m2, m3, m4 = st.columns(4)
    en_cola  = int(df["En Cola"].sum()) if "En Cola" in df.columns else 0
    sin_inv  = len(df[~df["Investigado"]]) if "Investigado" in df.columns else 0
    inv_cnt  = len(df[df["Investigado"]]) if "Investigado" in df.columns else 0
    m1.metric("Total CETA",      len(df))
    m2.metric("Sin investigar",  sin_inv)
    m3.metric("Ã°ÂÂÂ En Cola ahora", en_cola)
    m4.metric("Ã¢ÂÂ Investigados",   inv_cnt)

    st.divider()

    # Ã¢ÂÂÃ¢ÂÂ Configurar disparo Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    st.subheader("Ã¢ÂÂÃ¯Â¸Â  Configurar proceso de investigaciÃÂ³n")

    MODOS = {
        "Ã°ÂÂÂ  Cola Ã¢ÂÂ empresas marcadas En Cola":       "cola",
        "Ã°ÂÂÂ  Todos Ã¢ÂÂ empresas sin email (pendientes)": "todos",
        "Ã°ÂÂÂºÃ¯Â¸Â   Provincia Ã¢ÂÂ filtrar por provincia":      "provincia",
        "Ã°ÂÂÂ¬  Aeropuerto Ã¢ÂÂ filtrar por cÃÂ³digo IATA":   "aeropuerto",
    }

    col_m, col_v, col_l = st.columns([3, 3, 2])
    with col_m:
        modo_label = st.selectbox("Modo de operaciÃÂ³n", list(MODOS.keys()))
        modo_key   = MODOS[modo_label]

    with col_v:
        filtro_val = ""
        if modo_key == "provincia":
            provs = sorted(df["Provincia"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("Provincia", provs if provs else ["Buenos Aires"])
        elif modo_key == "aeropuerto":
            iatas = sorted(df["IATA"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("CÃÂ³digo IATA", iatas if iatas else ["SABE","SACO","SARC"])
        else:
            st.empty()

    with col_l:
        limite = st.number_input("LÃÂ­mite de empresas", min_value=1, max_value=628, value=30, step=10)

    # Ã¢ÂÂÃ¢ÂÂ Contexto del modo seleccionado Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if modo_key == "cola":
        st.info(f"Ã°ÂÂÂ Se procesarÃÂ¡n las **{en_cola}** empresas actualmente marcadas como *En Cola*.")
    elif modo_key == "todos":
        st.info(f"Ã°ÂÂÂ Se procesarÃÂ¡n hasta **{limite}** empresas sin email registrado (en orden Airtable).")
    elif modo_key == "provincia":
        cnt   = len(df[df["Provincia"] == filtro_val])
        cnt_s = len(df[(df["Provincia"] == filtro_val) & ~df["Investigado"]])
        st.info(f"Ã°ÂÂÂºÃ¯Â¸Â **{filtro_val}**: {cnt} empresas totales, {cnt_s} sin investigar.")
    elif modo_key == "aeropuerto":
        cnt = len(df[df["IATA"] == filtro_val])
        st.info(f"Ã°ÂÂÂ¬ **{filtro_val}**: {cnt} empresas registradas en ese aeropuerto.")

    # Ã¢ÂÂÃ¢ÂÂ BotÃÂ³n principal Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("Ã°ÂÂÂ  Iniciar investigaciÃÂ³n", type="primary", use_container_width=True):
            if modo_key == "cola" and en_cola == 0:
                st.warning("No hay empresas En Cola. SeleccionÃÂ¡ empresas abajo y marcalas primero.")
            else:
                with st.spinner("Enviando solicitud a n8nÃ¢ÂÂ¦"):
                    status, resp = disparar_webhook(modo_key, filtro_val, limite)
                if status and status < 300:
                    st.success(f"Ã¢ÂÂ Proceso iniciado Ã¢ÂÂ modo **{modo_key}**, lÃÂ­mite **{limite}** ÃÂ· n8n: {resp}")
                else:
                    st.error(f"Ã¢ÂÂ Error {status}: {resp}")

    st.divider()

    # Ã¢ÂÂÃ¢ÂÂ GestiÃÂ³n manual de la cola Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    st.subheader("Ã°ÂÂÂ  Gestionar cola manualmente")
    st.caption("BuscÃÂ¡, filtrÃÂ¡ y marcÃÂ¡ empresas especÃÂ­ficas para agregar o quitar de la cola.")

    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        prov_f = st.selectbox(
            "Provincia", ["Todas"] + sorted(df["Provincia"].dropna().unique().tolist()), key="ctrl_prov"
        )
    with cf2:
        estado_f = st.selectbox(
            "Estado", ["Todos", "Sin investigar", "Investigados", "En Cola"], key="ctrl_est"
        )
    with cf3:
        busq = st.text_input("Ã°ÂÂÂ Buscar razÃÂ³n social", placeholder="ej: SLA, AeroÃ¢ÂÂ¦", key="ctrl_busq")

    df_ctrl = df.copy()
    if prov_f != "Todas":
        df_ctrl = df_ctrl[df_ctrl["Provincia"] == prov_f]
    if estado_f == "Sin investigar":
        df_ctrl = df_ctrl[~df_ctrl["Investigado"]]
    elif estado_f == "Investigados":
        df_ctrl = df_ctrl[df_ctrl["Investigado"]]
    elif estado_f == "En Cola":
        df_ctrl = df_ctrl[df_ctrl["En Cola"]]
    if busq:
        df_ctrl = df_ctrl[df_ctrl["RazÃÂ³n Social"].str.contains(busq, case=False, na=False)]

    st.caption(f"{len(df_ctrl)} empresas")

    df_show = df_ctrl[["RazÃÂ³n Social","Provincia","Localidad","Investigado","En Cola"]]\
        .assign(Seleccionar=False).reset_index(drop=True)

    sel = st.data_editor(
        df_show,
        column_config={
            "Seleccionar":  st.column_config.CheckboxColumn("Ã¢ÂÂ Sel.", width="small"),
            "Investigado":  st.column_config.CheckboxColumn("Ã¢ÂÂ Inv.", width="small"),
            "En Cola":      st.column_config.CheckboxColumn("Ã°ÂÂÂ Cola", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_ctrl",
        disabled=["RazÃÂ³n Social","Provincia","Localidad","Investigado","En Cola"],
    )

    ids_sel = df_ctrl.iloc[sel[sel["Seleccionar"]].index]["id"].tolist()
    n_sel   = len(ids_sel)

    ca, cb, _ = st.columns([2, 2, 4])
    with ca:
        if st.button(f"Ã¢ÂÂ  Agregar a Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, True)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas Ã¢ÂÂ En Cola Ã¢ÂÂ")
            time.sleep(0.5)
            st.rerun()
    with cb:
        if st.button(f"Ã¢ÂÂ  Quitar de Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, False)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas quitadas de cola")
            time.sleep(0.5)
            st.rerun()


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# TAB 2 Ã¢ÂÂ DASHBOARD
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
with tab2:

    inv  = df[df["Investigado"]]
    alta = len(inv[inv["Confianza"] == "alta"])
    media= len(inv[inv["Confianza"] == "media"])
    baja = len(inv[inv["Confianza"] == "baja"])
    sd   = len(inv[inv["Confianza"] == ""])

    # Ã¢ÂÂÃ¢ÂÂ MÃÂ©tricas Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total CETA",       len(df))
    c2.metric("Investigados",      len(inv), f"{100*len(inv)//max(len(df),1)}%")
    c3.metric("Ã°ÂÂÂ¢ Alta confianza", alta)
    c4.metric("Ã°ÂÂÂ¡ Media",          media)
    c5.metric("Ã¢ÂÂ« Baja / s/d",     baja + sd)

    # Ã¢ÂÂÃ¢ÂÂ GrÃÂ¡fico por provincia Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if len(inv) > 0:
        st.divider()
        st.caption("Investigados por provincia (top 12)")
        prov_counts = (
            inv.groupby("Provincia").size()
            .sort_values(ascending=False)
            .head(12)
            .rename("Empresas investigadas")
        )
        st.bar_chart(prov_counts, height=220)

    st.divider()

    # Ã¢ÂÂÃ¢ÂÂ Filtros Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    df1, df2, df3 = st.columns(3)
    with df1:
        prov_d = st.selectbox(
            "Provincia", ["Todas"] + sorted(df["Provincia"].dropna().unique().tolist()), key="dash_prov"
        )
    with df2:
        conf_d = st.selectbox(
            "Confianza", ["Todas", "alta", "media", "baja", "sin datos"], key="dash_conf"
        )
    with df3:
        solo_inv = st.checkbox("Solo investigados", value=True, key="dash_inv")

    df_dash = df.copy()
    if prov_d != "Todas":
        df_dash = df_dash[df_dash["Provincia"] == prov_d]
    if conf_d != "Todas":
        df_dash = df_dash[df_dash["Confianza"] == ("" if conf_d == "sin datos" else conf_d)]
    if solo_inv:
        df_dash = df_dash[df_dash["Investigado"]]

    st.caption(f"{len(df_dash)} registros")

    st.dataframe(
        df_dash[[
            "RazÃÂ³n Social","Nombre Comercial","Provincia","Localidad",
            "Confianza","Email","Website","SeÃÂ±ales","Servicios","ÃÂlt. Act."
        ]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website":  st.column_config.LinkColumn("Website", width="small"),
            "SeÃÂ±ales":  st.column_config.TextColumn("SeÃÂ±ales / Oportunidad", width="large"),
            "Servicios":st.column_config.TextColumn("Servicios", width="medium"),
            "Confianza":st.column_config.TextColumn("Conf.", width="small"),
        },
    )

    # Ã¢ÂÂÃ¢ÂÂ Exportar Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    col_exp, col_ref = st.columns([2, 6])
    with col_exp:
        ts  = datetime.now().strftime("%Y%m%d_%H%M")
        csv = df_dash.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
        st.download_button("Ã¢Â¬ÂÃ¯Â¸Â  Exportar CSV", csv, f"ceta_{ts}.csv", "text/csv", use_container_width=True)
    with col_ref:
        if st.button("Ã°ÂÂÂ  Actualizar datos", use_container_width=False):
            cargar_todas.clear()
            st.rerun()
