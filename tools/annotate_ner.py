"""
Outil d'annotation Streamlit pour le NER (format IOB2).
Permet d'annoter des tokens : O, B-VALEUR, B-UNITE, B-ANNEE, B-TENDANCE, B-REFERENCE_GRI.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import NER_LABELS, NER_DATASET_DIR, create_directories

create_directories()

st.set_page_config(page_title="Annotation NER - ESG", page_icon="🔤", layout="wide")

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
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🔤 Annotation NER — Entités ESG</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Annotez les tokens : VALEUR, UNITE, ANNEE, TENDANCE, REFERENCE_GRI.</p>', unsafe_allow_html=True)

dataset_path = NER_DATASET_DIR / "ner_dataset.txt"

# Charger les phrases existantes
existing_sentences = 0
if dataset_path.exists():
    with open(dataset_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if content:
            existing_sentences = content.count('\n\n') + 1

with st.sidebar:
    st.markdown("### 📊 Progression")
    st.metric("Phrases annotées", existing_sentences)
    st.markdown("---")
    st.markdown("### 📖 Labels IOB2")
    label_colors = {
        'O': '⬜', 'B-VALEUR': '🔢', 'B-UNITE': '📏',
        'B-ANNEE': '📅', 'B-TENDANCE': '📈', 'B-REFERENCE_GRI': '📋'
    }
    for label in NER_LABELS:
        st.write(f"{label_colors.get(label, '⬜')} **{label}**")

# Zone d'annotation
st.markdown("### Annoter une phrase")
phrase = st.text_input("Entrez une phrase ESG :",
                       placeholder="Ex: TLF a réduit ses émissions de 15 % en 2023")

if phrase:
    words = phrase.split()
    st.markdown("### Attribution des labels")

    cols = st.columns(min(len(words), 6))
    annotations = []

    for i, word in enumerate(words):
        col_idx = i % 6
        with cols[col_idx]:
            label = st.selectbox(f"`{word}`", NER_LABELS, key=f"ner_{i}")
            annotations.append((word, label))

    st.markdown("---")
    st.markdown("### Aperçu IOB2")
    preview = ""
    for word, label in annotations:
        preview += f"{word}\t{label}\n"
    st.code(preview, language="text")

    if st.button("✅ Sauvegarder cette annotation"):
        with open(dataset_path, 'a', encoding='utf-8') as f:
            for word, label in annotations:
                f.write(f"{word}\t{label}\n")
            f.write("\n")  # Séparateur de phrases
        st.success(f"Phrase sauvegardée ! ({existing_sentences + 1} phrases au total)")
        st.rerun()
