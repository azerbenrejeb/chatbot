import sqlite3
import re
import json
import unicodedata
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, PROCESSED_DIR, RAW_PDF_DIR
from app.compliance_checker import normaliser_reference
from app.gri_referentiel import INDICATEURS_REQUIS

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"


def clean_float(value) -> float:
    """Nettoie et convertit une valeur textuelle en float de manière robuste."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    val_str = str(value).replace(" ", "").replace("\xa0", "").replace(".", "").replace(",", ".").strip()
    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _detecter_tendances_texte(rapport_name: str) -> list[dict]:
    """
    Extrait les séries temporelles directement depuis les tableaux et textes
    du rapport (JSON extrait) lorsque la BDD ne contient pas assez d'historique.
    """
    if not rapport_name:
        return []

    rapport_stem = Path(rapport_name).stem
    json_path = PROCESSED_DIR / f"{rapport_stem}_extracted.json"
    if not json_path.exists():
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    pages = data.get("pages", [])
    tendances = []

    # Patterns de recherche pour tableaux multi-années
    # Exemple 1 : Consommation électrique (kWh)
    elec_points = {}
    eau_points = {}
    ges_points = {}
    co2_ratio_points = {}
    formation_points = {}

    for p in pages:
        txt = p.get("text", "")
        lines = [l.strip() for l in txt.split("\n") if l.strip()]

        # Recherche de patterns d'années consécutives
        for idx, line in enumerate(lines):
            line_low = line.lower()

            # Consommation d'électricité
            if "total consommation" in line_low and "électricité" in line_low:
                # Regarder les lignes précédentes ou suivantes pour les années
                nums = []
                for nxt in lines[idx+1:idx+6]:
                    cleaned = clean_float(nxt)
                    if cleaned and cleaned > 1000:
                        nums.append(cleaned)
                if len(nums) >= 2:
                    elec_points = {"2022": nums[2] if len(nums) > 2 else nums[1], "2023": nums[1], "2024": nums[0]}

            # Gaz naturel
            if "gaz naturel" in line_low:
                nums = []
                for nxt in lines[idx+1:idx+5]:
                    cleaned = clean_float(nxt)
                    if cleaned and cleaned > 1000:
                        nums.append(cleaned)
                if len(nums) >= 2 and "2024" not in elec_points:
                    elec_points = {"2022": nums[2] if len(nums) > 2 else nums[1], "2023": nums[1], "2024": nums[0]}

            # Consommation d'eau
            if "consommation d’eau (m³)" in line_low or "consommation d'eau (m3)" in line_low:
                nums = []
                for nxt in lines[idx+1:idx+6]:
                    cleaned = clean_float(nxt)
                    if cleaned and cleaned > 100:
                        nums.append(cleaned)
                if len(nums) >= 2:
                    eau_points = {"2022": nums[2] if len(nums) > 2 else nums[1], "2023": nums[1], "2024": nums[0]}

            # Émissions CO2 transport (Kg CO2/km)
            if "émissions de co2 sur le transport" in line_low or "kg co2/km" in line_low:
                nums = []
                for nxt in lines[idx+1:idx+5]:
                    val = nxt.replace(",", ".").strip()
                    try:
                        fl = float(val)
                        if 0.1 < fl < 5.0:
                            nums.append(fl)
                    except ValueError:
                        pass
                if len(nums) >= 2:
                    co2_ratio_points = {"2022": nums[2] if len(nums) > 2 else nums[1], "2023": nums[1], "2024": nums[0]}

            # Heures de formation
            if "formation éco-conduite" in line_low or "heures de formation" in line_low:
                nums = []
                for nxt in lines[idx+1:idx+5]:
                    cleaned = clean_float(nxt)
                    if cleaned and 50 < cleaned < 50000:
                        nums.append(cleaned)
                if len(nums) >= 2:
                    formation_points = {"2022": nums[1], "2024": nums[0]}

    def _build_tendance(ref, desc, pts, alerte_si_hausse=True):
        if len(pts) < 2:
            return None
        annees = sorted(pts.keys())
        valeurs = [pts[y] for y in annees]
        v_init = valeurs[0]
        v_fin = valeurs[-1]
        if v_init == 0:
            return None
        var_pct = round(((v_fin - v_init) / v_init) * 100.0, 1)
        sens = "hausse" if var_pct > 2.0 else ("baisse" if var_pct < -2.0 else "stable")
        alerte = (sens == "hausse" and alerte_si_hausse) or (sens == "baisse" and not alerte_si_hausse)
        return {
            "reference_gri": ref,
            "description": desc,
            "annees": annees,
            "valeurs": valeurs,
            "variation_pct": var_pct,
            "sens": sens,
            "alerte": alerte
        }

    t1 = _build_tendance("GRI 302", "Consommation d'électricité totale (kWh)", elec_points, alerte_si_hausse=True)
    if t1:
        tendances.append(t1)

    t2 = _build_tendance("GRI 305", "Intensité des émissions carbone (Kg CO₂ / km)", co2_ratio_points, alerte_si_hausse=True)
    if t2:
        tendances.append(t2)

    t3 = _build_tendance("GRI 303", "Prélèvements et consommation d'eau (m³)", eau_points, alerte_si_hausse=True)
    if t3:
        tendances.append(t3)

    t4 = _build_tendance("GRI 404", "Volume d'heures de formation dispensées", formation_points, alerte_si_hausse=False)
    if t4:
        tendances.append(t4)

    return tendances


def detecter_tendances(session_id: int, rapport_name: str = None) -> list[dict]:
    """
    Détecte les tendances temporelles multi-années.
    Interroge d'abord la table SQLite `indicateurs_esg`, puis complète
    par une analyse du document textuel si nécessaire.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # 1. Résoudre le nom du rapport
    if not rapport_name and session_id:
        try:
            cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row[0]:
                rapport_name = row[0]
        except Exception:
            pass

    # 2. Récupérer les indicateurs multi-années stockés en base
    query = """
        SELECT reference_gri, valeur, annee, dimension, confiance 
        FROM indicateurs_esg 
        WHERE (session_id = ? OR (rapport_name = ? AND session_id IS NULL))
          AND annee IS NOT NULL AND valeur IS NOT NULL
    """
    records = []
    try:
        cursor.execute(query, (session_id, rapport_name))
        records = cursor.fetchall()
    except Exception:
        pass
    conn.close()
    
    # Regrouper par reference_gri
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
        
    tendances = []
    HAUSSE_EST_ALERT = {"GRI 302", "GRI 303", "GRI 305", "GRI 306"}
    
    for ref, datapoints in grouped_data.items():
        unique_datapoints = {}
        for dp in datapoints:
            yr = str(dp["annee"])
            if yr not in unique_datapoints:
                unique_datapoints[yr] = dp["valeur"]
                
        if len(unique_datapoints) < 2:
            continue
            
        sorted_years = sorted(unique_datapoints.keys())
        valeurs_triees = [unique_datapoints[yr] for yr in sorted_years]
        
        v_first = valeurs_triees[0]
        v_last = valeurs_triees[-1]
        if v_first == 0:
            continue
            
        variation_pct = round(((v_last - v_first) / v_first) * 100.0, 1)
        sens = "hausse" if variation_pct > 2.0 else ("baisse" if variation_pct < -2.0 else "stable")
        alerte = (sens == "hausse" and ref in HAUSSE_EST_ALERT)
        
        desc = ""
        for dim, list_ind in INDICATEURS_REQUIS.items():
            for cle, info in list_ind.items():
                if info["GRI"] == ref or info["ESRS"] == ref:
                    desc = info["description"]
                    break
        
        tendances.append({
            "reference_gri": ref,
            "description": desc or f"Indicateur {ref}",
            "annees": sorted_years,
            "valeurs": valeurs_triees,
            "variation_pct": variation_pct,
            "sens": sens,
            "alerte": alerte
        })

    # 3. Fallback d'enrichissement par analyse du texte si la BDD a moins de 2 tendances
    if len(tendances) < 2 and rapport_name:
        text_tendances = _detecter_tendances_texte(rapport_name)
        existing_refs = {t["reference_gri"] for t in tendances}
        for tt in text_tendances:
            if tt["reference_gri"] not in existing_refs:
                tendances.append(tt)

    return tendances
