# Compte-Rendu Pédagogique — Module 3 (RAG : ChromaDB + Mistral 7B) et Module 4 (Chatbot Streamlit)

Ce document explique le fonctionnement, le pourquoi et le comment des Modules 3 et 4 du pipeline de Chatbot ESG Intelligent.

---

## 1. Module 3 — RAG (Retrieval-Augmented Generation)

### Qu'est-ce que le RAG ?
Le RAG est une technique qui combine **recherche sémantique** (Retrieval) et **génération de texte** (Generation) pour produire des réponses précises et sourcées à partir d'une base de connaissances.

Le pipeline fonctionne en 3 étapes :
1. **STOCKER** : Les paragraphes des rapports ESG sont convertis en vecteurs numériques (embeddings) et indexés dans ChromaDB.
2. **CHERCHER** : Quand l'utilisateur pose une question, elle est aussi convertie en vecteur. ChromaDB retrouve les passages les plus proches sémantiquement (cosinus similaire).
3. **GÉNÉRER** : Les passages trouvés sont envoyés comme contexte à Mistral 7B qui formule une réponse naturelle en français, strictement sourcée.

### Outils Utilisés

| Composant | Outil | Rôle |
|---|---|---|
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Convertit le texte en vecteurs de 384 dimensions. Modèle multilingue couvrant 50+ langues dont le français. |
| Base Vectorielle | ChromaDB (PersistentClient) | Stockage persistant local des vecteurs. Recherche par similarité cosinus ultra-rapide. |
| LLM | Mistral 7B via Ollama | Génération de réponses en français basées exclusivement sur le contexte fourni. |
| Anti-hallucination | Prompt système strict | Instructions interdisant l'invention de chiffres et exigeant la citation des sources. |

### Pourquoi ce choix d'architecture ?
- **ChromaDB local** : Aucune donnée ESG sensible n'est envoyée à un serveur externe. La confidentialité est garantie.
- **Mistral 7B local** : Le LLM tourne sur la machine de l'utilisateur via Ollama. Aucune connexion Internet requise pour la génération.
- **Embeddings multilingues** : Le modèle `MiniLM-L12-v2` est léger (~130 Mo) et gère nativement le français, contrairement aux modèles anglais-only comme SBERT.

### Pipeline d'Indexation (`tools/index_extracted_json_to_chroma.py`)
1. Charge tous les fichiers `*_extracted.json` de `data/processed/`.
2. Découpe chaque page en blocs de texte (80-900 caractères) pour une granularité optimale.
3. Classifie chaque bloc en E/S/G/Général/Autre avec les heuristiques de mots-clés.
4. Indexe dans ChromaDB avec des métadonnées (rapport, page, label) pour le filtrage.
5. Utilise `upsert` pour éviter les doublons d'indexation.

---

## 2. Module 4 — Interface Chatbot Streamlit

### Architecture de l'Interface
L'interface Streamlit (`chatbot_app.py`) est composée de :
- **Barre latérale** : Upload de rapport PDF, filtrage par domaine ESG, statistiques de la base.
- **Zone de chat** : Interface de conversation avec historique des messages et affichage des sources citées.
- **Styles CSS premium** : Design sombre avec gradients, glassmorphism et animations.

### Composants Auxiliaires

| Fichier | Rôle |
|---|---|
| `session_manager.py` | Gestion de l'état `st.session_state` (historique, rapport actif, filtres). |
| `chat_memory.py` | Mémoire conversationnelle basée sur SQLite pour persister les échanges. |
| `pdf_uploader.py` | Validation, sauvegarde locale et envoi du PDF au backend FastAPI. |
| `export_pdf.py` | Export de la conversation en fichier PDF professionnel (ReportLab). |

### Flux de Données Complet
```
Utilisateur upload un PDF
    ↓
pdf_uploader.py valide et envoie au backend
    ↓
FastAPI (app/main.py) orchestre le pipeline :
    CNN filtre → pdfplumber extrait → CamemBERT classifie → ChromaDB indexe
    ↓
Utilisateur pose une question
    ↓
FastAPI : ChromaDB cherche → Mistral 7B génère → réponse + sources
    ↓
chatbot_app.py affiche la réponse avec les sources citées
```

---

## 3. Base de Données SQLite (`app/database.py`)
- Stocke l'historique de toutes les conversations du chatbot.
- Deux tables : `sessions` (métadonnées) et `messages` (contenu des échanges).
- Permet de reprendre une conversation précédente ou d'exporter l'historique.
