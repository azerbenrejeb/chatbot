import sqlite3
import sys
from pathlib import Path

# Résolution des imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, OLLAMA_MODEL
from app.compliance_checker import (
    extraire_references_uniques, 
    calculer_score_conformite,
    normaliser_reference
)
from app.gri_referentiel import INDICATEURS_REQUIS
import ollama

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"

def _get_indicators_for_session(session_id: int) -> tuple[dict, str]:
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # Récupérer le nom du rapport
    cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    rapport_name = row[0] if row else f"Session {session_id}"
    
    # Récupérer les indicateurs
    query = """
        SELECT reference_gri, valeur, unite, annee, dimension, confiance 
        FROM indicateurs_esg 
        WHERE session_id = ? OR (rapport_name = ? AND session_id IS NULL)
    """
    cursor.execute(query, (session_id, rapport_name))
    records = cursor.fetchall()
    conn.close()
    
    # Conserver la valeur ayant le plus fort taux de confiance pour chaque indicateur normalisé
    indicators = {}
    for ref, val, unite, annee, dim, conf in records:
        norm_ref = normaliser_reference(ref)
        if not norm_ref:
            continue
            
        if norm_ref not in indicators or (conf is not None and conf > indicators[norm_ref].get("confiance", 0.0)):
            # Trouver la description dans les indicateurs requis
            description = ""
            for dimension, list_ind in INDICATEURS_REQUIS.items():
                for cle, info in list_ind.items():
                    if info["GRI"] == norm_ref or info["ESRS"] == norm_ref:
                        description = info["description"]
                        break
                        
            indicators[norm_ref] = {
                "valeur": val,
                "unite": unite,
                "annee": annee,
                "confiance": conf if conf is not None else 0.0,
                "description": description
            }
            
    return indicators, rapport_name

def _format_valeur(val, unite):
    if val is not None and str(val).strip() != "" and str(val).strip().lower() != "none":
        if unite and str(unite).strip().lower() != "none":
            return f"{val} {unite}"
        return str(val)
    return "✅ Présent"


def comparer_rapports(session_id_a: int, session_id_b: int) -> dict:
    """
    Compare deux rapports RSE/ESG (sessions distinctes).
    Identifie les indicateurs communs, aligne leurs valeurs et compare leurs scores.
    
    :param session_id_a: Identifiant de la première session.
    :param session_id_b: Identifiant de la deuxième session.
    :return: Dictionnaire contenant les indicateurs communs, les scores et les noms de fichiers.
    """
    inds_a, name_a = _get_indicators_for_session(session_id_a)
    inds_b, name_b = _get_indicators_for_session(session_id_b)
    
    # Calculer les scores de conformité
    refs_a = extraire_references_uniques(session_id=session_id_a, rapport_name=name_a)
    refs_b = extraire_references_uniques(session_id=session_id_b, rapport_name=name_b)
    
    score_data_a = calculer_score_conformite(refs_a)
    score_data_b = calculer_score_conformite(refs_b)
    
    score_a = {"gri": score_data_a["score_global_gri"], "esrs": score_data_a["score_global_esrs"]}
    score_b = {"gri": score_data_b["score_global_gri"], "esrs": score_data_b["score_global_esrs"]}
    
    # Aligner les indicateurs communs
    indicateurs_communs = {}
    all_refs = set(inds_a.keys()) & set(inds_b.keys())
    
    for ref in sorted(all_refs):
        raw_a = inds_a[ref]["valeur"]
        raw_b = inds_b[ref]["valeur"]
        
        # Récupérer l'unité et la description
        unite = inds_a[ref]["unite"] if inds_a[ref]["unite"] else inds_b[ref]["unite"]
        description = inds_a[ref]["description"] if inds_a[ref]["description"] else inds_b[ref]["description"]
        
        val_a_fmt = _format_valeur(raw_a, unite)
        val_b_fmt = _format_valeur(raw_b, unite)
        
        indicateurs_communs[ref] = {
            "rapport_a": val_a_fmt,
            "rapport_b": val_b_fmt,
            "unite": unite,
            "description": description
        }
        
    return {
        "indicateurs_communs": indicateurs_communs,
        "score_a": score_a,
        "score_b": score_b,
        "nom_rapport_a": name_a,
        "nom_rapport_b": name_b
    }

def generer_synthese_comparaison(resultat_comparaison: dict) -> str:
    """
    Envoie le dictionnaire de comparaison à Mistral pour générer une synthèse rédigée.
    
    :param resultat_comparaison: Dictionnaire retourné par comparer_rapports.
    :return: Synthèse comparative rédigée en français par le LLM.
    """
    communs = resultat_comparaison.get("indicateurs_communs", {})
    name_a = resultat_comparaison.get("nom_rapport_a", "Rapport A")
    name_b = resultat_comparaison.get("nom_rapport_b", "Rapport B")
    score_a = resultat_comparaison.get("score_a", {})
    score_b = resultat_comparaison.get("score_b", {})
    
    if not communs:
        return "Aucun indicateur commun n'a été identifié pour réaliser une synthèse comparative."
        
    desc_communs = []
    for ref, data in communs.items():
        val_a = data['rapport_a'] if data['rapport_a'] is not None else "non renseigné"
        val_b = data['rapport_b'] if data['rapport_b'] is not None else "non renseigné"
        unite = data['unite'] if data['unite'] else ""
        desc_communs.append(
            f"- {ref} ({data['description']}) : {name_a} = {val_a} {unite} vs {name_b} = {val_b} {unite}"
        )
    desc_str = "\n".join(desc_communs)
    
    prompt = f"""Tu es un analyste ESG expert. Rédige une synthèse comparative de 5 à 6 lignes maximum entre ces deux rapports RSE :
1. Rapport A : {name_a} (Score global de conformité GRI: {score_a.get('gri')}%, ESRS: {score_a.get('esrs')}%)
2. Rapport B : {name_b} (Score global de conformité GRI: {score_b.get('gri')}%, ESRS: {score_b.get('esrs')}%)

Voici les indicateurs de performance communs extraits :
{desc_str}

Rédige une synthèse concise indiquant de manière claire et objective quel rapport est le plus performant par dimension (Environnemental, Social, Gouvernance).
Reste strictement factuel, écris en français et n'invente aucune information.
"""
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un analyste ESG impartial chargé d'éditer des synthèses comparatives structurées en français."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération de la synthèse avec Ollama: {e}")
        return f"Erreur de connexion avec Ollama (modèle '{OLLAMA_MODEL}') pour la synthèse comparative : {str(e)}"
