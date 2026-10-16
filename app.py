import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AERTEC — Inteligencia CETA",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID        = st.secrets.get("BASE_ID",     "appn6Aq6TDGYIEFns")
TABLE_ID       = st.secrets.get("TABLE_ID",    "tbleTsyCIWB9yRTtp")
WEBHOOK_URL    = st.secrets.get("WEBHOOK_URL", "https://abengole.app.n8n.cloud/webhook/ceta-investigar")

AT_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
AT_HDR = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}

# ── HELPERS ─────────────────────────────────────────────────────────────────────
def parse_confianza(notas: str) -> str:
    for linea in (notas or "").split("\n"):
        if linea.startswith("Confianza:"):
            return linea.replace("Confianza:", "").strip().split(" ")[0].lower()
    return ""

@st.cache_data(ttl=60, show_spinner="Cargando empresas desde Airtable…")
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
            senales  = f.get("Señales / Oportunidad", "")
            investigado = bool(f.get("Nombre Comercial") or senales)
            recs.append({
                "id":             rec["id"],
                "Razón Social":   f.get("Razón Social", ""),
                "Nombre Comercial": f.get("Nombre Comercial", ""),
                "Provincia":      f.get("Provincia", ""),
                "Localidad":      f.get("Localidad", ""),
                "Email":          f.get("Email", ""),
                "Website":        f.get("Website", ""),
                "IATA":           f.get("IATA", ""),
                "Señales":        senales,
                "Notas":          notas,
                "Confianza":      confianza,
                "En Cola":        bool(f.get("En Cola", False)),
                "Servicios":      f.get("Servicios Destacados", ""),
                "Investigado":    investigado,
                "Últ. Act.":      f.get("Últ. Act. Base", ""),
                "Teléfono":       f.get("Teléfono", ""),
                "Contacto":       f.get("Contacto Técnico", ""),
                "Cargo":          f.get("Cargo", ""),
                "Dirección":      f.get("Dirección", ""),
                "Redes":          f.get("Redes / IG", ""),
            })
        offset = data.get("offset")
        if not offset:
            break
    return pd.DataFrame(recs)

def marcar_en_cola(ids: list, valor: bool):
    """Actualiza el campo En Cola en Airtable (máx 10 por request)."""
    for i in range(0, len(ids), 10):
        chunk = ids[i:i+10]
        payload = {"records": [{"id": rid, "fields": {"En Cola": valor}} for rid in chunk]}
        requests.patch(AT_URL, headers=AT_HDR, json=payload)

def disparar_webhook(modo: str, filtro_valor: str = "", limite: int = 50):
    """Llama al webhook de n8n para iniciar el proceso de investigación."""
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

# ─── ESTILOS ─────────────────────────────────────────────────────────────────────
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

# ─── HEADER ──────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("## ✈️")
with col_title:
    st.title("AERTEC — Inteligencia Comercial CETA")
    st.caption(f"Datos actualizados hace menos de 1 minuto · {datetime.now().strftime('%d/%m/%Y %H:%M')}")

df = cargar_todas()

# ─── TABS ────────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🚀  Panel de Control", "📊  Dashboard de Resultados"])


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — PANEL DE CONTROL
# ══════════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Métricas rápidas ─────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    en_cola  = int(df["En Cola"].sum()) if "En Cola" in df.columns else 0
    sin_inv  = len(df[~df["Investigado"]]) if "Investigado" in df.columns else 0
    inv_cnt  = len(df[df["Investigado"]]) if "Investigado" in df.columns else 0
    m1.metric("Total CETA",      len(df))
    m2.metric("Sin investigar",  sin_inv)
    m3.metric("🔄 En Cola ahora", en_cola)
    m4.metric("✅ Investigados",   inv_cnt)

    st.divider()

    # ── Configurar disparo ───────────────────────────────────────────────────────
    st.subheader("⚙️  Configurar proceso de investigación")

    MODOS = {
        "🔄  Cola — empresas marcadas En Cola":       "cola",
        "📋  Todos — empresas sin email (pendientes)": "todos",
        "🗺️   Provincia — filtrar por provincia":      "provincia",
        "🛬  Aeropuerto — filtrar por código IATA":   "aeropuerto",
    }

    col_m, col_v, col_l = st.columns([3, 3, 2])
    with col_m:
        modo_label = st.selectbox("Modo de operación", list(MODOS.keys()))
        modo_key   = MODOS[modo_label]

    with col_v:
        filtro_val = ""
        if modo_key == "provincia":
            provs = sorted(df["Provincia"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("Provincia", provs if provs else ["Buenos Aires"])
        elif modo_key == "aeropuerto":
            iatas = sorted(df["IATA"].dropna().replace("", pd.NA).dropna().unique().tolist())
            filtro_val = st.selectbox("Código IATA", iatas if iatas else ["SABE","SACO","SARC"])
        else:
            st.empty()

    with col_l:
        limite = st.number_input("Límite de empresas", min_value=1, max_value=628, value=30, step=10)

    # ── Contexto del modo seleccionado ───────────────────────────────────────────
    if modo_key == "cola":
        st.info(f"🔄 Se procesarán las **{en_cola}** empresas actualmente marcadas como *En Cola*.")
    elif modo_key == "todos":
        st.info(f"📋 Se procesarán hasta **{limite}** empresas sin email registrado (en orden Airtable).")
    elif modo_key == "provincia":
        cnt   = len(df[df["Provincia"] == filtro_val])
        cnt_s = len(df[(df["Provincia"] == filtro_val) & ~df["Investigado"]])
        st.info(f"🗺️ **{filtro_val}**: {cnt} empresas totales, {cnt_s} sin investigar.")
    elif modo_key == "aeropuerto":
        cnt = len(df[df["IATA"] == filtro_val])
        st.info(f"🛬 **{filtro_val}**: {cnt} empresas registradas en ese aeropuerto.")

    # ── Botón principal ──────────────────────────────────────────────────────────
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("🚀  Iniciar investigación", type="primary", use_container_width=True):
            if modo_key == "cola" and en_cola == 0:
                st.warning("No hay empresas En Cola. Seleccioná empresas abajo y marcalas primero.")
            else:
                with st.spinner("Enviando solicitud a n8n…"):
                    status, resp = disparar_webhook(modo_key, filtro_val, limite)
                if status and status < 300:
                    st.success(f"✅ Proceso iniciado — modo **{modo_key}**, límite **{limite}** · n8n: {resp}")
                else:
                    st.error(f"❌ Error {status}: {resp}")

    st.divider()

    # ── Gestión manual de la cola ────────────────────────────────────────────────
    st.subheader("📋  Gestionar cola manualmente")
    st.caption("Buscá, filtrá y marcá empresas específicas para agregar o quitar de la cola.")

    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        prov_f = st.selectbox(
            "Provincia", ["Todas"] + (sorted(df["Provincia"].dropna().unique().tolist()) if "Provincia" in df.columns else []), key="ctrl_prov"
        )
    with cf2:
        estado_f = st.selectbox(
            "Estado", ["Todos", "Sin investigar", "Investigados", "En Cola"], key="ctrl_est"
        )
    with cf3:
        busq = st.text_input("🔍 Buscar razón social", placeholder="ej: SLA, Aero…", key="ctrl_busq")

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
        df_ctrl = df_ctrl[df_ctrl["Razón Social"].str.contains(busq, case=False, na=False)]

    st.caption(f"{len(df_ctrl)} empresas")

    df_show = df_ctrl[["Razón Social","Provincia","Localidad","Investigado","En Cola"]]\
        .assign(Seleccionar=False).reset_index(drop=True)

    sel = st.data_editor(
        df_show,
        column_config={
            "Seleccionar":  st.column_config.CheckboxColumn("✔ Sel.", width="small"),
            "Investigado":  st.column_config.CheckboxColumn("✅ Inv.", width="small"),
            "En Cola":      st.column_config.CheckboxColumn("🔄 Cola", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_ctrl",
        disabled=["Razón Social","Provincia","Localidad","Investigado","En Cola"],
    )

    ids_sel = df_ctrl.iloc[sel[sel["Seleccionar"]].index]["id"].tolist()
    n_sel   = len(ids_sel)

    ca, cb, _ = st.columns([2, 2, 4])
    with ca:
        if st.button(f"✅  Agregar a Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, True)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas → En Cola ✅")
            time.sleep(0.5)
            st.rerun()
    with cb:
        if st.button(f"❌  Quitar de Cola ({n_sel})", disabled=not ids_sel, use_container_width=True):
            marcar_en_cola(ids_sel, False)
            cargar_todas.clear()
            st.success(f"{n_sel} empresas quitadas de cola")
            time.sleep(0.5)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════════
with tab2:

    inv  = df[df["Investigado"]]
    alta = len(inv[inv["Confianza"] == "alta"])
    media= len(inv[inv["Confianza"] == "media"])
    baja = len(inv[inv["Confianza"] == "baja"])
    sd   = len(inv[inv["Confianza"] == ""])

    # ── Métricas ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total CETA",       len(df))
    c2.metric("Investigados",      len(inv), f"{100*len(inv)//max(len(df),1)}%")
    c3.metric("🟢 Alta confianza", alta)
    c4.metric("🟡 Media",          media)
    c5.metric("⚫ Baja / s/d",     baja + sd)

    # ── Última investigación ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("🆕  Última investigación")
    fechas = sorted(
        [x for x in inv["Últ. Act."].dropna().astype(str).unique().tolist() if x],
        reverse=True,
    ) if "Últ. Act." in inv.columns else []
    if not fechas:
        st.info("Todavía no hay empresas con fecha de actualización.")
    else:
        cfa, cfb = st.columns([2, 6])
        with cfa:
            fecha_sel = st.selectbox("Fecha de actualización", fechas, key="ult_fecha")
        ult = inv[inv["Últ. Act."].astype(str) == fecha_sel]
        n_mail = int((ult["Email"].astype(str).str.strip() != "").sum())
        n_tel  = int((ult["Teléfono"].astype(str).str.strip() != "").sum())
        n_web  = int((ult["Website"].astype(str).str.strip() != "").sum())
        with cfb:
            st.caption(
                f"**{len(ult)}** empresas actualizadas · {n_mail} con email · "
                f"{n_tel} con teléfono · {n_web} con sitio web"
            )
        ICONO = {"alta": "🟢", "media": "🟡", "baja": "⚫"}
        for _, r in ult.sort_values("Razón Social").iterrows():
            nombre = r["Razón Social"] or "(sin nombre)"
            if r["Nombre Comercial"]:
                nombre += f" — {r['Nombre Comercial']}"
            conf = r["Confianza"] or "s/d"
            with st.expander(f"{ICONO.get(r['Confianza'], '⚪')}  {nombre}  ·  confianza {conf}"):
                ca, cb = st.columns(2)
                with ca:
                    ubic = ", ".join([x for x in [r["Localidad"], r["Provincia"]] if x])
                    st.markdown(f"**Ubicación:** {ubic or '—'}" + (f"  ·  **IATA/OACI:** {r['IATA']}" if r["IATA"] else ""))
                    st.markdown(f"**Email:** {r['Email'] or '—'}")
                    st.markdown(f"**Teléfono:** {r['Teléfono'] or '—'}")
                    st.markdown(f"**Web:** {r['Website'] or '—'}")
                    st.markdown(f"**Redes:** {r['Redes'] or '—'}")
                with cb:
                    contacto = r["Contacto"] + (f" ({r['Cargo']})" if r["Cargo"] else "") if r["Contacto"] else "—"
                    st.markdown(f"**Contacto:** {contacto}")
                    st.markdown(f"**Dirección:** {r['Dirección'] or '—'}")
                    st.markdown(f"**Servicios:** {r['Servicios'] or '—'}")
                st.markdown("**Señales / Oportunidad:**")
                st.write(r["Señales"] or "—")
                if r["Notas"]:
                    st.caption(r["Notas"])

    # ── Gráfico por provincia ─────────────────────────────────────────────────────
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

    # ── Filtros ───────────────────────────────────────────────────────────────────
    df1, df2, df3 = st.columns(3)
    with df1:
        prov_d = st.selectbox(
            "Provincia", ["Todas"] + (sorted(df["Provincia"].dropna().unique().tolist()) if "Provincia" in df.columns else []), key="dash_prov"
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
            "Razón Social","Nombre Comercial","Provincia","Localidad",
            "Confianza","Email","Website","Señales","Servicios","Últ. Act."
        ]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website":  st.column_config.LinkColumn("Website", width="small"),
            "Señales":  st.column_config.TextColumn("Señales / Oportunidad", width="large"),
            "Servicios":st.column_config.TextColumn("Servicios", width="medium"),
            "Confianza":st.column_config.TextColumn("Conf.", width="small"),
        },
    )

    # ── Exportar ──────────────────────────────────────────────────────────────────
    col_exp, col_ref = st.columns([2, 6])
    with col_exp:
        ts  = datetime.now().strftime("%Y%m%d_%H%M")
        csv = df_dash.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Exportar CSV", csv, f"ceta_{ts}.csv", "text/csv", use_container_width=True)
    with col_ref:
        if st.button("🔄  Actualizar datos", use_container_width=False):
            cargar_todas.clear()
            st.rerun()
