"""
Téléchargement direct de rapports ESG/RSE publics depuis des URLs connues et stables.
"""
import requests
from pathlib import Path
import time

RAW_PDF_DIR = Path(r"c:\RSE Time\chatbot\rapport_non _annoteé")
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# URLs directes vers des rapports ESG/RSE publics
REPORTS = [
    # Schneider Electric - Sustainability Report 2023
    ("Schneider_Electric_Sustainability_Report_2023.pdf",
     "https://www.se.com/ww/en/assets/564/document/407997/sustainability-report-2023.pdf"),
    # TotalEnergies - Sustainability & Climate 2024 Progress Report
    ("TotalEnergies_Sustainability_Climate_2024.pdf",
     "https://totalenergies.com/sites/g/files/nytnzq121/files/documents/2024-03/Sustainability_Climate_2024_Progress_Report_EN.pdf"),
    # Veolia - Document Enregistrement Universel 2023
    ("Veolia_URD_2023.pdf",
     "https://www.veolia.com/sites/g/files/dvc4206/files/document/2024/04/Veolia-URD-2023-EN.pdf"),
    # Saint-Gobain - Integrated Report 2023
    ("Saint_Gobain_Integrated_Report_2023.pdf",
     "https://www.saint-gobain.com/sites/saint-gobain.com/files/media/document/Saint-Gobain_Integrated_Report_2023.pdf"),
    # BNP Paribas - ESG Report
    ("BNP_Paribas_CSR_Report_2023.pdf",
     "https://invest.bnpparibas/document/universal-registration-document-and-annual-financial-report-2023"),
    # Michelin - Annual and Sustainability Report 2023
    ("Michelin_Annual_Sustainability_2023.pdf",
     "https://www.michelin.com/documents/rapport-annuel-et-de-developpement-durable-2023/"),
    # Kering - Sustainability Progress Report 2023
    ("Kering_Sustainability_2023.pdf",
     "https://keringcorporate.dam.kering.com/m/5fd0950e7e6d2eaa/original/Kering-Sustainability-Progress-Report-2023.pdf"),
    # Accor - Integrated Report 2023
    ("Accor_Integrated_Report_2023.pdf",
     "https://group.accor.com/-/media/Project/Accor/AccorGroup/Documents/Finance-and-investors/Regulated-Information/Annual-Reports/2024/accor-universal-registration-document-2023-en.pdf"),
    # Legrand - CSR Report 2023
    ("Legrand_CSR_Report_2023.pdf",
     "https://www.legrandgroup.com/sites/default/files/2024-04/legrand-csr-report-2023.pdf"),
    # Pernod Ricard - ESG Strategic Plan
    ("Pernod_Ricard_ESG_2023.pdf",
     "https://www.pernod-ricard.com/sites/default/files/2024-03/Pernod%20Ricard%20-%20S%26R%20Report%202022-2023.pdf"),
    # Bouygues - Rapport RSE 2023
    ("Bouygues_RSE_2023.pdf",
     "https://www.bouygues.com/wp-content/uploads/2024/04/bouygues-csr-report-2023.pdf"),
    # Capgemini - ESG Report
    ("Capgemini_ESG_Report_2023.pdf",
     "https://www.capgemini.com/wp-content/uploads/2024/04/Capgemini-Environmental-Sustainability-Report_2023.pdf"),
    # Carrefour - Document Universel 2023
    ("Carrefour_URD_2023.pdf",
     "https://www.carrefour.com/sites/default/files/2024-04/Carrefour%20-%20Document%20d%27enregistrement%20universel%202023.pdf"),
    # LVMH - Social & Environmental Responsibility Report 2023
    ("LVMH_Social_Environmental_2023.pdf",
     "https://r.lvmh-static.com/uploads/2024/06/lvmh_ser-2023_va.pdf"),
    # Sodexo - Integrated Annual Report 2023
    ("Sodexo_Integrated_Report_2023.pdf",
     "https://www.sodexo.com/files/live/sites/com-global/files/02%20PDF/Finance/Sodexo-Integrated-Annual-Report-FY2023.pdf"),
]

def download_pdf(name, url):
    dest_path = RAW_PDF_DIR / name
    if dest_path.exists() and dest_path.stat().st_size > 10000:
        print(f"[EXISTE] {name} ({dest_path.stat().st_size} octets)")
        return True

    print(f"[DL] {name}")
    print(f"     URL: {url[:100]}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True, stream=True)
        ct = r.headers.get("Content-Type", "")
        print(f"     Status: {r.status_code} | Type: {ct}")

        if r.status_code != 200:
            print(f"     [ERR] HTTP {r.status_code}")
            return False

        # Vérifier que c'est bien un PDF (contenu ou URL)
        content = b""
        for chunk in r.iter_content(chunk_size=8192):
            content += chunk

        if len(content) < 5000:
            print(f"     [ERR] Fichier trop petit ({len(content)} octets) — probablement une page HTML")
            return False

        # Vérifier l'en-tête PDF
        if not content[:5] == b"%PDF-" and "application/pdf" not in ct:
            print(f"     [ERR] Pas un PDF valide (en-tête: {content[:20]})")
            return False

        with open(dest_path, "wb") as f:
            f.write(content)
        print(f"     [OK] {name} — {len(content)} octets")
        return True

    except requests.exceptions.Timeout:
        print(f"     [ERR] Timeout après 30s")
        return False
    except Exception as e:
        print(f"     [ERR] {e}")
        return False

def main():
    print(f"=== Téléchargement de {len(REPORTS)} rapports ESG/RSE ===\n")
    ok = 0
    for name, url in REPORTS:
        if download_pdf(name, url):
            ok += 1
        time.sleep(1)

    print(f"\n=== Résultat: {ok}/{len(REPORTS)} rapports téléchargés ===")

    # Compter le total dans le dossier
    all_pdfs = list(RAW_PDF_DIR.glob("*.pdf"))
    print(f"Total PDFs dans le dossier: {len(all_pdfs)}")

if __name__ == "__main__":
    main()
