"""
Script d'extraction et d'injection de données NON_ESG.
Convertit les pages des PDF statistiques de l'ONU en images à 120 DPI
et les injecte directement dans data/cnn_dataset/NON_ESG pour équilibrer le dataset.
"""
import os
import fitz
from pathlib import Path

def extraire_non_esg():
    print("[UN-EXTRACT] Lancement de l'extraction des pages NON_ESG...")
    
    # Chemins
    rapports_dir = Path(r"c:\RSE Time\chatbot\rapport_non _annoteé")
    dest_dir = Path(r"c:\RSE Time\chatbot\data\cnn_dataset\NON_ESG")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Fichiers sources
    sources = [
        ("Table03.pdf", "un_table03"),
        ("world-stats-pocketbook-2021.pdf", "un_pocketbook_2021"),
        ("world-stats-pocketbook-2022.pdf", "un_pocketbook_2022")
    ]
    
    total_extraites = 0
    # Zoom pour 120 DPI (120 / 72 = 1.6666)
    zoom = 120.0 / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    for filename, prefix in sources:
        pdf_path = rapports_dir / filename
        if not pdf_path.exists():
            print(f"[WARN] Fichier introuvable : {pdf_path}")
            continue
            
        print(f"📄 Extraction de {filename}...")
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=mat)
                
                # Sauvegarder dans NON_ESG
                img_name = f"{prefix}_page_{page_num + 1}.jpg"
                dest_path = dest_dir / img_name
                pix.save(str(dest_path))
                total_extraites += 1
                
            doc.close()
            print(f"[OK] {len(doc)} pages extraites de {filename}")
        except Exception as e:
            print(f"[ERR] Erreur lors de l'extraction de {filename} : {e}")
            
    print(f"\n==========================================")
    print(f"✨ EXTRACTION TERMINEE !")
    print(f"   - {total_extraites} nouvelles images injectées directement dans NON_ESG !")
    print(f"==========================================\n")

if __name__ == "__main__":
    extraire_non_esg()
