"""
Auto-annotateur CNN de très haute précision (Sélection Stricte).
Analyse les 1337 pages des 16 rapports et applique des critères stricts
pour isoler les pages purement ESG/RSE des pages génériques (financières, marketing, introductives).
"""
import os
import shutil
import re
from pathlib import Path
import fitz
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import RAW_PDF_DIR, CNN_DATASET_DIR, PROCESSED_DIR, CNN_CLASSES, create_directories

# 1. Mots-clés de très haute spécificité (suffisent à classer en ESG s'ils sont présents)
ULTRA_SPECIFIC_KEYWORDS = [
    "scope 1", "scope 2", "scope 3", "ges", "co2", "carbone", "climat", "carbon", "bilan carbone",
    "empreinte carbone", "durabilité", "gri", "csrd", "odd", "biodiversité", "renouvelable", 
    "photovoltaïque", "éolien", "mixité", "accident du travail", "droits de l'homme", "rse", "esg"
]

# 2. Mots-clés généraux (nécessitent d'être combinés pour être valides)
GENERAL_RSE_KEYWORDS = [
    "environnement", "social", "gouvernance", "sécurité", "diversité", "femme", "inclusion",
    "board", "conseil d'administration", "éthique", "formation", "déchet", "eau", "énergie", 
    "parité", "égalité", "durable", "salar", "sécurité", "formation", "handicap"
]

# 3. Mots-clés d'exclusion (renvoient souvent vers du NON_ESG sauf si forte présence RSE)
EXCLUSION_KEYWORDS = [
    "sommaire", "table des matières", "legal", "disclaimer", "introduction", "présentation du groupe",
    "lettre du président", "chiffres clés financiers", "méthodologie", "historique"
]

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def auto_annoter_strict():
    print("[AUTO-ANNOTATE] Lancement de l'auto-annotation hyper-sélective et stricte...")
    create_directories()
    
    images_dir = PROCESSED_DIR / "images"
    esg_dir = CNN_DATASET_DIR / "ESG"
    non_esg_dir = CNN_DATASET_DIR / "NON_ESG"
    
    # Nettoyer et recréer les répertoires propres
    if esg_dir.exists(): shutil.rmtree(esg_dir)
    if non_esg_dir.exists(): shutil.rmtree(non_esg_dir)
    esg_dir.mkdir(parents=True, exist_ok=True)
    non_esg_dir.mkdir(parents=True, exist_ok=True)
    
    # Lister et trier les images
    all_images = []
    if images_dir.exists():
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            all_images.extend(list(images_dir.glob(ext)))
            
    if not all_images:
        print("[ERR] Aucune image trouvée.")
        return
        
    all_images = sorted(all_images, key=natural_sort_key)
    print(f"Traitement strict de {len(all_images)} pages.")
    
    annotated_esg = 0
    annotated_non_esg = 0
    errors = 0
    
    pdf_cache = {}
    
    for img_path in all_images:
        img_name = img_path.name
        
        try:
            parts = img_name.rsplit("_page_", 1)
            if len(parts) != 2:
                shutil.copy2(str(img_path), str(non_esg_dir / img_name))
                annotated_non_esg += 1
                continue
                
            rapport_name = parts[0]
            page_num = int(parts[1].split(".")[0]) - 1
            
            # Charger PDF
            pdf_path = RAW_PDF_DIR / f"{rapport_name}.pdf"
            if not pdf_path.exists():
                pdf_path = None
                for candidate in RAW_PDF_DIR.glob("*.pdf"):
                    if candidate.stem == rapport_name:
                        pdf_path = candidate
                        break
                        
            if pdf_path is None or not pdf_path.exists():
                shutil.copy2(str(img_path), str(non_esg_dir / img_name))
                annotated_non_esg += 1
                continue
                
            pdf_str = str(pdf_path)
            if pdf_str not in pdf_cache:
                pdf_cache[pdf_str] = fitz.open(pdf_path)
                
            doc = pdf_cache[pdf_str]
            
            if page_num >= len(doc):
                shutil.copy2(str(img_path), str(non_esg_dir / img_name))
                annotated_non_esg += 1
                continue
                
            page = doc.load_page(page_num)
            text = page.get_text()
            
            is_esg = False
            
            if text:
                text_lower = text.lower()
                text_len = len(text_lower.strip())
                
                # Heuristique stricte :
                # - Doit avoir une taille minimale (> 150 caractères)
                if text_len > 150:
                    # 1. Vérifier la présence de mots-clés d'ultra-haute spécificité (scopes, co2, ges, etc.)
                    has_ultra = any(kw in text_lower for kw in ULTRA_SPECIFIC_KEYWORDS)
                    
                    # 2. Vérifier la combinaison de plusieurs mots généraux RSE
                    matched_general = [kw for kw in GENERAL_RSE_KEYWORDS if kw in text_lower]
                    has_general_combo = len(set(matched_general)) >= 2  # Au moins 2 mots différents
                    
                    # 3. Exclusions strictes : si c'est un sommaire ou disclaimer sans mots ultra-spécifiques -> NON_ESG
                    is_exclusion = any(kw in text_lower for kw in EXCLUSION_KEYWORDS)
                    
                    if has_ultra and not (is_exclusion and not any(w in text_lower for w in ["scope", "co2", "ges"])):
                        is_esg = True
                    elif has_general_combo and not is_exclusion:
                        is_esg = True
            
            # Copie vers la destination finale
            if is_esg:
                shutil.copy2(str(img_path), str(esg_dir / img_name))
                annotated_esg += 1
            else:
                shutil.copy2(str(img_path), str(non_esg_dir / img_name))
                annotated_non_esg += 1
                
        except Exception as e:
            print(f"[WARN] Erreur {img_name}: {e}")
            shutil.copy2(str(img_path), str(non_esg_dir / img_name))
            annotated_non_esg += 1
            errors += 1
            
    # Fermer le cache
    for doc in pdf_cache.values():
        doc.close()
        
    print("\n==========================================")
    print("🌟 RÉSULTATS DE L'AUTO-ANNOTATION STRICTE :")
    print(f"   - Classés ESG (pures pages RSE/Émissions) : {annotated_esg}")
    print(f"   - Classés NON_ESG (génériques, financiers) : {annotated_non_esg}")
    print(f"   - Total des images classées                : {annotated_esg + annotated_non_esg} / {len(all_images)}")
    print("==========================================\n")

if __name__ == "__main__":
    auto_annoter_strict()
