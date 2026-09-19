import streamlit as st
import shutil
from pathlib import Path
import sys
import re


sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import CNN_DATASET_DIR, CNN_CLASSES, PROCESSED_DIR, create_directories

# Créer les dossiers nécessaires
create_directories()

st.set_page_config(page_title="Annotation CNN - ESG Filter", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0813 0%, #110e20 50%, #181330 100%);
        color: #e2e8f0;
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 20px;
    }
    .stButton > button { 
        width: 100%; 
        padding: 14px 20px; 
        font-size: 1.1rem; 
        font-weight: 700;
        border-radius: 12px; 
        margin: 8px 0;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        color: #e2e8f0;
    }
    .stButton > button:hover {
        border-color: #818cf8;
        background: rgba(129, 140, 248, 0.12);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(129, 140, 248, 0.2);
    }
    .status-badge {
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 15px;
        display: inline-block;
    }
    .status-badge.unannotated {
        background-color: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    .status-badge.annotated {
        background-color: rgba(74, 222, 128, 0.1);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.2);
    }
    /* Gros boutons ESG / NON_ESG */
    div[data-testid="column"]:nth-child(2) .stButton > button:first-child {
        background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.08));
        border-color: rgba(74, 222, 128, 0.3);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🔍 Annotation CNN — Filtre ESG</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Classez chaque page : <strong>ESG</strong> (pertinente) ou <strong>NON_ESG</strong> (à ignorer).</p>', unsafe_allow_html=True)

images_dir = PROCESSED_DIR / "images"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(s))]

all_images = []
if images_dir.exists():
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        all_images.extend(list(images_dir.glob(ext)))

# Tri naturel pour grouper par rapport et garder l'ordre des pages
all_images.sort(key=natural_sort_key)

# Récupérer l'état actuel des annotations {nom_fichier: classe}
already_annotated = {}
for cls in CNN_CLASSES:
    cls_dir = CNN_DATASET_DIR / cls
    if cls_dir.exists():
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            for p in cls_dir.glob(ext):
                already_annotated[p.name] = cls

total_images = len(all_images)
total_annotated = len(already_annotated)
total_remaining = total_images - total_annotated

# Initialisation intelligente : focus sur la première image non annotée
if "cnn_index" not in st.session_state:
    first_unannotated_idx = 0
    for idx, img in enumerate(all_images):
        if img.name not in already_annotated:
            first_unannotated_idx = idx
            break
    st.session_state.cnn_index = first_unannotated_idx

# Sécurité bornes
if total_images > 0:
    st.session_state.cnn_index = max(0, min(st.session_state.cnn_index, total_images - 1))

with st.sidebar:
    st.markdown("### 📊 Progression")
    if total_images > 0:
        progress = total_annotated / total_images
        st.progress(progress)

    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Total", total_images)
        st.metric("Annotées", total_annotated)
    with col_stat2:
        st.metric("Restantes", total_remaining)
        st.metric("Ratio", f"{progress:.1%}" if total_images > 0 else "0%")

    st.markdown("---")

    if total_remaining > 0:
        if st.button("🔍 Aller au 1er non annoté"):
            for idx, img in enumerate(all_images):
                if img.name not in already_annotated:
                    st.session_state.cnn_index = idx
                    break
            st.rerun()

    st.markdown("---")
    st.markdown("### 📁 Répartition")
    for cls in CNN_CLASSES:
        cls_dir = CNN_DATASET_DIR / cls
        count = len(list(cls_dir.glob("*.*"))) if cls_dir.exists() else 0
        emoji = "✅" if cls == "ESG" else "❌"
        st.write(f"{emoji} **{cls}** : {count} images")

    st.markdown("---")

    # Bouton de réinitialisation sécurisé
    if total_annotated > 0:
        st.markdown("### ⚠️ Zone de Danger")
        if "confirm_reset" not in st.session_state:
            st.session_state.confirm_reset = False

        if not st.session_state.confirm_reset:
            if st.button("🚨 Réinitialiser tout", key="btn_reset_all"):
                st.session_state.confirm_reset = True
                st.rerun()
        else:
            st.warning("⚠️ Confirmer la suppression de TOUTES les annotations ?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Oui, effacer", key="btn_confirm_yes"):
                    for cls in CNN_CLASSES:
                        cls_dir = CNN_DATASET_DIR / cls
                        if cls_dir.exists():
                            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                                for p in cls_dir.glob(ext):
                                    p.unlink()
                    st.session_state.cnn_index = 0
                    st.session_state.confirm_reset = False
                    st.rerun()
            with col_no:
                if st.button("Annuler", key="btn_confirm_no"):
                    st.session_state.confirm_reset = False
                    st.rerun()

if total_images == 0:
    st.info("Aucune image trouvée. Veuillez extraire les pages PDF dans 'data/processed/images'.")
else:
    idx = st.session_state.cnn_index
    current_image = all_images[idx]
    current_class = already_annotated.get(current_image.name)

    st.markdown(f"#### Image **{idx + 1}** sur **{total_images}** — `{current_image.name}`")

    if current_class:
        st.markdown(f'<div class="status-badge annotated">✅ Classé : <strong>{current_class}</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge unannotated">ℹ️ En attente de classification</div>', unsafe_allow_html=True)

    col_img, col_btn = st.columns([3, 1])

    with col_img:
        st.image(str(current_image), use_container_width=True)

    with col_btn:
        st.markdown("### Classification")

        # Bouton ESG (vert)
        if st.button("✅ ESG (pertinent)", key="btn_ESG"):
            for other_cls in CNN_CLASSES:
                other_path = CNN_DATASET_DIR / other_cls / current_image.name
                if other_path.exists():
                    other_path.unlink()
            dest_dir = CNN_DATASET_DIR / "ESG"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(current_image), str(dest_dir / current_image.name))
            if st.session_state.cnn_index < total_images - 1:
                st.session_state.cnn_index += 1
            st.rerun()

        # Bouton NON_ESG (rouge)
        if st.button("❌ NON_ESG (ignorer)", key="btn_NON_ESG"):
            for other_cls in CNN_CLASSES:
                other_path = CNN_DATASET_DIR / other_cls / current_image.name
                if other_path.exists():
                    other_path.unlink()
            dest_dir = CNN_DATASET_DIR / "NON_ESG"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(current_image), str(dest_dir / current_image.name))
            if st.session_state.cnn_index < total_images - 1:
                st.session_state.cnn_index += 1
            st.rerun()

        st.markdown("---")

        # Contrôles de navigation
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("⬅️ Préc.", disabled=(idx == 0)):
                st.session_state.cnn_index -= 1
                st.rerun()
        with col_next:
            if st.button("Suiv. ➡️", disabled=(idx == total_images - 1)):
                st.session_state.cnn_index += 1
                st.rerun()
