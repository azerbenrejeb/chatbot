# ============================================================
# CHATBOT INTELLIGENT D'ANALYSE DE RAPPORTS RSE
# ============================================================
# Projet PFE 2025/2026 — Azer Ben Rejeb — RSE Time
# Machine Learning • Deep Learning CNN • LLM • RAG • Chatbot ESG
# ============================================================

## 📋 Description

Système intelligent en **4 modules IA** qui analyse des rapports RSE (PDF)
et permet de les interroger en langage naturel via un chatbot.

```
PDF uploadé → CNN → ML → LLM + RAG → Chatbot
```

## 🏗️ Architecture

| Module | Technologie | Rôle |
|--------|-------------|------|
| Module 1 — CNN | ResNet-50 (PyTorch) | Classification visuelle des pages ESG |
| Module 2 — NLP | CamemBERT + spaCy | Classification thématique + extraction NER |
| Module 3 — LLM+RAG | Mistral 7B + ChromaDB | Réponses intelligentes basées sur le rapport |
| Module 4 — Chatbot | Streamlit | Interface de chat conversationnelle |

## 🚀 Installation

### 1. Prérequis
- Python 3.11+
- Poppler (pour pdf2image) : https://github.com/oschwartz10612/poppler-windows
- Ollama (pour Mistral 7B) : https://ollama.ai

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
ollama pull mistral
```

### 3. Initialiser le projet
```bash
python app/config.py
```

## 📖 Guide d'utilisation pas à pas

### Étape 1 : Extraire le texte des PDF
```bash
python extraction/pdf_extractor.py
```

### Étape 2 : Convertir les PDF en images (pour le CNN)
```bash
python extraction/pdf_to_images.py
```

### Étape 3 : Annoter les données
```bash
# Annotation CNN (images → catégories)
streamlit run tools/annotate_cnn.py

# Annotation ML (texte → classes GRI)
streamlit run tools/annotate_ml.py

# Annotation NER (phrases → entités)
streamlit run tools/annotate_ner.py
```

### Étape 4 : Entraîner les modèles
```bash
# Entraîner le CNN
python -m modules.module1_cnn.train_cnn

# Entraîner les modèles ML (compare 3 modèles)
python -m modules.module2_nlp.train_ml
```

### Étape 5 : Lancer le chatbot
```bash
streamlit run modules/module4_chatbot/chatbot_app.py
```

### Étape 6 : Générer les rapports d'évaluation
```bash
python -m modules.module1_cnn.rapport_cnn
python -m modules.module2_nlp.rapport_ml
python -m modules.module3_llm_rag.rapport_rag
```

## 📊 Objectifs de performance

| Module | Métrique | Objectif |
|--------|----------|----------|
| CNN ResNet-50 | Accuracy | ≥ 85% |
| CamemBERT | F1-score macro | ≥ 75% |
| NER spaCy | F1 VALEUR | ≥ 80% |
| RAG | Pertinence | ≥ 80% |

## 📁 Structure du projet

```
chatbot/
├── app/                    # Configuration et base de données
├── extraction/             # Extraction PDF (texte + images)
├── modules/
│   ├── module1_cnn/        # Classification CNN ResNet-50
│   ├── module2_nlp/        # CamemBERT + NER spaCy
│   ├── module3_llm_rag/    # Mistral 7B + ChromaDB + RAG
│   └── module4_chatbot/    # Interface Streamlit
├── tools/                  # Outils d'annotation
├── graphiques/             # Graphiques générés (PNG)
├── rapports/               # Rapports d'évaluation (PDF)
├── data/                   # Données (PDF, datasets)
├── models/                 # Modèles entraînés
└── tests/                  # Tests unitaires
```

## 👤 Auteur
**Azer Ben Rejeb** — PFE 2025/2026 — RSE Time, Tunisie
