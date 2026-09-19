import sqlite3
import re
import sys
from pathlib import Path

# Résolution des imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR
from app.compliance_checker import normaliser_reference
from app.gri_referentiel import INDICATEURS_REQUIS

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"

def clean_float(value) -> float:
    """
    Nettoie et convertit une valeur en float de manière robuste.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).replace(" ", "").replace("\xa0", "").replace(",", ".").strip()
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def detecter_tendances(session_id: int) -> list[dict]:
    """
    Détecte les tendances temporelles pour les indicateurs ayant des valeurs sur plusieurs années.
    
    :param session_id: Identifiant de la session en base.
    :return: Liste de dictionnaires décrivant les tendances.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # Récupérer le nom du rapport
    cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    rapport_name = row[0] if row else None
    
    # Récupérer les indicateurs
    query = """
        SELECT reference_gri, valeur, annee, dimension, confiance 
        FROM indicateurs_esg 
        WHERE session_id = ? OR (rapport_name = ? AND session_id IS NULL)
    """
    cursor.execute(query, (session_id, rapport_name))
    records = cursor.fetchall()
    conn.close()
    
    # 1. Regrouper par reference_gri normalisée
    grouped_data = {}
    for ref, val, annee, dim, conf in records:
        norm_ref = normaliser_reference(ref)
        if not norm_ref or not annee or val is None:
            continue
            
        val_float = clean_float(val)
        if val_float is None:
            continue
            
        try:
            annee_int = int(annee)
        except ValueError:
            continue
            
        if norm_ref not in grouped_data:
            grouped_data[norm_ref] = []
            
        grouped_data[norm_ref].append({
            "annee": annee_int,
            "valeur": val_float,
            "dimension": dim
        })
        
    # 2. Filtrer pour ne garder que ceux ayant plusieurs années différentes
    tendances = []
    
    # Liste des indicateurs environnementaux où une hausse est négative (alerte)
    HAUSSE_EST_ALERT = {"GRI 302", "GRI 303", "GRI 305", "GRI 306"}
    
    for ref, datapoints in grouped_data.items():
        # Dédoublonner par année en prenant la première valeur (ou max/min, ici on dédoublonne simplement)
        unique_datapoints = {}
        for dp in datapoints:
            yr = dp["annee"]
            if yr not in unique_datapoints:
                unique_datapoints[yr] = dp["valeur"]
                
        if len(unique_datapoints) < 2:
            continue
            
        # Trier par année croissante
        sorted_years = sorted(unique_datapoints.keys())
        valeurs_triees = [unique_datapoints[yr] for yr in sorted_years]
        
        valeur_premiere = valeurs_triees[0]
        valeur_derniere = valeurs_triees[-1]
        
        if valeur_premiere == 0:
            # Éviter la division par zéro
            continue
            
        # Calcul de la variation en %
        variation_pct = round(((valeur_derniere - valeur_premiere) / valeur_premiere) * 100.0, 2)
        
        # Déterminer le sens de la tendance (seuil ±3%)
        if variation_pct > 3.0:
            sens = "hausse"
        elif variation_pct < -3.0:
            sens = "baisse"
        else:
            sens = "stable"
            
        # Déterminer si c'est une alerte
        alerte = False
        if sens == "hausse" and ref in HAUSSE_EST_ALERT:
            alerte = True
            
        # Récupérer la description de l'indicateur
        description = ""
        for dimension, list_ind in INDICATEURS_REQUIS.items():
            for cle, info in list_ind.items():
                if info["GRI"] == ref or info["ESRS"] == ref:
                    description = info["description"]
                    break
        
        if not description:
            description = f"Indicateur {ref}"
            
        tendances.append({
            "reference_gri": ref,
            "description": description,
            "annees": sorted_years,
            "valeurs": valeurs_triees,
            "variation_pct": variation_pct,
            "sens": sens,
            "alerte": alerte
        })
        
    return tendances
