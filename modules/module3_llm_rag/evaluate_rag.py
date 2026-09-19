"""
MODULE 5 & 6 — Évaluation automatique du pipeline RAG (Retrieval-Augmented Generation).
Mesure la qualité de la recherche sémantique dans ChromaDB et la pertinence
des résultats retournés pour un ensemble de questions ESG types.

Métriques calculées :
- Taux de réponse : % de questions pour lesquelles ChromaDB retourne au moins un résultat.
- Score de pertinence moyen : Distance cosinus moyenne des résultats (plus bas = plus pertinent).
- Nombre moyen de sources par question.
- Couverture thématique : Répartition E/S/G des résultats.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from modules.module3_llm_rag.vector_store import rechercher, formater_contexte, get_stats


# Questions de test couvrant les 3 piliers ESG
QUESTIONS_TEST = [
    # Environnemental
    "Quelles sont les émissions de CO2 du groupe ?",
    "Quelle est la consommation d'énergie renouvelable ?",
    "Comment l'entreprise gère-t-elle ses déchets ?",
    "Quels sont les objectifs de réduction des gaz à effet de serre ?",
    # Social
    "Combien de salariés compte l'entreprise ?",
    "Quel est le pourcentage de femmes dans l'effectif ?",
    "Quelles sont les actions de formation des collaborateurs ?",
    "Comment l'entreprise assure-t-elle la santé et la sécurité au travail ?",
    # Gouvernance
    "Comment est composé le conseil d'administration ?",
    "Quelles sont les mesures anti-corruption mises en place ?",
]


def evaluer_retrieval():
    """
    Évalue la qualité de la recherche sémantique ChromaDB
    en soumettant des questions types et en mesurant les résultats.
    """
    print("=" * 60)
    print("📊 ÉVALUATION DU PIPELINE RAG (RETRIEVAL)")
    print("=" * 60)

    # Statistiques de la base
    stats = get_stats()
    print(f"\n📦 Base vectorielle : {stats['total_documents']} documents dans '{stats['collection_name']}'")

    if stats['total_documents'] == 0:
        print("\n[ERREUR] La base ChromaDB est vide. Lancez d'abord l'indexation :")
        print("  python tools/index_extracted_json_to_chroma.py")
        return {}

    questions_repondues = 0
    total_sources = 0
    total_distance = 0
    distances_comptees = 0
    labels_distribution = {"Environnemental": 0, "Social": 0, "Gouvernance": 0, "Autre": 0, "General": 0}

    print(f"\n--- Test de {len(QUESTIONS_TEST)} questions ESG ---\n")

    for i, question in enumerate(QUESTIONS_TEST, 1):
        resultats = rechercher(question, n_resultats=5)

        if resultats and resultats['documents'] and resultats['documents'][0]:
            questions_repondues += 1
            nb_sources = len(resultats['documents'][0])
            total_sources += nb_sources

            # Calculer la distance moyenne des résultats
            if resultats.get('distances') and resultats['distances'][0]:
                for dist in resultats['distances'][0]:
                    total_distance += dist
                    distances_comptees += 1

            # Distribution des labels
            for meta in resultats['metadatas'][0]:
                label = meta.get('label', 'Autre')
                if label in labels_distribution:
                    labels_distribution[label] += 1

            contexte = formater_contexte(resultats)
            extrait = contexte[:120].replace('\n', ' ') + "..." if contexte else "N/A"
            print(f"  ✅ Q{i}: \"{question}\"")
            print(f"     → {nb_sources} sources trouvées | Extrait: {extrait}")
        else:
            print(f"  ❌ Q{i}: \"{question}\" → Aucun résultat pertinent")

    # Calcul des métriques globales
    taux_reponse = (questions_repondues / len(QUESTIONS_TEST)) * 100 if QUESTIONS_TEST else 0
    moy_sources = total_sources / questions_repondues if questions_repondues > 0 else 0
    moy_distance = total_distance / distances_comptees if distances_comptees > 0 else 0

    print("\n" + "=" * 60)
    print("📈 RÉSULTATS DE L'ÉVALUATION RAG")
    print("=" * 60)
    print(f"  Taux de réponse           : {taux_reponse:.1f}% ({questions_repondues}/{len(QUESTIONS_TEST)})")
    print(f"  Sources moyennes/question : {moy_sources:.1f}")
    print(f"  Distance cosinus moyenne  : {moy_distance:.4f} (plus bas = plus pertinent)")
    print(f"  Distribution des labels   :")
    for label, count in labels_distribution.items():
        if count > 0:
            print(f"    - {label}: {count}")

    return {
        "taux_reponse": taux_reponse,
        "moy_sources": moy_sources,
        "moy_distance": moy_distance,
        "labels": labels_distribution
    }


if __name__ == "__main__":
    evaluer_retrieval()
