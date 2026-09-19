import fitz
import os
from pathlib import Path
import sys

# Ajouter le dossier racine au path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import RAW_PDF_DIR, PROCESSED_DIR, PDF_DPI

def create_directories():
    """Crée les dossiers de sortie s'ils n'existent pas."""
    output_dir = PROCESSED_DIR / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def convert_pdf_to_images(pdf_path, output_dir):
    """
    Convertit un fichier PDF en images (une image par page) en utilisant PyMuPDF (fitz).
    """
    print(f"📄 Conversion de {pdf_path.name} en cours...")
    
    try:
        # Ouvrir le PDF avec PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Le facteur de zoom correspond au DPI. Par défaut PyMuPDF est à 72 DPI.
        # zoom = DPI / 72
        zoom = PDF_DPI / 72
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            
            # Nommer l'image avec le nom du PDF et le numéro de page
            image_name = f"{pdf_path.stem}_page_{page_num + 1}.jpg"
            image_path = output_dir / image_name
            
            # Sauvegarder l'image
            pix.save(str(image_path))
            
        print(f"[OK] {len(doc)} pages extraites de {pdf_path.name}")
        return True
        
    except Exception as e:
        print(f"[ERR] Erreur lors de la conversion de {pdf_path.name} : {str(e)}")
        return False

def convert_all_pdfs():
    """
    Parcourt le dossier contenant les rapports bruts et convertit tous les PDFs.
    """
    output_dir = create_directories()
    
    if not RAW_PDF_DIR.exists():
        print(f"[ERR] Le dossier {RAW_PDF_DIR} n'existe pas. Veuillez le créer et y ajouter des PDF.")
        return
        
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"[ERR] Aucun fichier PDF trouvé dans {RAW_PDF_DIR}")
        return
        
    print(f"Trouvé {len(pdf_files)} fichier(s) PDF à traiter.")
    
    for pdf in pdf_files:
        convert_pdf_to_images(pdf, output_dir)
        
    print("[OK] Conversion de tous les PDF terminée !")

if __name__ == "__main__":
    convert_all_pdfs()
