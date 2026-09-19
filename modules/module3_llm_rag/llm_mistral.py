"""
MODULE 6 — MISTRAL 7B (Ollama client).
Génère des réponses basées uniquement sur le contexte sémantique de ChromaDB.
"""
import ollama
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import OLLAMA_MODEL
from modules.module3_llm_rag.prompt_templates import SYSTEM_PROMPT, template_rag


def generer_reponse(question, contexte):
    """
    Génère une réponse via local Ollama Mistral 7B en utilisant un prompt anti-hallucination.
    
    Args:
        question: Question de l'utilisateur
        contexte: Contexte formaté extrait de ChromaDB
    
    Returns:
        Réponse textuelle de Mistral
    """
    if not contexte:
        return "Information non disponible dans les rapports chargés."

    prompt = template_rag(contexte, question)

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération avec Ollama: {e}")
        return f"Erreur de connexion avec Ollama (modèle '{OLLAMA_MODEL}') : {str(e)}"


def generer_reponse_conformite(question, resume_conformite):
    """
    Génère une réponse via local Ollama Mistral 7B pour une question de conformité ESG.
    
    Args:
        question: Question de l'utilisateur.
        resume_conformite: Résumé textuel des scores et indicateurs manquants.
        
    Returns:
        Réponse de Mistral.
    """
    system_prompt = "Tu es un assistant ESG expert en standards GRI et ESRS (CSRD)."
    prompt = f"""Voici le rapport de conformité calculé automatiquement à partir des indicateurs extraits du rapport RSE :

{resume_conformite}

Réponds à la question de l'utilisateur en te basant uniquement sur ce rapport de conformité. Si la question porte sur un standard précis (GRI ou ESRS), concentre ta réponse sur ce standard tout en mentionnant brièvement l'autre si pertinent. Donne les scores, cite les indicateurs présents et manquants si pertinent, et reste factuel.

Question : {question}
"""
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération de conformité avec Ollama: {e}")
        return f"Erreur de connexion avec Ollama pour la conformité (modèle '{OLLAMA_MODEL}') : {str(e)}"



if __name__ == "__main__":
    # Test simple (Ollama doit tourner en tâche de fond)
    test_context = "Le groupe RSE Time a réduit ses émissions de scope 1 de 12% en 2024. (Source: RSE_Report_2024, page 14)"
    test_q = "De combien de pourcent RSE Time a réduit ses émissions de scope 1 en 2024 ?"
    print("Génération de test...")
    rep = generer_reponse(test_q, test_context)
    print(f"Question: {test_q}")
    print(f"Réponse: {rep}")
