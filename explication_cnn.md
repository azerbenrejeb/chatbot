# 📊 Explication Technique — Classification et Filtrage des Pages par CNN (Module 1)

Ce document explique le **pourquoi**, le **comment** et les **outils** utilisés pour la classification automatique des pages de rapports (ESG vs NON_ESG) à l'aide d'un réseau de neurones convolutif (CNN).

---

## 1. Pourquoi ? (Le Rôle du CNN dans le Pipeline)

Les rapports de responsabilité sociétale des entreprises (RSE/ESG) ou les rapports annuels intégrés sont des documents extrêmement volumineux (souvent de 100 à 500 pages). Cependant, toutes les pages ne contiennent pas de données pertinentes pour l'analyse ESG :
* **Pages NON_ESG (Bruit)** : Couvertures, sommaires, index, intercalaires vierges, pages purement financières (bilans, comptes de résultat), ou publicités de l'entreprise.
* **Pages ESG (Pertinentes)** : Tableaux de bord de performance environnementale, indicateurs sociaux (parité, accidents de travail), rapports de gouvernance et chartes éthiques.

### Les Avantages du Filtrage en Amont :
1. **Économie de ressources et rapidité** : L'extraction textuelle fine (pdfplumber) et surtout les modèles NLP lourds (CamemBERT, LLM) sont très gourmands en temps de calcul et en mémoire. Filtrer les pages inutiles permet de réduire le volume de texte à traiter de **40% à 70%**.
2. **Qualité du RAG (Retrieval-Augmented Generation)** : Éviter de stocker du texte inutile (ex. mentions légales, sommaires) dans la base de données vectorielle ChromaDB, ce qui évite au chatbot de récupérer des informations hors-sujet pour répondre aux questions.

---

## 2. Quels Outils ?

Le module repose sur plusieurs outils et bibliothèques Python standards de l'intelligence artificielle :
* **PyTorch (`torch`)** : Le framework de Deep Learning utilisé pour définir les architectures, calculer les gradients et entraîner le modèle.
* **Torchvision** : Fournit des transformations d'images standardisées (normalisation, redimensionnement) et des modèles de vision par ordinateur pré-entraînés comme ResNet-50.
* **PyMuPDF (`fitz`)** : Utilisé dans `extraction/pdf_to_images.py` pour convertir instantanément chaque page de chaque PDF en image JPEG haute résolution (120 DPI) pour alimenter le CNN.
* **Scikit-Learn (`train_test_split`)** : Permet de diviser notre jeu d'images en ensembles d'entraînement (Train), validation (Val) et test (Test) de manière stratifiée.
* **Pillow (`PIL`)** : Utilisé pour lire, convertir en RGB et manipuler les fichiers images JPEG avant leur passage dans le tenseur PyTorch.
* **ReportLab** : Utilisé pour compiler automatiquement les résultats d'évaluation du modèle et en faire un rapport PDF professionnel (`data/rapports_generes/Rapport_Evaluation_CNN.pdf`).

---

## 3. Comment ? (Fonctionnement du Code)

### A. Les Deux Architectures Proposées
Le fichier `cnn_classifier.py` propose deux options d'architecture :
1. **`ESG_CNN_Light` (Activé par défaut)** : Un CNN sur-mesure léger composé de 3 blocs convolutifs successifs. Il extrait les caractéristiques spatiales de la page à moindre coût. Il est idéal pour s'entraîner rapidement sur un ordinateur dépourvu de carte graphique (CPU).
2. **`ESG_CNN` (ResNet-50)** : Un réseau très profond (50 couches de neurones résiduelles) pré-entraîné sur plus d'un million d'images d'ImageNet. Nous utilisons le **Transfer Learning** : nous figeons les couches de détection de formes existantes (backbone) et remplaçons uniquement la couche finale (Fully Connected) par un classifieur binaire pour l'adapter à notre tâche.

### B. Le Pipeline d'Entraînement et de Validation
1. **Chargement et Augmentation de données (`dataset_builder.py`)** :
   - Les images d'entraînement subissent des transformations aléatoires (Data Augmentation) : retournements horizontaux aléatoires, variations de luminosité et de contraste. Cela apprend au modèle à reconnaître la mise en page même si l'image est légèrement inclinée ou colorée différemment.
   - Les images sont normalisées avec la moyenne et l'écart-type standards d'ImageNet pour stabiliser le réseau.
2. **Pondération des classes (`_build_class_weights` dans `train_cnn.py`)** :
   - Les rapports comportant souvent plus de pages non pertinentes que de pages ESG, le jeu de données peut être déséquilibré.
   - Nous calculons des poids inverses aux fréquences des classes. Ainsi, commettre une erreur sur la classe minoritaire pénalise plus lourdement le modèle lors du calcul de la perte (`CrossEntropyLoss`), ce qui évite au modèle d'avoir un biais de prédiction.
3. **Apprentissage et Sauvegarde Anticipée** :
   - À chaque époque, l'optimiseur **Adam** ajuste les poids du réseau par descente de gradient.
   - Nous évaluons les performances sur l'ensemble de Validation. Si la perte (`val_loss`) diminue, le modèle est sauvegardé dans `models/cnn_resnet50_esg.pth`. Si le modèle commence à surapprendre (overfitting), sa perte en validation remontera, et cette sauvegarde dynamique nous garantit de conserver uniquement la version qui généralise le mieux.
