"""
MODULE 5 & 6 — Moteur RAG ESG.
Orchestre la recherche sémantique (ChromaDB) et la génération de réponses (Mistral 7B).
"""
import sqlite3
import unicodedata
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from modules.module3_llm_rag.vector_store import rechercher, formater_contexte
from modules.module3_llm_rag.llm_mistral import generer_reponse, generer_reponse_conformite
from app.compliance_checker import (
    extraire_references_uniques, 
    calculer_score_conformite, 
    generer_resume_conformite_textuel,
    DATABASE_PATH
)


def detecter_question_conformite(question_utilisateur: str) -> bool:
    """
    Détecte si la question porte sur la conformité ESG (GRI, ESRS, CSRD, etc.).
    
    :param question_utilisateur: Question en français de l'utilisateur.
    :return: True si lié à la conformité, False sinon.
    """
    keywords = [
        "conforme", "conformité", "respecte", "manque", "manquant", 
        "indicateur", "norme GRI", "standard GRI", "GRI", "ESRS", "CSRD"
    ]
    
    # Normalisation pour enlever les accents et passer en minuscule
    def nettoyer_texte(t):
        return "".join(
            c for c in unicodedata.normalize("NFD", t.lower())
            if unicodedata.category(c) != "Mn"
        )
        
    q_clean = nettoyer_texte(question_utilisateur)
    return any(nettoyer_texte(kw) in q_clean for kw in keywords)


def detecter_standard_demande(question_utilisateur: str) -> str:
    """
    Détecte si la question cible spécifiquement un standard (GRI ou ESRS).
    
    :param question_utilisateur: Question en français de l'utilisateur.
    :return: "esrs", "gri", ou "both".
    """
    q_lower = question_utilisateur.lower()
    has_esrs = "esrs" in q_lower or "csrd" in q_lower
    has_gri = "gri" in q_lower
    
    if has_esrs and not has_gri:
        return "esrs"
    elif has_gri and not has_esrs:
        return "gri"
    else:
        return "both"


def interroger_rapports(question, n_resultats=3, filtre_label=None, filtre_rapport=None, session_id=None):
    """
    Pipeline RAG complet :
    1. Si question de conformité, résout le rapport, calcule la conformité, injecte le résumé et appelle Mistral.
    2. Sinon, recherche sémantique dans ChromaDB, formate le contexte, et appelle Mistral.
    
    Args:
        question: Question en français
        n_resultats: Nombre de passages à récupérer (défaut: 3)
        filtre_label: Label ESG pour filtrer les passages (Environnemental, Social, Gouvernance)
        filtre_rapport: Nom du rapport pour filtrer (optionnel)
        session_id: Identifiant unique de session SQLite (optionnel)
        
    Returns:
        Dictionnaire : {'reponse': str, 'sources': list, 'contexte_brut': str}
    """
    # --- Cas 1 : Question de conformité ---
    if detecter_question_conformite(question):
        rapport_nom = filtre_rapport
        
        # Résoudre le nom du rapport à partir de la session si non spécifié
        if not rapport_nom and session_id:
            try:
                conn = sqlite3.connect(str(DATABASE_PATH))
                cursor = conn.cursor()
                cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                if row:
                    rapport_nom = row[0]
                conn.close()
            except Exception:
                pass

        if not rapport_nom:
            return {
                'reponse': "Veuillez charger et sélectionner un rapport RSE spécifique dans la barre latérale pour analyser sa conformité aux standards GRI et ESRS/CSRD.",
                'sources': [],
                'contexte_brut': ""
            }

        # Extraire les indicateurs et calculer le score
        references = extraire_references_uniques(session_id, rapport_nom)
        conformity_data = calculer_score_conformite(references)
        resume_text = generer_resume_conformite_textuel(conformity_data)

        # Ajouter des consignes de focus pour le LLM selon le standard ciblé
        standard = detecter_standard_demande(question)
        instruction_focus = ""
        if standard == "gri":
            instruction_focus = "\nL'utilisateur s'intéresse spécifiquement au standard GRI. Concentre ta réponse sur le standard GRI."
        elif standard == "esrs":
            instruction_focus = "\nL'utilisateur s'intéresse spécifiquement au standard ESRS/CSRD. Concentre ta réponse sur le standard ESRS et la préparation à la CSRD."

        # Générer la réponse de conformité avec Mistral
        reponse = generer_reponse_conformite(question, resume_text + instruction_focus)

        # Source métadonnées factices pour la conformité
        sources = [{
            'document': rapport_nom,
            'page': 'Analyse Globale',
            'label': 'Conformité',
            'extrait': 'Rapport synthétique GRI & ESRS (CSRD) généré par le moteur de conformité.'
        }]

        return {
            'reponse': reponse,
            'sources': sources,
            'contexte_brut': resume_text
        }

    # --- Cas 2 : Question RAG classique ---
    # 1. Recherche sémantique
    resultats = rechercher(question, n_resultats=n_resultats, filtre_label=filtre_label, filtre_rapport=filtre_rapport)

    # Si aucun résultat pertinent
    if not resultats or not resultats['documents'] or not resultats['documents'][0]:
        return {
            'reponse': "Information non disponible dans les rapports chargés.",
            'sources': [],
            'contexte_brut': ""
        }

    # 2. Formater le contexte
    contexte = formater_contexte(resultats)

    # 3. Génération de réponse
    reponse = generer_reponse(question, contexte)

    # 4. Extraire les métadonnées des sources
    sources = []
    for doc, meta in zip(resultats['documents'][0], resultats['metadatas'][0]):
        sources.append({
            'document': meta.get('rapport', 'Inconnu'),
            'page': meta.get('page', 'N/A'),
            'label': meta.get('label', 'N/A'),
            'extrait': doc[:150] + "..."
        })

    return {
        'reponse': reponse,
        'sources': sources,
        'contexte_brut': contexte
    }


if __name__ == "__main__":
    # Test d'intégration rapide
    test_q = "Quelles sont les émissions de CO2 ?"
    print(f"Test RAG pour: '{test_q}'")
    res = interroger_rapports(test_q)
    print(f"Réponse: {res['reponse']}")
    print(f"Sources: {res['sources']}")

