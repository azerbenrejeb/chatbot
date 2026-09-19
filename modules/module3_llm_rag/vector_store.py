"""
MODULE 5 — ChromaDB (Base vectorielle RAG).
Stocke les paragraphes ESG sous forme de vecteurs pour la recherche sémantique.
"""
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import (
    CHROMA_DB_DIR, CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME, SEARCH_N_RESULTS, SIMILARITY_THRESHOLD
)


def get_client():
    """Retourne un client ChromaDB persistant."""
    return chromadb.PersistentClient(path=str(CHROMA_DB_DIR))


def get_embedding_function():
    """Retourne la fonction d'embedding multilingue."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


def get_collection():
    """Retourne la collection ChromaDB pour les rapports ESG."""
    client = get_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef
    )
    return collection


def stocker_paragraphes(paragraphes, labels, metadonnees):
    """
    Stocke des paragraphes dans ChromaDB avec leurs métadonnées.
    
    Args:
        paragraphes: Liste de textes
        labels: Liste de labels (Environnemental/Social/Gouvernance)
        metadonnees: Liste de dicts {'page': int, 'rapport': str, 'annee': str}
    """
    collection = get_collection()

    # Générer des IDs uniques basés sur le contenu existant
    existing_count = collection.count()

    collection.add(
        documents=paragraphes,
        metadatas=[{
            'label': label,
            'page': str(meta['page']),
            'rapport': meta['rapport'],
            'annee': meta.get('annee', 'N/A')
        } for label, meta in zip(labels, metadonnees)],
        ids=[f'doc_{existing_count + i}' for i in range(len(paragraphes))]
    )

    print(f"[OK] {len(paragraphes)} paragraphes stockés dans ChromaDB (total: {collection.count()})")


def rechercher(question, n_resultats=None, filtre_label=None, filtre_rapport=None):
    """
    Recherche sémantique dans ChromaDB.
    
    Args:
        question: Question en langage naturel
        n_resultats: Nombre de résultats à retourner
        filtre_label: Filtrer par label ESG (optionnel)
        filtre_rapport: Filtrer par nom de rapport (optionnel)
    
    Returns:
        Résultats de la recherche ou None si aucun résultat pertinent
    """
    if n_resultats is None:
        n_resultats = SEARCH_N_RESULTS

    collection = get_collection()

    if collection.count() == 0:
        return None

    # Construction du filtre ChromaDB
    where_clauses = []
    if filtre_label:
        where_clauses.append({'label': filtre_label})
    if filtre_rapport:
        where_clauses.append({'rapport': filtre_rapport})

    if len(where_clauses) == 1:
        where = where_clauses[0]
    elif len(where_clauses) > 1:
        where = {'$and': where_clauses}
    else:
        where = None

    resultats = collection.query(
        query_texts=[question],
        n_results=min(n_resultats, collection.count()),
        where=where
    )

    # Vérifier le score de similarité
    if resultats['distances'] and resultats['distances'][0]:
        if resultats['distances'][0][0] > SIMILARITY_THRESHOLD:
            return None  # Pas de résultat assez pertinent

    return resultats


def formater_contexte(resultats):
    """
    Formate les résultats ChromaDB en contexte lisible pour le LLM.
    
    Returns:
        Texte formaté avec sources
    """
    if not resultats or not resultats['documents'] or not resultats['documents'][0]:
        return None

    contexte_parts = []
    for i, (doc, meta) in enumerate(zip(resultats['documents'][0], resultats['metadatas'][0])):
        source = f"(Source: {meta.get('rapport', 'N/A')}, page {meta.get('page', 'N/A')})"
        contexte_parts.append(f"[{i+1}] {doc}\n{source}")

    return '\n\n'.join(contexte_parts)


def get_stats():
    """Retourne les statistiques de la collection ChromaDB."""
    collection = get_collection()
    return {
        'total_documents': collection.count(),
        'collection_name': CHROMA_COLLECTION_NAME
    }


if __name__ == "__main__":
    stats = get_stats()
    print(f"ChromaDB: {stats['total_documents']} documents dans '{stats['collection_name']}'")
