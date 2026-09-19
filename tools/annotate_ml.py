"""
Outil d'annotation Streamlit pour la classification ML (CamemBERT).
Permet d'annoter des paragraphes en 3 classes : Environnemental, Social, Gouvernance.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ML_CLASSES, ML_DATASET_DIR, PROCESSED_DIR, create_directories

create_directories()

st.set_page_config(page_title="Annotation ML - ESG", page_icon="🏷️", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0813 0%, #110e20 50%, #181330 100%);
        color: #e2e8f0;
    }
    .main-title {
        font-size: 2.3rem; font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title { font-size: 1rem; color: #94a3b8; margin-bottom: 20px; }
    .stButton > button {
        width: 100%; padding: 12px 20px; font-size: 1rem; font-weight: 600;
        border-radius: 12px; margin: 5px 0;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03); color: #e2e8f0;
    }
    .stButton > button:hover {
        border-color: #818cf8; background: rgba(129,140,248,0.12);
        transform: translateY(-2px); box-shadow: 0 4px 15px rgba(129,140,248,0.2);
    }
    .paragraph-box {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 20px; margin: 15px 0;
        font-size: 1.05rem; line-height: 1.7; color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🏷️ Annotation ML — Classification E/S/G</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Classez chaque paragraphe : <strong>Environnemental</strong>, <strong>Social</strong>, ou <strong>Gouvernance</strong>.</p>', unsafe_allow_html=True)

# Charger ou initialiser le dataset
csv_path = ML_DATASET_DIR / "classification" / "ml_dataset.csv"

if csv_path.exists():
    df = pd.read_csv(csv_path)
else:
    df = pd.DataFrame(columns=['texte', 'label'])

# Zone d'ajout de paragraphes
with st.sidebar:
    st.markdown("### 📊 Progression")
    st.metric("Paragraphes annotés", len(df))
    for cls in ML_CLASSES:
        count = len(df[df['label'] == cls]) if len(df) > 0 else 0
        st.write(f"**{cls}** : {count}")

    st.markdown("---")
    st.markdown("### 📤 Exporter")
    if len(df) > 0:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Télécharger CSV", csv_data, "ml_dataset.csv", "text/csv")

# Zone principale : ajout de paragraphe
st.markdown("### Ajouter un paragraphe")
new_text = st.text_area("Collez un paragraphe ESG ici :", height=150,
                        placeholder="Ex: Les émissions CO₂ s'élèvent à 45 200 tCO₂e en 2023...")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🌿 Environnemental", key="btn_env"):
        if new_text.strip():
            new_row = pd.DataFrame([{'texte': new_text.strip(), 'label': 'Environnemental'}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            st.success("✅ Ajouté comme Environnemental")
            st.rerun()
with col2:
    if st.button("👥 Social", key="btn_soc"):
        if new_text.strip():
            new_row = pd.DataFrame([{'texte': new_text.strip(), 'label': 'Social'}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            st.success("✅ Ajouté comme Social")
            st.rerun()
with col3:
    if st.button("🏛️ Gouvernance", key="btn_gouv"):
        if new_text.strip():
            new_row = pd.DataFrame([{'texte': new_text.strip(), 'label': 'Gouvernance'}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            st.success("✅ Ajouté comme Gouvernance")
            st.rerun()

# Afficher les annotations existantes
if len(df) > 0:
    st.markdown("---")
    st.markdown("### 📋 Annotations existantes")
    st.dataframe(df, use_container_width=True, height=400)

    # Supprimer une annotation
    idx_to_delete = st.number_input("Index à supprimer", min_value=0,
                                     max_value=max(0, len(df)-1), step=1)
    if st.button("🗑️ Supprimer"):
        df = df.drop(index=idx_to_delete).reset_index(drop=True)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        st.rerun()
