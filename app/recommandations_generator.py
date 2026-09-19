import sys
from pathlib import Path

# Résolution des imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, OLLAMA_MODEL
from app.compliance_checker import extraire_references_uniques, calculer_score_conformite
import ollama

def generer_recommandations(session_id: int) -> list[str]:
    """
    Génère les 3 recommandations prioritaires sous forme de phrases courtes et actionnables
    basées sur les indicateurs manquants des dimensions les plus faibles.
    
    :param session_id: Identifiant de la session en base.
    :return: Liste de 3 phrases de recommandations.
    """
    # 1. Obtenir les indicateurs trouvés pour la session
    refs_trouvees = extraire_references_uniques(session_id=session_id)
    score_data = calculer_score_conformite(refs_trouvees)
    
    # 2. Trier les dimensions par score GRI croissant (le plus faible d'abord)
    dimensions_sortees = sorted(
        score_data["dimensions"].keys(),
        key=lambda dim: score_data["dimensions"][dim]["gri"]["score"]
    )
    
    # 3. Sélectionner les 3 premiers indicateurs manquants au global
    missing_selected = []
    for dim in dimensions_sortees:
        manquants = score_data["dimensions"][dim]["gri"]["manquants"]
        for m in manquants:
            if len(missing_selected) < 3:
                missing_selected.append({
                    "code": m["code"],
                    "description": m["description"],
                    "dimension": dim
                })
            else:
                break
        if len(missing_selected) >= 3:
            break
            
    if not missing_selected:
        return ["Le rapport est déjà 100% conforme aux standards GRI ! Aucune recommandation nécessaire."]
        
    # 4. Pour chaque indicateur manquant, générer une recommandation via Mistral
    recommandations = []
    for m in missing_selected:
        prompt = f"""Tu es un consultant ESG expert. L'entreprise n'a pas reporté l'indicateur réglementaire suivant :
Indicateur : {m['code']}
Description : {m['description']}
Dimension : {m['dimension']}

Génère une recommandation d'action concrète et prioritaire en français sous la forme d'une seule phrase simple et directe du type :
"Pour combler l'indicateur {m['code']} ({m['description']}), il est recommandé de [action concrète suggérée par toi]"

Reste strictement sur une seule phrase, factuelle et directement applicable.
"""
        try:
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert ESG chargé de rédiger des recommandations d'action courtes et professionnelles en français."},
                    {"role": "user", "content": prompt}
                ]
            )
            recommandations.append(response['message']['content'].strip())
        except Exception as e:
            print(f"[ERR] Erreur lors de la génération de recommandation pour {m['code']} : {e}")
            # Fallback statique si Ollama échoue
            recommandations.append(
                f"Pour combler l'indicateur {m['code']} ({m['description']}), il est recommandé de mettre en place un processus de collecte et de reporting des données associées."
            )
            
    return recommandations
