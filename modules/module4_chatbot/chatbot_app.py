"""
INTERFACE — Streamlit Principal.
Interface utilisateur premium intégrant l'historique en base SQLite,
la validation des PDFs, le filtrage ESG et l'export PDF des rapports de conversation.
"""
import streamlit as st
import requests
import os
import sys
from pathlib import Path

# Résolution des imports du projet
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.config import FASTAPI_HOST, FASTAPI_PORT
from modules.module4_chatbot.session_manager import (
    initialiser_session,
    ajouter_message_session,
    reset_conversation,
    set_rapport_actif,
    get_resume_session
)
from modules.module4_chatbot.chat_memory import ChatMemory
from modules.module4_chatbot.pdf_uploader import (
    valider_pdf,
    sauvegarder_pdf_local,
    envoyer_au_backend,
    lister_rapports_charges
)
from modules.module4_chatbot.export_pdf import exporter_conversation_pdf

# Config de l'application Streamlit
st.set_page_config(
    page_title="RSE Time — ESG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Récupérer l'URL FastAPI depuis l'environnement ou config
fastapi_host_client = FASTAPI_HOST if FASTAPI_HOST != "0.0.0.0" else "127.0.0.1"
FASTAPI_URL = os.getenv("FASTAPI_URL", f"http://{fastapi_host_client}:{FASTAPI_PORT}")

# Initialiser la session Streamlit
initialiser_session(st)

if "predefined_question" not in st.session_state:
    st.session_state["predefined_question"] = None

if "conformite_rapport" not in st.session_state:
    st.session_state["conformite_rapport"] = None

# Initialiser le gestionnaire de mémoire (SQLite)
@st.cache_resource
def get_chat_memory():
    return ChatMemory()

chat_mem = get_chat_memory()

# Si pas de session active en BDD, on en crée une ou on charge la dernière
if st.session_state.session_id is None:
    sessions = chat_mem.get_toutes_sessions()
    if sessions:
        # Charger la dernière session par défaut
        st.session_state.session_id = sessions[0]['id']
        st.session_state.rapport_actif = sessions[0]['rapport_name']
        chat_mem.charger_session(st.session_state.session_id)
        st.session_state.messages = chat_mem.get_historique_complet()
        st.session_state.compteur_messages = len(st.session_state.messages)
    else:
        # Créer une nouvelle session par défaut
        st.session_state.session_id = chat_mem.nouvelle_session(titre="Discussion Générale")
        st.session_state.messages = []
        st.session_state.compteur_messages = 0
else:
    # S'assurer que le chat_mem a bien la session active chargée
    chat_mem.charger_session(st.session_state.session_id)

# Styles CSS personnalisés pour design premium
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #09090e 0%, #111122 50%, #1a1a36 100%);
        color: #e2e8f0;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .tagline {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 25px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .source-box {
        background: rgba(56, 189, 248, 0.05);
        border-left: 4px solid #38bdf8;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    .session-item {
        padding: 8px 12px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.02);
        margin-bottom: 6px;
        cursor: pointer;
        transition: background 0.2s;
    }
    .session-item:hover {
        background: rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# Barre de titre principale
st.markdown('<h1 class="main-title">🤖 Chatbot ESG Intelligent</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">PFE 2025/2026 — RSE Time — Extraction intelligente & Recherche sémantique RAG</p>', unsafe_allow_html=True)

# Barre latérale (Sidebar)
with st.sidebar:
    st.markdown("## ⚙️ Navigation & Historique")
    
    # Bouton Nouvelle session
    if st.button("➕ Nouvelle Conversation", use_container_width=True):
        reset_conversation(st)
        st.session_state.session_id = chat_mem.nouvelle_session(titre="Nouvelle conversation")
        st.rerun()

    # Liste des sessions précédentes
    st.markdown("### 💬 Conversations Précédentes")
    sessions = chat_mem.get_toutes_sessions()
    if sessions:
        for sess in sessions[:5]:  # Afficher les 5 dernières
            col1, col2 = st.columns([4, 1])
            with col1:
                lbl = f"💬 {sess['titre'][:20]}" if len(sess['titre']) > 20 else f"💬 {sess['titre']}"
                if st.button(lbl, key=f"sess_{sess['id']}", use_container_width=True):
                    st.session_state.session_id = sess['id']
                    st.session_state.rapport_actif = sess['rapport_name']
                    chat_mem.charger_session(sess['id'])
                    st.session_state.messages = chat_mem.get_historique_complet()
                    st.session_state.compteur_messages = len(st.session_state.messages)
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{sess['id']}", help="Supprimer la session"):
                    chat_mem.supprimer_session(sess['id'])
                    # Si c'était la session active
                    if st.session_state.session_id == sess['id']:
                        st.session_state.session_id = None
                    st.rerun()
    else:
        st.caption("Aucune session enregistrée.")

    st.markdown("---")

    # 1. Chargement de rapports PDF
    st.markdown("### 📄 Analyser un Nouveau Rapport")
    uploaded_file = st.file_uploader("Choisissez un rapport au format PDF", type="pdf")
    
    if uploaded_file:
        valide, msg = valider_pdf(uploaded_file)
        if valide:
            st.success("Format & taille valides.")
            if st.button("🚀 Lancer l'analyse complète", use_container_width=True):
                with st.spinner("Pipeline IA en cours (CNN → Extraction → ML → Indexation)..."):
                    # Sauvegarder localement
                    sauvegarder_pdf_local(uploaded_file)
                    # Envoyer au backend
                    res = envoyer_au_backend(uploaded_file, api_url=FASTAPI_URL)
                    if res.get("success"):
                        data = res["data"]
                        st.success("✅ Analyse terminée et indexée !")
                        set_rapport_actif(st, uploaded_file.name)
                        # Mettre à jour le titre de la session actuelle
                        chat_mem.charger_session(st.session_state.session_id)
                        # Créer une nouvelle session associée au rapport
                        st.session_state.session_id = chat_mem.nouvelle_session(
                            rapport_name=uploaded_file.name,
                            titre=f"Rapport : {uploaded_file.name[:25]}"
                        )
                        st.session_state.messages = []
                        st.session_state.compteur_messages = 0
                        st.session_state["conformite_rapport"] = None
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Erreur : {res.get('error')}")
        else:
            st.error(msg)
                    
    st.markdown("---")

    # Rapports déjà chargés
    st.markdown("### 📚 Rapports Indexés")
    rapports_charges = lister_rapports_charges()
    if rapports_charges:
        noms_rapports = [r['nom'] for r in rapports_charges]
        idx_default = 0
        if st.session_state.rapport_actif in noms_rapports:
            idx_default = noms_rapports.index(st.session_state.rapport_actif)
        
        sel_rapport = st.selectbox(
            "Rapport actif pour la recherche :",
            ["Tous les rapports"] + noms_rapports,
            index=0 if st.session_state.rapport_actif is None else (idx_default + 1)
        )
        if sel_rapport == "Tous les rapports":
            if st.session_state.get("rapport_actif") is not None:
                set_rapport_actif(st, None)
                chat_mem.mettre_a_jour_rapport("")
                st.session_state["conformite_rapport"] = None
                st.rerun()
        else:
            if st.session_state.get("rapport_actif") != sel_rapport:
                set_rapport_actif(st, sel_rapport)
                chat_mem.mettre_a_jour_rapport(sel_rapport)
                st.session_state["conformite_rapport"] = None
                st.rerun()
    else:
        st.caption("Aucun rapport dans le dossier.")

    # 2. Filtrage des réponses
    st.markdown("### 🎯 Filtrer la recherche")
    filtre_label = st.selectbox(
        "Limiter les réponses au domaine :",
        ["Tous les domaines", "Environnemental", "Social", "Gouvernance"]
    )
    filtre_val = None if filtre_label == "Tous les domaines" else filtre_label
    st.session_state.filtre_esg = filtre_val

    # Auto-chargement de la conformité si un rapport est actif
    if st.session_state.get("rapport_actif") and st.session_state.get("conformite_rapport") is None:
        try:
            comp_resp = requests.post(f"{FASTAPI_URL}/conformity/check", json={"session_id": str(st.session_state.session_id)})
            if comp_resp.status_code == 200:
                st.session_state["conformite_rapport"] = comp_resp.json().get("results")
        except Exception as e:
            print(f"[WARN] Erreur chargement initial conformité: {e}")

    # Avertissement PDF scanné sans texte
    if st.session_state.get("conformite_rapport"):
        conf = st.session_state["conformite_rapport"]
        if not conf.get("has_text", True):
            st.markdown("---")
            st.warning(
                "⚠️ **Document scanné détecté** : Ce PDF ne contient pas de texte vectoriel. "
                "L'extraction a été tentée par OCR (EasyOCR), mais les résultats peuvent être "
                "moins précis. Pour de meilleurs résultats, utilisez un PDF avec du texte sélectionnable."
            )

    # Section Conformité ESG (GRI & ESRS) dans la sidebar
    if st.session_state.get("rapport_actif") and st.session_state.get("conformite_rapport"):
        st.markdown("---")
        st.markdown("### 📊 Conformité ESG (GRI & ESRS)")
        
        conf = st.session_state["conformite_rapport"]
        score_gri = conf.get("score_global_gri", 0.0)
        score_esrs = conf.get("score_global_esrs", 0.0)
        
        def get_color(score):
            if score >= 80:
                return "#16A34A" # green
            elif score >= 50:
                return "#D97706" # orange
            else:
                return "#DC2626" # red

        # ── Score ESG Global sur 100 (pondéré E:40, S:35, G:25) ──
        score_esg_100_data = conf.get("score_esg_100", {})
        score_global_100 = score_esg_100_data.get("score_global_100") if score_esg_100_data else None
        if score_global_100 is not None:
            color_100 = "#16A34A" if score_global_100 >= 70 else ("#D97706" if score_global_100 >= 40 else "#DC2626")
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.05); padding:12px; border-radius:12px; border:2px solid {color_100}; text-align:center; margin-bottom:10px;'>
                <span style='font-size:0.85rem; color:#94a3b8;'>🎯 Score ESG Global</span><br/>
                <span style='font-size:2.2rem; font-weight:800; color:{color_100};'>{score_global_100}/100</span>
            </div>
            """, unsafe_allow_html=True)

        # Affichage des deux scores st.metric côte à côte avec HTML personnalisé pour couleurs
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.03); padding:8px; border-radius:8px; border-left:4px solid {get_color(score_gri)}; text-align:center;'>
                <span style='font-size:0.8rem; color:#94a3b8;'>Score GRI</span><br/>
                <span style='font-size:1.3rem; font-weight:bold; color:{get_color(score_gri)};'>{score_gri}%</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.03); padding:8px; border-radius:8px; border-left:4px solid {get_color(score_esrs)}; text-align:center;'>
                <span style='font-size:0.8rem; color:#94a3b8;'>Score ESRS</span><br/>
                <span style='font-size:1.3rem; font-weight:bold; color:{get_color(score_esrs)};'>{score_esrs}%</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        
        # Expanders par dimension
        dim_emojis = {
            "Environnemental": "🌿",
            "Social": "👥",
            "Gouvernance": "⚖️"
        }
        
        for dimension, dim_data in conf.get("dimensions", {}).items():
            emoji = dim_emojis.get(dimension, "🎯")
            with st.expander(f"{emoji} {dimension}"):
                gri_dim = dim_data.get("gri", {})
                esrs_dim = dim_data.get("esrs", {})
                
                # Barres de progression
                st.write(f"**GRI :** {gri_dim.get('score', 0)}%")
                st.progress(max(0.0, min(1.0, gri_dim.get('score', 0.0) / 100.0)))
                
                st.write(f"**ESRS :** {esrs_dim.get('score', 0)}%")
                st.progress(max(0.0, min(1.0, esrs_dim.get('score', 0.0) / 100.0)))
                
                # Indicateurs manquants
                if gri_dim.get("manquants"):
                    st.markdown("**🇬 Indicateurs GRI manquants :**")
                    for m in gri_dim["manquants"]:
                        st.caption(f"❌ **{m['code']}** : {m['description']}")
                else:
                    st.caption("✅ Tous les indicateurs GRI requis sont présents !")
                    
                if esrs_dim.get("manquants"):
                    st.markdown("**🇪🇺 Indicateurs ESRS manquants :**")
                    for m in esrs_dim["manquants"]:
                        st.caption(f"❌ **{m['code']}** : {m['description']}")
                else:
                    st.caption("✅ Tous les indicateurs ESRS requis sont présents !")
                    
        st.write("")
        
        # ── Recommandations Prioritaires ──
        try:
            recos_resp = requests.get(f"{FASTAPI_URL}/rapport/recommandations", params={"session_id": str(st.session_state.session_id)})
            if recos_resp.status_code == 200:
                recos_data = recos_resp.json()
                recos_list = recos_data.get("recommandations", [])
                if recos_list and score_gri < 100:
                    st.markdown("### 💡 Recommandations Prioritaires")
                    for i, r in enumerate(recos_list, 1):
                        st.warning(f"**{i}.** {r}")
        except Exception:
            pass

        st.write("")
        
        # Boutons d'analyse rapide
        if st.button("🔍 Analyser conformité GRI", use_container_width=True):
            st.session_state["predefined_question"] = "Quel est le niveau de conformité GRI de ce rapport ?"
            st.rerun()
            
        if st.button("🇪🇺 Analyser conformité ESRS/CSRD", use_container_width=True):
            st.session_state["predefined_question"] = "Ce rapport est-il prêt pour la CSRD selon les ESRS ?"
            st.rerun()

    st.markdown("---")
    
    # 3. Statistiques de la base
    st.markdown("### 📊 État de la Base")
    try:
        stats_resp = requests.get(f"{FASTAPI_URL}/stats")
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size:0.9rem;color:#94a3b8;">Paragraphes indexés</span><br>
                <span style="font-size:1.8rem;font-weight:700;color:#38bdf8;">{stats.get('total_documents', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.caption("⚠️ Serveur FastAPI injoignable.")

# Affichage du statut de la session
resume = get_resume_session(st)
status_str = f"👉 **Session active :** {st.session_state.session_id} | "
if resume['rapport_actif']:
    status_str += f"📄 **Rapport :** `{resume['rapport_actif']}`"
    st.session_state["rapport_analyse"] = True
else:
    status_str += "🌐 **Mode RAG global (Tous les rapports)**"
    st.session_state["rapport_analyse"] = False
st.info(status_str)

# ═══════════════════════════════════════════════════════════════════════
# ONGLETS PRINCIPAUX : Chat / Résumé / Tendances / Comparaison
# ═══════════════════════════════════════════════════════════════════════
tab_chat, tab_resume, tab_tendances, tab_comparaison = st.tabs(["💬 Chat", "📝 Résumé", "📈 Tendances", "⚖️ Comparaison"])

# ── Onglet Résumé Automatique ──
with tab_resume:
    if st.session_state.get("rapport_actif"):
        st.markdown("### 📝 Résumé Automatique du Rapport")
        if st.button("🔄 Générer / Actualiser le résumé", key="btn_resume"):
            with st.spinner("Génération du résumé par Mistral..."):
                try:
                    resp = requests.post(f"{FASTAPI_URL}/rapport/resume", json={"session_id": str(st.session_state.session_id)}, timeout=120)
                    if resp.status_code == 200:
                        resume_data = resp.json()
                        st.session_state["resume_auto"] = resume_data.get("resume", "")
                except Exception as e:
                    st.error(f"Erreur : {e}")
        if st.session_state.get("resume_auto"):
            st.info(st.session_state["resume_auto"])
        else:
            st.caption("Cliquez sur le bouton ci-dessus pour générer le résumé automatique.")
    else:
        st.caption("Veuillez charger un rapport pour accéder au résumé automatique.")

# ── Onglet Tendances Temporelles ──
with tab_tendances:
    if st.session_state.get("rapport_actif"):
        st.markdown("### 📈 Tendances Temporelles")
        try:
            tend_resp = requests.get(f"{FASTAPI_URL}/rapport/tendances", params={"session_id": str(st.session_state.session_id)}, timeout=30)
            if tend_resp.status_code == 200:
                tendances = tend_resp.json().get("tendances", [])
                if tendances:
                    for t in tendances:
                        fleche = "⬆️" if t["sens"] == "hausse" else ("⬇️" if t["sens"] == "baisse" else "➡️")
                        couleur = "red" if t["alerte"] else ("green" if t["sens"] == "baisse" and t["reference_gri"] in ["GRI 302","GRI 303","GRI 305","GRI 306"] else "gray")
                        st.markdown(f"**{t['reference_gri']}** — {t['description']} {fleche} `{t['variation_pct']:+.1f}%`")
                        if t.get("alerte"):
                            st.error(f"⚠️ Alerte : {t['description']} en hausse ({t['variation_pct']:+.1f}%)")
                        import pandas as pd
                        df_t = pd.DataFrame({"Année": t["annees"], "Valeur": t["valeurs"]})
                        df_t = df_t.set_index("Année")
                        st.line_chart(df_t)
                else:
                    st.caption("Aucune tendance temporelle détectée (données multi-années requises).")
        except Exception as e:
            st.caption(f"Tendances non disponibles : {e}")
    else:
        st.caption("Veuillez charger un rapport pour accéder aux tendances.")

# ── Onglet Comparaison ──
with tab_comparaison:
    st.markdown("### ⚖️ Comparaison de Deux Rapports")
    sessions_list = chat_mem.get_toutes_sessions()
    sessions_avec_rapport = [s for s in sessions_list if s.get("rapport_name")]
    if len(sessions_avec_rapport) >= 2:
        noms_a = [f"{s['id']} — {s['rapport_name']}" for s in sessions_avec_rapport]
        sel_a = st.selectbox("Rapport A :", noms_a, index=0, key="comp_a")
        sel_b = st.selectbox("Rapport B :", noms_a, index=min(1, len(noms_a)-1), key="comp_b")
        sid_a = sel_a.split(" — ")[0]
        sid_b = sel_b.split(" — ")[0]
        if st.button("🔄 Comparer", key="btn_compare"):
            with st.spinner("Comparaison en cours (Mistral)..."):
                try:
                    cmp_resp = requests.post(f"{FASTAPI_URL}/rapport/comparer", json={"session_id_a": sid_a, "session_id_b": sid_b}, timeout=120)
                    if cmp_resp.status_code == 200:
                        cmp_data = cmp_resp.json()
                        # Scores côte à côte
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric(f"📄 {cmp_data.get('nom_rapport_a', 'A')}", f"GRI: {cmp_data['score_a']['gri']}%")
                        with c2:
                            st.metric(f"📄 {cmp_data.get('nom_rapport_b', 'B')}", f"GRI: {cmp_data['score_b']['gri']}%")
                        # Indicateurs communs
                        communs = cmp_data.get("indicateurs_communs", {})
                        if communs:
                            import pandas as pd
                            rows = []
                            for ref, vals in communs.items():
                                rows.append({"Indicateur": ref, "Description": vals["description"], cmp_data.get('nom_rapport_a','A'): vals["rapport_a"], cmp_data.get('nom_rapport_b','B'): vals["rapport_b"]})
                            df_cmp = pd.DataFrame(rows)
                            st.dataframe(df_cmp, use_container_width=True, hide_index=True)
                        # Synthèse
                        if cmp_data.get("synthese"):
                            st.info(cmp_data["synthese"])
                except Exception as e:
                    st.error(f"Erreur : {e}")
    else:
        st.caption("Il faut au moins 2 rapports chargés pour effectuer une comparaison.")

# ── Onglet Chat (contenu principal) ──
with tab_chat:

    # Boutons d'action rapides sur la conversation
    if len(st.session_state.messages) > 0:
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("🗑️ Vider l'historique", use_container_width=True):
                reset_conversation(st)
                chat_mem.charger_session(st.session_state.session_id)
                st.rerun()
        with c2:
            try:
                pdf_path = exporter_conversation_pdf(
                    st.session_state.messages,
                    rapport_name=st.session_state.rapport_actif or "Recherche RAG Globale"
                )
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Télécharger la conversation en PDF",
                        data=pdf_file,
                        file_name=Path(pdf_path).name,
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.caption(f"Export PDF non disponible : {e}")

    # Afficher les messages de la session active
    for msg in st.session_state.messages:
        role = msg.get("role") or ("user" if msg.get("is_user") else "assistant")
        with st.chat_message(role):
            st.write(msg["content"])
            # Si le message a des sources associées
            if msg.get("sources"):
                st.markdown("#### 📄 Sources citées :")
                for src in msg["sources"]:
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Rapport :</strong> {src['document']} | <strong>Page :</strong> {src['page']} | <strong>Domaine :</strong> {src['label']}<br>
                        <em>"{src['extrait']}"</em>
                    </div>
                    """, unsafe_allow_html=True)

    # Saisie de l'utilisateur
    question_to_process = None
    if st.session_state.get("predefined_question"):
        question_to_process = st.session_state["predefined_question"]
        st.session_state["predefined_question"] = None
    else:
        question = st.chat_input("Posez votre question sur les rapports ESG...")
        if question:
            question_to_process = question

    if question_to_process:
        # Afficher et sauvegarder la question
        with st.chat_message("user"):
            st.write(question_to_process)
        
        # Enregistrer dans Streamlit state
        ajouter_message_session(st, "user", question_to_process)
        
        # Enregistrer dans SQLite
        chat_mem.charger_session(st.session_state.session_id)
        chat_mem.ajouter_message("user", question_to_process)

        # Obtenir la réponse
        with st.chat_message("assistant"):
            with st.spinner("Recherche sémantique et génération avec Mistral..."):
                try:
                    payload = {
                        "texte": question_to_process,
                        "rapport": st.session_state.rapport_actif,
                        "filtre_label": st.session_state.filtre_esg,
                        "session_id": st.session_state.session_id
                    }
                    response = requests.post(f"{FASTAPI_URL}/question", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        reponse_text = data.get("reponse", "Aucune réponse générée.")
                        sources = data.get("sources", [])

                        st.write(reponse_text)
                        
                        if sources:
                            st.markdown("#### 📄 Sources citées :")
                            for src in sources:
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>Rapport :</strong> {src['document']} | <strong>Page :</strong> {src['page']} | <strong>Domaine :</strong> {src['label']}<br>
                                    <em>"{src['extrait']}"</em>
                                </div>
                                """, unsafe_allow_html=True)

                        # Enregistrer dans Streamlit state
                        ajouter_message_session(st, "assistant", reponse_text, sources)
                        
                        # Enregistrer dans SQLite (sans les sources sous format brut complexe pour le prompt)
                        chat_mem.ajouter_message("assistant", reponse_text)
                        
                        st.rerun()
                    else:
                        st.error(f"Erreur API ({response.status_code}): {response.text}")
                except Exception as e:
                    st.error(f"Erreur lors de la connexion au serveur: {e}")
