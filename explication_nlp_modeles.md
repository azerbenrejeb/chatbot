# Compte-Rendu Pédagogique — Suite NLP (Classification ESG & Extraction NER)

Ce document explique le fonctionnement, le pourquoi, le comment et les outils utilisés pour le **Module 2 (NLP)** du projet de Chatbot Intelligent d'analyse de rapports RSE.

---

## 1. Contexte & Rôle dans le Pipeline

Le **Module 2** intervient juste après l'extraction visuelle et textuelle des pages filtrées par le CNN. Son rôle est de donner un sens thématique et d'extraire les informations quantitatives clés contenues dans chaque paragraphe :
1. **Classification ESG** : Déterminer si le paragraphe parle d'**Environnemental**, de **Social**, ou de **Gouvernance** (E/S/G).
2. **Reconnaissance d'Entités Nommées (NER)** : Extraire automatiquement les indicateurs chiffrés (`VALEUR`), les mesures (`UNITE`), les dates (`ANNEE`), les variations de tendance (`TENDANCE`) et les normes (`REFERENCE_GRI`).

---

## 2. Classification ESG (Multiclasse) — Comparaison des 3 Modèles

Pour concevoir une architecture robuste et professionnelle, nous avons implémenté et entraîné **3 modèles de classification** différents, allant du plus simple et rapide au plus complexe.

### A. Baseline TF-IDF + Régression Logistique (`ml1_baseline_tfidf.py`)
* **Outils** : Scikit-Learn (`TfidfVectorizer`, `LogisticRegression`).
* **Pourquoi** : En apprentissage automatique, il est indispensable de définir une **ligne de référence (Baseline)** simple. La régression logistique est très légère, rapide (inférieure à 1 seconde d'entraînement) et fournit d'excellents scores sur les textes courts.
* **Comment** : 
  - **TF-IDF** (Term Frequency-Inverse Document Frequency) calcule un score d'importance pour chaque mot-clé. Un mot très fréquent dans un paragraphe mais rare dans le reste du rapport (comme *"scope 3"*) aura un score TF-IDF très élevé.
  - La **Régression Logistique** trace une frontière de décision linéaire entre les classes dans l'espace vectoriel des mots.
* **Résultat obtenu** : **88,98 % d'accuracy** en validation !

### B. Random Forest - Forêt Aléatoire (`ml1_random_forest.py`)
* **Outils** : Scikit-Learn (`RandomForestClassifier`).
* **Pourquoi** : Un classifieur non-linéaire d'ensemble. Il réduit le risque de surapprentissage en combinant les prédictions de plusieurs arbres de décision indépendants.
* **Comment** : 
  - Entraîne 150 arbres de décision en parallèle sur des sous-ensembles aléatoires des données (bagging) et des caractéristiques (mots-clés).
  - La décision finale est prise par vote majoritaire de l'ensemble des arbres.
* **Résultat obtenu** : **91,05 % d'accuracy** en validation ! (Notre meilleur modèle rapide).

### C. Deep Learning CamemBERT (`ml1_camembert.py`)
* **Outils** : PyTorch + HuggingFace (`transformers`).
* **Pourquoi** : Modèle de langage état de l'art basé sur l'architecture **Transformer** pré-entraîné spécifiquement sur le français. Contrairement à TF-IDF, il comprend le contexte d'un mot (la polysémie) et l'ordre des mots grâce au mécanisme d'**attention bidirectionnelle**.
* **Comment** : 
  - Les paragraphes sont découpés en sous-mots (SentencePiece).
  - Nous fine-tunons (ajustons les poids) de la tête de classification linéaire de CamemBERT avec PyTorch et un optimiseur AdamW sur notre dataset.

---

## 3. Reconnaissance d'Entités Nommées (NER)

Le NER permet d'isoler les données précieuses au sein d'une phrase. Nous avons implémenté **2 approches** pour ce composant :

### A. Générateur Automatique de Dataset IOB2 (`tools/prepare_ner_annotations.py`)
* **Pourquoi** : Pour entraîner un extracteur NER supervisé, il est nécessaire de posséder un jeu de données étiqueté au format **IOB2** (Inside-Outside-Beginning).
* **Comment** : 
  - Nous avons conçu un script qui découpe automatiquement les paragraphes de `ml_dataset.csv` en phrases et en tokens (mots).
  - Un moteur de règles et de regex précises étiquette automatiquement chaque token avec les labels de pilier RSE :
    - `B-ANNEE` : Années (2020-2030).
    - `B-VALEUR` : Chiffres de performances (ex: 45 200, 32%, -8).
    - `B-UNITE` : Unités de performance (ex: tCO2e, salariés, %, MW).
    - `B-TENDANCE` : Mots-clés de variation (baisse, augmentation, stable).
    - `B-REFERENCE_GRI` : Normes GRI (GRI 305, 401-1).
  - **Résultat** : Un dataset massif de **3 888 phrases propres** et **40 739 étiquettes d'entités** généré dans `data/ml_dataset/ner/ner_dataset.txt`.

### B. spaCy Custom NER (`ml2_ner_spacy.py`)
* **Outils** : spaCy (Framework NLP de qualité industrielle).
* **Pourquoi** : spaCy est réputé pour sa rapidité d'exécution phénoménale en production (inférence en quelques millisecondes sur CPU), ce qui le rend idéal pour notre pipeline local.
* **Comment** : 
  - Nous convertissons les phrases IOB2 de `ner_dataset.txt` au format de spaCy (offsets de caractères).
  - Nous créons un pipeline vierge en français (`spacy.blank("fr")`) et l'entraînons avec les exemples d'apprentissage pour optimiser les frontières d'entités par descente de gradient.

### C. CamemBERT Token Classification (`ner_camembert.py`)
* **Pourquoi** : Le modèle le plus puissant pour le NER contextuel. Il utilise le même tokenizer et la même base d'attention bidirectionnelle que pour la classification mais classifie chaque token individuellement.

---

## 4. Stratégie de Validation & Rigueur Technique

* **Découpage Stratifié** : Pour tous les modèles de classification, nous effectuons un découpage de validation stratifié (70 % Train, 15 % Validation, 15 % Test) pour garantir que les proportions de E, S et G restent rigoureusement identiques et éviter toute sur-représentation.
* **Zéro Bruit** : Les rapports non-ESG et les fichiers corrompus ont été systématiquement filtrés en amont pour éviter de polluer les poids des modèles.
