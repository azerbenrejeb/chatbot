import streamlit as st
from modules.module5_conformity.conformity_checker import check_conformity

def display_conformity_widget(session_id: str):
    """
    Widget Streamlit complet de conformité GRI.
    À appeler dans chatbot_app.py après analyse du rapport.
    NE MODIFIE PAS le chatbot existant.
    """

    st.markdown("---")
    st.markdown("## 📊 Vérification de Conformité GRI 2021")

    with st.spinner("Analyse de conformité en cours..."):
        results = check_conformity(session_id)

    # ── Score Global ──────────────────────────────────────────────────────
    global_data = results["Global"]
    global_status = global_data["status"]

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"""
        <div style='background:#1E293B; padding:20px; border-radius:10px;
                    border-left: 5px solid {global_status["color"]}'>
            <h3 style='color:{global_status["color"]}; margin:0'>
                {global_status["emoji"]} {global_status["label"]}
            </h3>
            <p style='color:#94A3B8; margin:5px 0 0 0'>Score global GRI 2021</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            label="Score Global",
            value=f"{global_data['score']}%",
            delta=f"{global_data['presents_count']}/{global_data['total_count']} indicateurs"
        )

    # ── Scores par Dimension ─────────────────────────────────────────────
    st.markdown("### Scores par dimension")

    DIMENSION_CONFIG = {
        "Environnemental": {"emoji": "🌿", "color": "#16A34A"},
        "Social":          {"emoji": "👥", "color": "#2563EB"},
        "Gouvernance":     {"emoji": "⚖️", "color": "#7C3AED"}
    }

    cols = st.columns(3)
    for idx, (dimension, config) in enumerate(DIMENSION_CONFIG.items()):
        dim_data = results[dimension]
        status = dim_data["status"]

        with cols[idx]:
            st.markdown(f"""
            <div style='background:#1E293B; padding:15px;
                        border-radius:10px; text-align:center;
                        border-top: 4px solid {config["color"]}'>
                <h4 style='color:{config["color"]}; margin:0'>
                    {config["emoji"]} {dimension}
                </h4>
                <h2 style='color:white; margin:10px 0'>
                    {dim_data["score"]}%
                </h2>
                <p style='color:{status["color"]}; margin:0'>
                    {status["emoji"]} {status["label"]}
                </p>
                <p style='color:#94A3B8; font-size:12px'>
                    {len(dim_data["presents"])}/{dim_data["total"]} indicateurs
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ── Détail Indicateurs ────────────────────────────────────────────────
    st.markdown("### Détail des indicateurs")

    tab_env, tab_soc, tab_gov = st.tabs([
        "🌿 Environnemental",
        "👥 Social",
        "⚖️ Gouvernance"
    ])

    for tab, dimension in zip(
        [tab_env, tab_soc, tab_gov],
        ["Environnemental", "Social", "Gouvernance"]
    ):
        with tab:
            dim_data = results[dimension]

            # Indicateurs présents
            if dim_data["presents"]:
                st.markdown("**✅ Indicateurs présents :**")
                for ind in dim_data["presents"]:
                    st.success(f"✅ **{ind['code']}** — {ind['nom']}")

            # Indicateurs manquants
            if dim_data["manquants"]:
                st.markdown("**❌ Indicateurs manquants :**")
                for ind in dim_data["manquants"]:
                    st.error(f"❌ **{ind['code']}** — {ind['nom']}")
                    st.caption(f"   → {ind['description']}")

    # ── Recommandations ───────────────────────────────────────────────────
    if results["recommandations"]:
        st.markdown("### 💡 Recommandations d'amélioration")
        for rec in results["recommandations"]:
            st.warning(
                f"**{rec['indicateur']}** ({rec['dimension']}) "
                f"— {rec['action']}"
            )

