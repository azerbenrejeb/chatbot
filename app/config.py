# ============================================================
# CONFIGURATION GLOBALE DU PROJET — CHATBOT ESG
# Nouveau CDC — Pipeline: CNN → Extraction → CamemBERT → NER → ChromaDB → Mistral
# ============================================================
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# CHEMINS DU PROJET
# ============================================================
RAW_PDF_DIR = BASE_DIR / "rapport_non _annoteé"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CNN_DATASET_DIR = BASE_DIR / "data" / "cnn_dataset"
ML_DATASET_DIR = BASE_DIR / "data" / "ml_dataset"
NER_DATASET_DIR = BASE_DIR / "data" / "ml_dataset" / "ner"
MODELS_DIR = BASE_DIR / "models"
GRAPHIQUES_DIR = BASE_DIR / "graphiques"
RAPPORTS_DIR = BASE_DIR / "data" / "rapports_generes"
CHROMA_DB_DIR = BASE_DIR / "models" / "chroma_db"

# ============================================================
# MODULE 1 — CNN (Filtre ESG / NON_ESG)
# ============================================================
CNN_IMAGE_SIZE = 224
CNN_BATCH_SIZE = 32
CNN_EPOCHS = 10
CNN_LEARNING_RATE = 1e-3
CNN_EARLY_STOPPING_PATIENCE = 5
CNN_TRAIN_SPLIT = 0.70
CNN_VAL_SPLIT = 0.15
CNN_TEST_SPLIT = 0.15

# 2 classes binaires : pages pertinentes ESG vs pages non pertinentes
CNN_CLASSES = [
    "ESG",
    "NON_ESG"
]

# ============================================================
# MODULE 2 — EXTRACTION DE TEXTE
# ============================================================
PDF_DPI = 120
MIN_TEXT_LENGTH = 50  # Ignorer les pages avec moins de 50 caractères
MIN_PARAGRAPH_LENGTH = 50  # Longueur minimale d'un paragraphe

# ============================================================
# MODULE 3 — CLASSIFICATION ML (CamemBERT)
# ============================================================
ML_CLASSES = ["Environnemental", "Social", "Gouvernance"]
ML_MODEL_NAME = "camembert-base"
ML_BATCH_SIZE = 16
ML_EPOCHS = 10
ML_LEARNING_RATE = 2e-5
ML_MAX_LENGTH = 512

# ============================================================
# MODULE 4 — NER (CamemBERT Token Classification)
# ============================================================
NER_LABELS = ["O", "B-VALEUR", "B-UNITE", "B-ANNEE", "B-TENDANCE", "B-REFERENCE_GRI"]
NER_MODEL_NAME = "camembert-base"
NER_BATCH_SIZE = 16
NER_EPOCHS = 10
NER_LEARNING_RATE = 2e-5
NER_MAX_LENGTH = 512

# ============================================================
# MODULE 5 — CHROMADB (RAG)
# ============================================================
CHROMA_COLLECTION_NAME = "esg_rapports"
# Modele multilingue plus leger et deja compatible avec le cache local.
# Il couvre bien le francais pour le RAG et evite les erreurs de chargement du modele mpnet.
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SEARCH_N_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7

# ============================================================
# MODULE 6 — MISTRAL 7B (Ollama)
# ============================================================
OLLAMA_MODEL = "mistral"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ============================================================
# BACKEND — FASTAPI
# ============================================================
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000

# ============================================================
# INITIALISATION DES DOSSIERS
# ============================================================
def create_directories():
    directories = [
        RAW_PDF_DIR,
        PROCESSED_DIR,
        PROCESSED_DIR / "images",
        CNN_DATASET_DIR,
        ML_DATASET_DIR / "classification",
        ML_DATASET_DIR / "ner",
        MODELS_DIR,
        GRAPHIQUES_DIR,
        RAPPORTS_DIR,
        CHROMA_DB_DIR,
    ]
    for classe in CNN_CLASSES:
        directories.append(CNN_DATASET_DIR / classe)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    print(f"[OK] {len(directories)} dossiers verifies/crees")

if __name__ == "__main__":
    create_directories()
    print(f"[DIR] Projet initialise dans : {BASE_DIR}")
