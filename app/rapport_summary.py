import sqlite3
import sys
from pathlib import Path

# Résolution des chemins et des imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, OLLAMA_MODEL
from app.compliance_checker import extraire_references_uniques, calculer_score_conformite
import ollama

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"

def generer_resume_rapport(session_id: int) -> str:
    """
    Génère un résumé automatique du rapport RSE lié à la session donnée.
    Le résumé fait 8-10 lignes, structuré en 3 courts paragraphes (E, S, G)
    et se base sur les indicateurs ayant le plus fort taux de confiance.
    
    :param session_id: Identifiant de la session en base.
    :return: Résumé rédigé par le LLM.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # 1. Récupérer le nom du rapport lié à la session
    cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    rapport_name = row[0] if row else None
    
    # 2. Récupérer tous les indicateurs extraits pour ce rapport / session
    query = """
        SELECT reference_gri, valeur, unite, annee, dimension, confiance 
        FROM indicateurs_esg 
        WHERE session_id = ? OR (rapport_name = ? AND session_id IS NULL)
    """
    cursor.execute(query, (session_id, rapport_name))
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        return "Aucun indicateur extrait disponible pour générer un résumé automatique."
        
    # 3. Regrouper les indicateurs par dimension
    indicators_by_dim = {
        "Environnemental": [],
        "Social": [],
        "Gouvernance": []
    }
    
    for r in records:
        ref, val, unite, annee, dim, conf = r
        if not dim:
            # Fallback de dimensionnement
            if ref in ["GRI 302", "GRI 303", "GRI 305", "GRI 306"]:
                dim = "Environnemental"
            elif ref in ["GRI 401", "GRI 403", "GRI 404", "GRI 405"]:
                dim = "Social"
            elif ref in ["GRI 205", "GRI 206", "GRI 415", "GRI 419"]:
                dim = "Gouvernance"
                
        if dim in indicators_by_dim:
            indicators_by_dim[dim].append({
                "ref": ref,
                "valeur": val,
                "unite": unite,
                "annee": annee,
                "confiance": conf if conf is not None else 0.0
            })
            
    # 4. Pour chaque dimension, retenir les 3-4 indicateurs à plus forte confiance
    selected_indicators = {}
    for dim, items in indicators_by_dim.items():
        items_sorted = sorted(items, key=lambda x: x["confiance"], reverse=True)
        selected_indicators[dim] = items_sorted[:4]
        
    # 5. Récupérer les scores de conformité
    refs_trouvees = extraire_references_uniques(session_id=session_id, rapport_name=rapport_name)
    score_data = calculer_score_conformite(refs_trouvees)
    
    # 6. Construire la liste descriptive des indicateurs pour le LLM
    desc_parts = []
    for dim, items in selected_indicators.items():
        desc_parts.append(f"--- Dimension {dim} ---")
        if not items:
            desc_parts.append("Aucun indicateur marquant extrait.")
        for item in items:
            val_str = f"valeur: {item['valeur']}" if item['valeur'] is not None else "détecté"
            unite_str = f" {item['unite']}" if item['unite'] else ""
            annee_str = f" (année: {item['annee']})" if item['annee'] else ""
            desc_parts.append(f"- {item['ref']} : {val_str}{unite_str}{annee_str}")
            
    desc_indicateurs = "\n".join(desc_parts)
    
    prompt = f"""Tu es un expert RSE. Rédige un résumé automatique du rapport RSE analysé.
Le rapport présente la conformité réglementaire suivante :
- Niveau de conformité global GRI : {score_data['score_global_gri']}%
- Niveau de conformité global ESRS (CSRD) : {score_data['score_global_esrs']}%

Voici les principaux indicateurs extraits du document :
{desc_indicateurs}

Rédige un résumé de 8 à 10 lignes maximum, structuré en 3 courts paragraphes correspondant aux dimensions ESG :
1. Environnemental (E)
2. Social (S)
3. Gouvernance (G)

Instructions strictes :
- Sois factuel et précis.
- Écris uniquement en français.
- Base-toi uniquement sur les indicateurs et scores ci-dessus. N'invente pas d'autres données.
"""
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un expert ESG chargé de rédiger des résumés RSE fidèles et concis en français."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération avec Ollama: {e}")
        return f"Erreur de connexion avec Ollama (modèle '{OLLAMA_MODEL}') pour le résumé : {str(e)}"
