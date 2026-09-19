# 🏷️ Explication Technique — Préparation et Annotation des Données ML (Module 2)

Ce document explique le **pourquoi**, le **comment** et les **outils** utilisés pour segmenter, nettoyer et annoter automatiquement le dataset d'entraînement en vue de la classification thématique (Environnemental / Social / Gouvernance) par un modèle comme CamemBERT.

---

## 1. Pourquoi ? (Objectif du Pipeline ML)

Une fois que les pages pertinentes ont été isolées par le CNN, l'étape suivante consiste à structurer et catégoriser le texte extrait pour que le chatbot puisse faire des recherches sémantiques précises. 
Cependant, les pages de rapports bruts contiennent souvent des pavés textuels de taille variable mélangeant parfois plusieurs thématiques. 

### Les Objectifs du Traitement ML :
1. **Création d'unités de texte homogènes** : Découper le document en paragraphes ou en groupes de phrases cohérents. Si un paragraphe est trop long, il risque de diluer l'information et de mélanger E, S et G.
2. **Filtrage du bruit non-ESG restant** : Écarter les documents ou les pages génériques (ex. pages de sommaire, copyright, world stats pocketbooks) qui n'apportent aucun contenu ESG.
3. **Annotation de haute qualité pour l'entraînement** : Automatiser l'étiquetage en classes (Environnemental, Social, Gouvernance) via des heuristiques de mots-clés strictes pour fournir un jeu d'entraînement propre et qualitatif à notre classifieur textuel CamemBERT.

---

## 2. Quels Outils ?

Ce module utilise un ensemble d'outils complémentaires :
* **PyMuPDF (`fitz`)** : Permet une extraction extrêmement rapide de l'intégralité du texte par page à partir des fichiers PDF sources (`tools/extract_pdfs_to_json.py`).
* **Python RegEx (`re`)** : Utilisé pour la normalisation textuelle (suppression des accents, suppression des espaces superflus, réparation du mojibake suite à de mauvaises lectures UTF-8).
* **Segmenter de paragraphes (`text_preprocessor.py`)** : Un module interne qui découpe le texte en blocs selon les retours à la ligne tout en fixant une longueur minimale (ex: 80 caractères) pour éliminer les résidus de mise en page.
* **Pandas (`pd`)** : Utilisé pour manipuler la table d'annotations, vérifier les valeurs manquantes, appliquer la déduplication et sauvegarder au format CSV.
* **Streamlit (`tools/annotate_ml.py`)** : Interface interactive permettant à l'utilisateur de réviser manuellement, modifier, supprimer ou ajouter de nouvelles annotations de paragraphes.

---

## 3. Comment ? (Algorithmes et Logique de Nettoyage)

Le pipeline d'annotation automatique (`tools/prepare_ml_annotations.py`) applique les étapes suivantes :

### A. Filtrage des Documents (Exclusion de bruit)
1. **Filtre par nom de fichier** : Les fichiers contenant des indices comme `world-stats`, `pocketbook` ou `table03` sont identifiés comme non-ESG et immédiatement exclus.
2. **Filtre par score d'introduction** : Pour chaque rapport, le script analyse les 20 premières pages. Si moins de 2 mots-clés ESG généraux (comme *esg, rse, durabilité, extra-financier*) sont détectés, le rapport complet est écarté.

### B. Découpage Intelligent en Paragraphes
Les pages retenues sont segmentées. Si un paragraphe brut extrait dépasse 900 caractères, il est découpé dynamiquement en sous-blocs de phrases pour garantir que chaque unité de texte cible un seul sujet (E, S ou G).

### C. Annotation par Heuristiques et Mots-Clés
Chaque paragraphe reçoit un score pour chaque pilier ESG en comptant la présence de mots-clés spécialisés :
* **Environnemental** : *co2, carbone, climat, ges, émissions, énergie, biodiversité, eau, déchets, etc.*
* **Social** : *salarié, formation, santé, sécurité, accident, parité, inclusion, droits humains, etc.*
* **Gouvernance** : *gouvernance, conseil d'administration, éthique, corruption, conformité, risques, actionnaire, etc.*

**Règle de décision stricte** :
* Le paragraphe reçoit l'étiquette de la catégorie ayant le plus haut score.
* **Gestion de l'ambiguïté** : Si le score le plus haut est inférieur à un seuil (`min_score=2`) ou s'il y a égalité parfaite entre deux catégories, le paragraphe est **rejeté**. Cela évite d'introduire des données confuses dans le jeu d'entraînement.

### D. Déduplication Finale
Après génération automatique, le script élimine les doublons exacts sur le texte (provenant de pieds de page répétés ou de formules récurrentes) à l'aide de la méthode `drop_duplicates` de Pandas, garantissant un dataset `ml_dataset.csv` de 3872 lignes saines et uniques.
