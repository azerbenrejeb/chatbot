"""
Script de migration pour convertir les annotations CNN 5 classes en 2 classes.
Environnemental, Social, Gouvernance, Graphique_ESG -> ESG
Autre -> NON_ESG
"""
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
CNN_DATASET_DIR = BASE_DIR / "data" / "cnn_dataset"

def migrer():
    print("[MIGRATION] Début de la migration des annotations...")
    
    esg_dir = CNN_DATASET_DIR / "ESG"
    non_esg_dir = CNN_DATASET_DIR / "NON_ESG"
    
    esg_dir.mkdir(parents=True, exist_ok=True)
    non_esg_dir.mkdir(parents=True, exist_ok=True)
    
    mapping = {
        "Environnemental": esg_dir,
        "Social": esg_dir,
        "Gouvernance": esg_dir,
        "Graphique_ESG": esg_dir,
        "Autre": non_esg_dir
    }
    
    deplacements = 0
    
    for old_name, new_dir in mapping.items():
        old_dir = CNN_DATASET_DIR / old_name
        if old_dir.exists():
            files = list(old_dir.glob("*.jpg")) + list(old_dir.glob("*.jpeg")) + list(old_dir.glob("*.png"))
            for f in files:
                dest = new_dir / f.name
                if not dest.exists():
                    shutil.move(str(f), str(dest))
                    deplacements += 1
                else:
                    # Doublon résolu : supprimer le fichier source pour nettoyer
                    f.unlink()
            
            # Supprimer le dossier vide
            try:
                old_dir.rmdir()
            except Exception as e:
                print(f"[WARN] Impossible de supprimer le dossier {old_dir.name}: {e}")
                
    print(f"[OK] Migration terminée. {deplacements} images migrées avec succès dans les nouvelles classes ESG / NON_ESG !")

if __name__ == "__main__":
    migrer()
