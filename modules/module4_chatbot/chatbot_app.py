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

# Auto-démarrage transparent de FastAPI si non actif
def backend_est_actif(url):
    try:
        r = requests.get(f"{url}/stats", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False

@st.cache_resource
def assurer_backend_lance(api_url, port):
    if not backend_est_actif(api_url):
        import subprocess
        import time
        root_dir = Path(__file__).resolve().parent.parent.parent
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
                cwd=str(root_dir),
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for _ in range(15):
                time.sleep(0.5)
                if backend_est_actif(api_url):
                    break
        except Exception as e:
            print(f"[WARN] Impossible de lancer FastAPI automatiquement: {e}")

assurer_backend_lance(FASTAPI_URL, FASTAPI_PORT)

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
                        st.warning(f"Backend HTTP non réactif ({res.get('error')}). Traitement direct local...")
                        try:
                            from app.compliance_checker import extraire_et_stocker_indicateurs
                            from app.config import RAW_PDF_DIR
                            import fitz
                            pdf_local = RAW_PDF_DIR / uploaded_file.name
                            doc = fitz.open(str(pdf_local))
                            full_text = "\n".join([page.get_text('text').strip() for page in doc])
                            doc.close()
                            if full_text:
                                extraire_et_stocker_indicateurs(uploaded_file.name, full_text)
                            st.success("✅ Rapport analysé et indexé avec succès en mode direct !")
                            set_rapport_actif(st, uploaded_file.name)
                            chat_mem.charger_session(st.session_state.session_id)
                            st.session_state.session_id = chat_mem.nouvelle_session(
                                rapport_name=uploaded_file.name,
                                titre=f"Rapport : {uploaded_file.name[:25]}"
                            )
                            st.session_state.messages = []
                            st.session_state.compteur_messages = 0
                            st.session_state["conformite_rapport"] = None
                            st.balloons()
                            st.rerun()
                        except Exception as e_fallback:
                            st.error(f"Erreur d'analyse locale : {e_fallback}")
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
            comp_resp = requests.post(
                f"{FASTAPI_URL}/conformity/check", 
                json={"session_id": str(st.session_state.session_id)},
                timeout=5
            )
            if comp_resp.status_code == 200:
                st.session_state["conformite_rapport"] = comp_resp.json().get("results")
        except Exception:
            pass

        # Fallback direct si l'API backend n'a pas répondu
        if st.session_state.get("conformite_rapport") is None:
            try:
                from modules.module5_conformity.conformity_checker import check_conformity
                from app.compliance_checker import calculer_score_esg_global_100
                res = check_conformity(str(st.session_state.session_id))
                res["score_esg_100"] = calculer_score_esg_global_100(res)
                st.session_state["conformite_rapport"] = res
            except Exception as e:
                print(f"[WARN] Erreur chargement conformité : {e}")

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
                
                # ── Indicateurs identifiés avec numéros de page ──
                trouves = gri_dim.get("trouves", [])
                if trouves:
                    st.markdown("**✅ Indicateurs identifiés :**")
                    for t in trouves:
                        if isinstance(t, dict):
                            code = t.get("code", "")
                            nom = t.get("nom", "")
                            pg = t.get("pages_str", "")
                            badge_pg = f" `[{pg}]`" if pg else ""
                            st.caption(f"✅ **{code}** ({nom}){badge_pg}")
                        else:
                            st.caption(f"✅ **{t}**")

                # ── Indicateurs manquants ──
                manquants = gri_dim.get("manquants", [])
                if manquants:
                    st.markdown("**❌ Indicateurs manquants :**")
                    for m in manquants:
                        code = m.get("code", "") if isinstance(m, dict) else m
                        desc = m.get("nom") or m.get("description", "") if isinstance(m, dict) else ""
                        st.caption(f"❌ **{code}** : {desc}")
                elif not trouves:
                    st.caption("Aucune donnée disponible pour cette dimension.")
                    
        st.write("")
        
        # ── Téléchargement du Rapport d'Audit ESG en PDF ──
        try:
            from modules.module5_conformity.conformity_report import generate_conformity_pdf
            pdf_audit_path = generate_conformity_pdf(
                str(st.session_state.session_id),
                conf,
                rapport_name=st.session_state.rapport_actif or ""
            )
            with open(pdf_audit_path, "rb") as fh:
                st.download_button(
                    label="📥 Télécharger Rapport de Conformité (PDF)",
                    data=fh,
                    file_name=Path(pdf_audit_path).name,
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_dl_audit_pdf"
                )
        except Exception as e:
            st.caption(f"Export PDF audit : {e}")

        st.write("")

        # ── Recommandations Prioritaires ──
        recos_list = []
        try:
            recos_resp = requests.get(
                f"{FASTAPI_URL}/rapport/recommandations", 
                params={"session_id": str(st.session_state.session_id)},
                timeout=5
            )
            if recos_resp.status_code == 200:
                recos_list = recos_resp.json().get("recommandations", [])
        except Exception:
            pass

        if not recos_list:
            try:
                from app.recommandations_generator import generer_recommandations
                recos_list = generer_recommandations(str(st.session_state.session_id))
            except Exception:
                pass

        if recos_list and score_gri < 100:
            st.markdown("### 💡 Recommandations Prioritaires")
            for i, r in enumerate(recos_list, 1):
                st.warning(f"**{i}.** {r}")

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
                resume_txt = ""
                try:
                    resp = requests.post(f"{FASTAPI_URL}/rapport/resume", json={"session_id": str(st.session_state.session_id)}, timeout=90)
                    if resp.status_code == 200:
                        resume_txt = resp.json().get("resume", "")
                except Exception:
                    pass

                if not resume_txt:
                    try:
                        from app.rapport_summary import generer_resume_rapport
                        resume_txt = generer_resume_rapport(st.session_state.rapport_actif)
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du résumé : {e}")

                if resume_txt:
                    st.session_state["resume_auto"] = resume_txt
                    st.rerun()

        if st.session_state.get("resume_auto"):
            st.info(st.session_state["resume_auto"])
        else:
            st.caption("Cliquez sur le bouton ci-dessus pour générer le résumé automatique.")
    else:
        st.caption("Veuillez charger un rapport pour accéder au résumé automatique.")

# ── Onglet Tendances Temporelles ──
with tab_tendances:
    if st.session_state.get("rapport_actif"):
        st.markdown(f"### 📈 Tendances Temporelles Pluri-Annuelles — `{st.session_state.rapport_actif}`")
        tendances = []
        try:
            tend_resp = requests.get(f"{FASTAPI_URL}/rapport/tendances", params={"session_id": str(st.session_state.session_id)}, timeout=10)
            if tend_resp.status_code == 200:
                tendances = tend_resp.json().get("tendances", [])
        except Exception:
            pass

        if not tendances:
            try:
                from app.tendances_detector import detecter_tendances
                tendances = detecter_tendances(st.session_state.session_id, st.session_state.rapport_actif)
            except Exception as e:
                st.caption(f"Tendances non disponibles : {e}")

        if tendances:
            st.success(f"🎯 **{len(tendances)} séries temporelles historiques** identifiées dans ce rapport.")
            import pandas as pd
            for t in tendances:
                is_hausse = t["sens"] == "hausse"
                is_baisse = t["sens"] == "baisse"
                fleche = "📈" if is_hausse else ("📉" if is_baisse else "➡️")
                
                # Couleurs et badges selon impact RSE
                if t.get("alerte"):
                    badge_color = "#dc2626"
                    badge_txt = f"⚠️ Augmentation préoccupante ({t['variation_pct']:+.1f}%)"
                else:
                    badge_color = "#16a34a" if is_baisse or t["reference_gri"] == "GRI 404" else "#0284c7"
                    badge_txt = f"✅ Évolution favorable ({t['variation_pct']:+.1f}%)" if is_baisse or t["reference_gri"] == "GRI 404" else f"Tendance ({t['variation_pct']:+.1f}%)"

                with st.container():
                    st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.03); padding:12px; border-radius:10px; border-left:4px solid {badge_color}; margin-top:12px; margin-bottom:8px;'>
                        <span style='font-size:1.05rem; font-weight:700;'>{fleche} {t['reference_gri']} — {t['description']}</span><br/>
                        <span style='font-size:0.85rem; color:{badge_color}; font-weight:600;'>{badge_txt}</span> &nbsp;|&nbsp;
                        <span style='font-size:0.85rem; color:#94a3b8;'>Période : {t['annees'][0]} ➔ {t['annees'][-1]}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    df_t = pd.DataFrame({"Année": [str(a) for a in t["annees"]], "Valeur": t["valeurs"]})
                    df_t = df_t.set_index("Année")
                    st.line_chart(df_t)
        else:
            st.info("ℹ️ Aucune donnée pluri-annuelle consolidée détectée dans ce rapport. Les tendances nécessitent des séries de données sur au moins 2 exercices.")
    else:
        st.info("👈 Veuillez sélectionner un rapport dans le volet latéral pour analyser ses tendances temporelles.")

# ── Onglet Comparaison Idéale de Deux Rapports ──
with tab_comparaison:
    st.markdown("### ⚖️ Comparateur d'Audit ESG Multi-Rapports")
    st.caption("Comparez deux rapports d'entreprises différentes ou deux millésimes successifs sur les standards GRI 2021 et ESRS.")

    # Récupérer l'ensemble des rapports disponibles (sessions + fichiers analysés)
    from pathlib import Path
    fichiers_disponibles = set()
    for s in chat_mem.get_toutes_sessions():
        if s.get("rapport_name"):
            fichiers_disponibles.add(s["rapport_name"])
    for f in list(Path("data/processed").glob("*_extracted.json")):
        raw_name = f.stem.replace("_extracted", "") + ".pdf"
        fichiers_disponibles.add(raw_name)
    for p in list(Path("rapport_non _annoté").glob("*.pdf")):
        fichiers_disponibles.add(p.name)

    liste_rapports_comp = sorted(list(fichiers_disponibles))

    if len(liste_rapports_comp) >= 2:
        col_ca, col_cb = st.columns(2)
        with col_ca:
            default_a = 0
            if st.session_state.get("rapport_actif") in liste_rapports_comp:
                default_a = liste_rapports_comp.index(st.session_state.rapport_actif)
            sel_a = st.selectbox("📄 Premier Rapport (A) :", liste_rapports_comp, index=default_a, key="comp_sel_a")
        with col_cb:
            default_b = min(1, len(liste_rapports_comp) - 1)
            if default_b == default_a and len(liste_rapports_comp) > 1:
                default_b = (default_a + 1) % len(liste_rapports_comp)
            sel_b = st.selectbox("📄 Second Rapport (B) :", liste_rapports_comp, index=default_b, key="comp_sel_b")

        if st.button("⚖️ Lancer la Comparaison ESG Détaillée", key="btn_compare_exec", use_container_width=True):
            with st.spinner("Audit comparatif des standards GRI et ESRS en cours..."):
                cmp_data = None
                try:
                    cmp_resp = requests.post(f"{FASTAPI_URL}/rapport/comparer", json={"session_id_a": sel_a, "session_id_b": sel_b}, timeout=90)
                    if cmp_resp.status_code == 200:
                        cmp_data = cmp_resp.json()
                except Exception:
                    pass

                if not cmp_data:
                    try:
                        from app.rapport_comparateur import comparer_rapports, generer_synthese_comparaison
                        cmp_data = comparer_rapports(sel_a, sel_b)
                        cmp_data["synthese"] = generer_synthese_comparaison(cmp_data)
                    except Exception as e:
                        st.error(f"Erreur lors de la comparaison : {e}")

                if cmp_data:
                    st.session_state["comparaison_active"] = cmp_data

        if st.session_state.get("comparaison_active"):
            cmp_data = st.session_state["comparaison_active"]

            st.markdown("---")
            # 1. Cartes de Scores Globaux
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); padding:14px; border-radius:10px; border-left:5px solid #0284c7; text-align:center;'>
                    <span style='font-size:0.9rem; color:#94a3b8;'>📄 {cmp_data.get('nom_rapport_a', 'Rapport A')}</span><br/>
                    <span style='font-size:1.8rem; font-weight:800; color:#38bdf8;'>GRI: {cmp_data['score_a']['gri']}%</span> &nbsp;|&nbsp;
                    <span style='font-size:1.1rem; color:#cbd5e1;'>ESRS: {cmp_data['score_a']['esrs']}%</span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.03); padding:14px; border-radius:10px; border-left:5px solid #10b981; text-align:center;'>
                    <span style='font-size:0.9rem; color:#94a3b8;'>📄 {cmp_data.get('nom_rapport_b', 'Rapport B')}</span><br/>
                    <span style='font-size:1.8rem; font-weight:800; color:#34d399;'>GRI: {cmp_data['score_b']['gri']}%</span> &nbsp;|&nbsp;
                    <span style='font-size:1.1rem; color:#cbd5e1;'>ESRS: {cmp_data['score_b']['esrs']}%</span>
                </div>
                """, unsafe_allow_html=True)

            # 2. Graphique comparatif par dimension
            st.markdown("#### 📊 Comparaison des Scores par Dimension")
            s_dims = cmp_data.get("scores_dimensions", {})
            import pandas as pd
            df_dims = pd.DataFrame({
                "Dimension": ["Environnemental", "Social", "Gouvernance"],
                cmp_data.get('nom_rapport_a', 'Rapport A')[:20]: [
                    s_dims.get("Environnemental", {}).get("score_a", 0.0),
                    s_dims.get("Social", {}).get("score_a", 0.0),
                    s_dims.get("Gouvernance", {}).get("score_a", 0.0),
                ],
                cmp_data.get('nom_rapport_b', 'Rapport B')[:20]: [
                    s_dims.get("Environnemental", {}).get("score_b", 0.0),
                    s_dims.get("Social", {}).get("score_b", 0.0),
                    s_dims.get("Gouvernance", {}).get("score_b", 0.0),
                ]
            })
            df_dims = df_dims.set_index("Dimension")
            st.bar_chart(df_dims)

            # 3. Tableau comparatif détaillé des 12 indicateurs GRI
            st.markdown("#### 📋 Matrice Comparative des 12 Indicateurs GRI")
            tbl = cmp_data.get("tableau_comparatif", [])
            if tbl:
                df_tab = pd.DataFrame(tbl)
                st.dataframe(df_tab, use_container_width=True, hide_index=True)

            # 4. Synthèse rédigée
            if cmp_data.get("synthese"):
                st.markdown("#### 🧠 Synthèse Comparative Experte")
                st.info(cmp_data["synthese"])
    else:
        st.info("ℹ️ Il faut au moins 2 rapports disponibles pour effectuer une comparaison.")

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
                reponse_text = None
                sources = []
                try:
                    payload = {
                        "texte": question_to_process,
                        "rapport": st.session_state.rapport_actif,
                        "filtre_label": st.session_state.filtre_esg,
                        "session_id": st.session_state.session_id
                    }
                    response = requests.post(f"{FASTAPI_URL}/question", json=payload, timeout=90)
                    
                    if response.status_code == 200:
                        data = response.json()
                        reponse_text = data.get("reponse", "Aucune réponse générée.")
                        sources = data.get("sources", [])
                except Exception:
                    pass

                # Fallback direct local si l'API HTTP n'a pas répondu
                if not reponse_text:
                    try:
                        from modules.module3_llm_rag.rag_engine import interroger_rapports
                        rag_out = interroger_rapports(
                            question=question_to_process,
                            filtre_label=st.session_state.filtre_esg,
                            filtre_rapport=st.session_state.rapport_actif,
                            session_id=st.session_state.session_id
                        )
                        reponse_text = rag_out.get("reponse", "Aucune réponse générée.")
                        sources = rag_out.get("sources", [])
                    except Exception as e:
                        reponse_text = f"Erreur lors de la génération : {e}"

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
                
                # Enregistrer dans SQLite
                chat_mem.ajouter_message("assistant", reponse_text)
                
                st.rerun()
