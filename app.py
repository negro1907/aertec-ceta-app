import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# âââ CONFIG âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
st.set_page_config(
    page_title="AERTEC â Inteligencia CETA",
    page_icon="âï¸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID        = st.secrets.get("BASE_ID",     "appn6Aq6TDGYIEFns")
TABLE_ID       = st.secrets.get("TABLE_ID",    "tbleTsyCIWB9yRTtp")
WEBHOOK_URL    = st.secrets.get("WEBHOOK_URL", "https://abengole.app.n8n.cloud/webhook/ceta-investigar")

AT_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
AT_HDR = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}

# ââ HELPERS âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def parse_confianza(notas: str) -> str:
    for linea in (notas or "").split("\n"):
        if linea.startswith("Confianza:"):
            return linea.replace("Confianza:", "").strip().split(" ")[0].lower()
    return ""

@st.cache_data(ttl=60, show_spinner="Cargando empresas desde Airtableâ¦")
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
            senales  = f.get("SeÃ±ales / Oportunidad", "")
            investigado = bool(f.get("Nombre Comercial") or senales)
            recs.append({
                "id":             rec["id"],
                "RazÃ³n Social":   f.get("RazÃ³n Social", ""),
                "Nombre Comercial": f.get("Nombre Comercial", ""),
                "Provincia":      f.get("Provincia", ""),
                "Localidad":      f.get("Localidad", ""),
                "Email":          f.get("Email", ""),
                "Website":        f.get("Website", ""),
                "IATA":           f.get("IATA", ""),
                "SeÃ±ales":        senales,
                "Notas":          notas,
                "Confianza":      confianza,
                "En Cola":        bool(f.get("En Cola", False)),
                "Servicios":      f.get("Servicios Destacados", ""),
                "En Cola":        f.get("En Cola", False),
                "Investigado":    investigado,
                "Ãlt. Act.":      f.get("Ãlt. Act. Base", ""),
            })
        offset = data.get("offset")
        if not offset:
            break
    return pd.DataFrame(recs)

def marcar_en_cola(ids: list, valor: bool):
    """Actualiza el campo En Cola en Airtable (mÃ¡x 10 por request)."""
    for i in range(0, len(ids), 10):
        chunk = ids[i:i+10]
        payload = {"records": [{"id": rid, "fields": {"En Cola": valor}} for rid in chunk]}
        requests.patch(AT_URL, headers=AT_HDR, json=payload)

def disparar_webhook(modo: str, filtro_valor: str = "", limite: int = 50):
    """Llama al webhook de n8n para iniciar el proceso de investigaciÃ³n."""
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

# âââ ESTILOS âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

# âââ HEADER ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("## âï¸")
with col_title:
    st.title("AERTEC â Inteligencia Comercial CETA")
    st.caption(f"Datos actualizados hace menos de 1 minuto Â· {datetime.now().strftime('%d/%m/%Y %H:%M')}")

df = cargar_todas()

# âââ TABS ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
tab1, tab2 = st.tabs(["ð  Panel de Control", "ð  Dashboard de Resultados"])


# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TAB 1 â PANEL DE CONTROL
# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab1:

    # ââ MÃ©tricas rÃ¡pidas âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    m1, m2, m3, m4 = st.columns(4)
    en_cola  = int(df["En Cola"].sum())
    sin_inv  = len(df[~df["Investigado"]])
    inv_cnt  = len(df[df["Investigado"]])
    m1.metric("Total CETA",      len(df))
    m2.metric("Sin investigar",  sin_inv)
    m3.metric("ð En Cola ahora", en_cola)
    m4.metric("â Investigados",   inv_cnt)

    st.divider()

    # ââ Configurar disparo âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    st.subheader("âï¸  Configurar proceso de investigaciÃ³n")

    MODOS = {
        "ð  Cola â empresas marcadas En Cola":       "cola",
        "ð  Todos â empresas sin email (pendientes)": "todos",
        "ðºï¸   Provincia â filtrar por provincia":      "provincia",
        "ð¬  Aeropuerto â filtrar por cÃ³digo IATA":   "aeropuerto",
    }

    col_m, col_v, col_l = st.columns([3, 3, 2])
    with col_m:
        modo_label = st.selectbox("Modo de operaciÃ³n", list(MODOS.keys()))
        modo_key   = MODOS[modo_label]

    with col_v:
        filtro_val = ""
        if modo_key == "provincia":
            provs = sorted(df["Provincia"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("Provincia", provs if provs else ["Buenos Aires"])
        elif modo_key == "aeropuerto":
            iatas = sorted(df["IATA"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("CÃ³digo IATA", iatas if iatas else ["SABE","SACO","SARC"])
        else:
            st.empty()

    with col_l:
        limite = st.number_input("LÃ­mite de empresas", min_value=1, max_value=628, value=30, step=10)

    # ââ Contexto del modo seleccionado âââââââââââââââââââââââââââââââââââââââââââ
    if modo_key == "cola":
        st.info(f"ð Se procesarÃ¡n las **{en_cola}** empresas actualmente marcadas como *En Cola*.")
    elif modo_key == "todos":
        st.info(f"ð Se procesarÃ¡n hasta **{limite}** empresas sin email registrado (en orden Airtable).")
    elif modo_key == "provincia":
        cnt   = len(df[df["Provincia"] == filtro_val])
        cnt_s = len(df[(df["Provincia"] == filtro_val) & ~df["Investigado"]])
        st.info(f"ðºï¸ **{filtro_val}**: {cnt} empresas totales, {cnt_s} sin investigar.")
    elif modo_key == "aeropuerto":
        cnt = len(df[df["IATA"] == filtro_val])
        st.info(f"ð¬ **{filtro_val}**: {cnt} empresas registradas en ese aeropuerto.")

    # ââ BotÃ³n principal ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("ð  Iniciar investigaciÃ³n", type="primary", use_container_width=True):
            if modo_key == "cola" and en_cola == 0:
                st.warning("No hay empresas En Cola. SeleccionÃ¡ empresas abajo y marcalas primero.")
            else:
                with st.spinner("Enviando solicitud a n8nâ¦"):
                    status, resp = disparar_webhook(modo_key, filtro_val, limite)
                if status and status < 300:
                    st.success(f"â Proceso iniciado â modo **{modo_key}**, lÃ­mite **{limite}** Â· n8n: {resp}")
                else:
                    st.error(f"â Error {status}: {resp}")

    st.divider()

    # ââ GestiÃ³n manual de la cola ââââââââââââââââââââââââââââââââââââââââââââââââ
    st.subheader("ð  Gestionar cola manualmente")
    st.caption("BuscÃ¡, filtrÃ¡ y marcÃ¡ empresas especÃ­ficas para agregar o quitar de la cola.")

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
        busq = st.text_input("ð Buscar razÃ³n social", placeholder="ej: SLA, Aeroâ¦", key="ctrl_busq")

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
        df_ctrl = df_ctrl[df_ctrl["RazÃ³n Social"].str.contains(busq, case=False, na=False)]

    st.caption(f"{len(df_ctrl)} empresas")

    df_show = df_ctrl[["RazÃ³n Social","Provincia","Localidad","Investigado","En Cola"]]\
        .assign(Seleccionar=False).reset_index(drop=True)

    sel = st.data_editor(
        df_show,
        column_config={
            "Seleccionar":  st.column_config.CheckboxColumn("â Sel.", width="small"),
            "Investigado":  st.column_config.CheckboxColumn("â Inv.", width="small"),
            "En Cola":      st.column_config.CheckboxColumn("ð Cola", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_ctrl",
        disabled=["RazÃ³n Social","Provincia","Localidad","Investigado","En Cola"],
    )

    ids_sel = df_ctrl.iloc[sel[sel["Seleccionar"]].index]["id"].tolist()
    n_sel   = len(ids_sel)

    ca, cb, _ = st.columns([2, 2, 4])
    with ca:
        if st.button(f"â  Agregar a Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, True)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas â En Cola â")
            time.sleep(0.5)
            st.rerun()
    with cb:
        if st.button(f"â  Quitar de Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, False)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas quitadas de cola")
            time.sleep(0.5)
            st.rerun()


# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TAB 2 â DASHBOARD
# ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with tab2:

    inv  = df[df["Investigado"]]
    alta = len(inv[inv["Confianza"] == "alta"])
    media= len(inv[inv["Confianza"] == "media"])
    baja = len(inv[inv["Confianza"] == "baja"])
    sd   = len(inv[inv["Confianza"] == ""])

    # ââ MÃ©tricas âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total CETA",       len(df))
    c2.metric("Investigados",      len(inv), f"{100*len(inv)//max(len(df),1)}%")
    c3.metric("ð¢ Alta confianza", alta)
    c4.metric("ð¡ Media",          media)
    c5.metric("â« Baja / s/d",     baja + sd)

    # ââ GrÃ¡fico por provincia âââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

    # ââ Filtros âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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
            "RazÃ³n Social","Nombre Comercial","Provincia","Localidad",
            "Confianza","Email","Website","SeÃ±ales","Servicios","Ãlt. Act."
        ]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website":  st.column_config.LinkColumn("Website", width="small"),
            "SeÃ±ales":  st.column_config.TextColumn("SeÃ±ales / Oportunidad", width="large"),
            "Servicios":st.column_config.TextColumn("Servicios", width="medium"),
            "Confianza":st.column_config.TextColumn("Conf.", width="small"),
        },
    )

    # ââ Exportar ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    col_exp, col_ref = st.columns([2, 6])
    with col_exp:
        ts  = datetime.now().strftime("%Y%m%d_%H%M")
        csv = df_dash.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
        st.download_button("â¬ï¸  Exportar CSV", csv, f"ceta_{ts}.csv", "text/csv", use_container_width=True)
    with col_ref:
        if st.button("ð  Actualizar datos", use_container_width=False):
            cargar_todas.clear()
            st.rerun()
