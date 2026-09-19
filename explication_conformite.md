# Explication du Module de Conformité ESG Multi-Standards (GRI & ESRS / CSRD)

Ce document explique le fonctionnement, la méthodologie et les choix d'implémentation du **Module de Conformité ESG Multi-Standards**.

---

## 1. Contexte réglementaire : GRI vs ESRS (CSRD)

Dans le cadre de l'évaluation extra-financière des entreprises (RSE), deux référentiels mondiaux majeurs s'appliquent aujourd'hui :
- **GRI Standards 2021 (Global Reporting Initiative)** : Un standard international de référence, utilisé volontairement par des milliers d'entreprises pour rapporter leurs impacts économiques, environnementaux et sociaux.
- **ESRS (European Sustainability Reporting Standards)** : Les nouvelles normes européennes obligatoires dans le cadre de la directive **CSRD (Corporate Sustainability Reporting Directive)**. Tout rapport publié par les grandes entreprises européennes doit s'aligner sur ces standards.

La capacité de comparer et mesurer en parallèle la conformité d'un rapport à ces deux référentiels est donc un enjeu critique pour les directions RSE.

---

## 2. Méthodologie d'extraction et normalisation

Le module fonctionne en 4 étapes majeures :

### Étape A : Extraction des entités par le NER customisé
Le modèle de reconnaissance d'entités nommées (**spaCy NER**) est préalablement entraîné pour détecter des entités de type `REFERENCE_GRI` dans le texte des rapports. Ces entités incluent :
- Les codes GRI standards (ex: `GRI 305`, `GRI 302-1`, `303-3`).
- Les codes ESRS correspondants (ex: `E1-5`, `E1-6`, `S1-14`).

Ces références extraites lors de la phase d'upload sont automatiquement stockées dans la table relationnelle SQLite `indicateurs_esg`.

### Étape B : Auto-correction (Self-Healing)
Si l'application interroge la conformité d'un rapport déjà existant pour lequel aucun indicateur n'a été préalablement stocké, le module s'auto-corrige à la volée :
1. Il lit le fichier JSON de texte extrait correspondant au rapport.
2. Il exécute l'inférence du modèle spaCy NER pour extraire les entités.
3. Il les persiste en base de données SQLite pour les prochaines requêtes.

### Étape C : Normalisation robuste par Regex
Avant toute comparaison sémantique, chaque code brut extrait est nettoyé et normalisé par notre parser regex (`normaliser_reference`) :
- **GRI** : Uniformise les casses et supprime les suffixes de sous-indicateurs.
  - Exemples : `GRI 305-1` ➔ `GRI 305` | `gri302` ➔ `GRI 302` | `303` ➔ `GRI 303`.
- **ESRS** : Uniformise la casse en préservant le tiret.
  - Exemples : `e1-5` ➔ `E1-5` | `S1-13` ➔ `S1-13`.

---

## 3. Algorithme de calcul des scores

Les indicateurs requis sont répartis selon les 3 dimensions de l'ESG :
- **🌿 Environnemental** (Énergie, Eau, Émissions, Déchets)
- **👥 Social** (Emploi, Santé & Sécurité, Formation, Diversité)
- **⚖️ Gouvernance** (Anti-corruption, Concurrence déloyale, Politiques publiques/Lobbying, Conformité réglementaire)

Pour chaque dimension :
- Le score **GRI** est égal au ratio : $\frac{\text{Indicateurs GRI trouvés}}{\text{Indicateurs GRI requis}} \times 100$
- Le score **ESRS** est égal au ratio : $\frac{\text{Indicateurs ESRS trouvés}}{\text{Indicateurs ESRS requis}} \times 100$
  *(Pour l'ESRS, si le code ESRS direct ou son équivalent GRI mappé est présent, l'indicateur est validé).*

Les **scores globaux** sont calculés en faisant la moyenne arithmétique simple des 3 scores de dimensions pour chaque standard. Le **score combiné** est la moyenne des deux scores globaux.

---

## 4. Stratégie d'intégration RAG & LLM (Mistral 7B)

Lorsqu'une question sur la conformité est posée au chatbot (détectée via des mots-clés comme `conforme`, `manquant`, `GRI`, `ESRS`, `CSRD`), le pipeline s'adapte automatiquement :

1. Au lieu d'effectuer une simple recherche vectorielle de passages textuels, le système calcule le rapport de conformité du PDF actif et le formate sous forme de synthèse textuelle structurée.
2. Si l'utilisateur pose une question ciblée sur un standard (ex: *"Quels indicateurs ESRS manquent ?"*), une consigne de focus est ajoutée pour forcer le LLM à mettre l'accent sur ce standard précis.
3. Le résumé de conformité et les instructions sont injectés dans un prompt système adapté aux standards ESG pour Mistral.
4. Mistral génère une réponse factuelle, structurée, listant les scores et les indicateurs présents ou manquants, garantissant **zéro hallucination** car reposant sur les calculs déterministes du code Python.
