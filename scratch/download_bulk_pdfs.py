import requests
import re
import urllib.parse
from pathlib import Path
import time

# Configuration
RAW_PDF_DIR = Path("c:/RSE Time/chatbot/rapport_non _annoteé")
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def search_duckduckgo_pdfs(query, max_links=40):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    print(f"Recherche DuckDuckGo : {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"Erreur HTTP {r.status_code}")
            return []
        
        # Trouver tous les liens d'origine dans les résultats
        # DDG utilise souvent des redirections ou des liens directs vers les sites dans la classe 'result__snippet' ou 'result__url'
        # Cherchons les URLs se terminant par .pdf
        links = []
        # Trouver les href
        hrefs = re.findall(r'href="([^"]+)"', r.text)
        for href in hrefs:
            # Nettoyer l'URL DDG si elle est encapsulée dans une redirection
            if "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in query_params:
                    href = query_params['uddg'][0]
            
            # Vérifier si c'est un PDF
            if href.lower().endswith(".pdf") and href not in links:
                links.append(href)
                
        print(f"Trouvé {len(links)} liens PDF uniques dans cette recherche.")
        return links[:max_links]
    except Exception as e:
        print(f"Erreur lors de la recherche : {e}")
        return []

def download_pdf(url, dest_dir):
    try:
        # Extraire le nom de fichier
        filename = Path(urllib.parse.unquote(url.split("/")[-1])).name
        # Nettoyer le nom de fichier
        filename = re.sub(r"[^\w\-_.]", "_", filename)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
            
        dest_path = dest_dir / filename
        
        if dest_path.exists() and dest_path.stat().st_size > 0:
            print(f"[EXISTE] {filename}")
            return True
            
        print(f"Téléchargement de {url} ...")
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        if r.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"[OK] Sauvegardé sous {filename} ({dest_path.stat().st_size} octets)")
            return True
        else:
            print(f"[ERR] Status {r.status_code} pour {url}")
            return False
    except Exception as e:
        print(f"[ERR] Exception pour {url} : {e}")
        return False

def main():
    queries = [
        'filetype:pdf "rapport rse" 2023',
        'filetype:pdf "rapport esg" 2023',
        'filetype:pdf "rapport de développement durable" 2023',
        'filetype:pdf "sustainability report" 2023 esg',
        'filetype:pdf "rapport rse" 2024',
        'filetype:pdf "sustainability report" 2024 esg'
    ]
    
    all_links = []
    for q in queries:
        links = search_duckduckgo_pdfs(q)
        all_links.extend(links)
        # Éviter d'être bloqué
        time.sleep(3)
        
    unique_links = list(set(all_links))
    print(f"\nAu total : {len(unique_links)} liens uniques trouvés.")
    
    downloaded_count = 0
    for url in unique_links:
        if downloaded_count >= 35:
            print("Limite de 35 téléchargements atteinte.")
            break
        success = download_pdf(url, RAW_PDF_DIR)
        if success:
            downloaded_count += 1
            # Petit délai entre les téléchargements
            time.sleep(1)
            
    print(f"\nTerminé ! {downloaded_count} rapports PDF téléchargés avec succès dans {RAW_PDF_DIR}")

if __name__ == "__main__":
    main()
