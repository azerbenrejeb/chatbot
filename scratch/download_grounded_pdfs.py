"""
Téléchargement de nouveaux rapports ESG/RSE via des liens de redirection Google Grounding.
"""
import requests
from pathlib import Path
import time

RAW_PDF_DIR = Path(r"c:\RSE Time\chatbot\rapport_non _annoteé")
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

REPORTS = [
    ("Rapport_RSE_UBCI_2023.pdf", 
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEFQkW53eix-75n-ZUg2htY1H5BPcDuEH_4xfwErasbf8EnSb5Mw126SAZAMFWW1It9svcC6_AHVeGOI_ZcmH96E7O_fbFDR8J31oE8ch7qE6G7XuBSq-6aysLLMQorARzmeRzRDsIx5XzqK-gQdWDLnJIh3HAuzm8pjUXJHdbk"),
    ("Rapport_RSE_SFBT_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGOevfVdEdvU5N2NeoGf3t2fDpm0rHduPey2N7G_14Ng-8Gh3HOEh-mWQPksajMEKb0JNDRIs0G50gqaYQsKdGBQ7xLSxMSGpwYeTxk6HSR82dBvhYSWh0eFVZoEYZV8jVjdt61ZF-F42SmDHyJ-fyqdiSmvqA7eH7mjLz877BEfWQmmxg="),
    ("Rapport_RSE_TMM_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFFbdR4LNuo9VmLxstYihEl50HDzd1Oirhhm78e5-ZWmiiN67ATWUK8ggMO0HplKfCXIwPmkncbg6veENOO2H8QHeLn_YByBNUOHWLITDZSq9faXQBMKv6PRe7NtAIvDNTzLa-VYknkBVbE--BoYUiCmR08Xl5P168xrjqJ6_z7spOJjtbpgXQ="),
    ("Rapport_RSE_Promod_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHwXZiOuMXcHy8nbMb0pXcW46QHYaX0j9oqKSTx9aeC2UHYNuZ8lh1CImtQ9XZEihuvx_RSbq4Og3CQ9XSltHQ-ltKAsnnft7z544LYh1jx3gbu-veZOc1B-r7I8Xd7UgGUBuYiOfCA9YGo1ubX5JR73QQLic2JsyxZ8WIxYKVQOz3wqzvVLAk2HT1V_Fo434PINhV_oSr7J1ofVA=="),
    ("Rapport_RSE_Grant_Thornton_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFNR04tikOi8lWCA0gU4_kPgzPdtpAJTeYSetQsfblzzF0ugtqrp8BVGqvEqRm-xu0hxrO68R5ZeBizJBO0jn1q46ljhrFUp3hxyknX2rRN0hvuwt_cCi8JJZt0-3DCQvfTrlmtMBM9gZiWKDaHFykISpnU86YxhaWvi3YtibXh1vZrpb-qYyf5Up4N0UnlhbjHTaD0QVGpdZ-t4d-sMdV--wLCMSl50led_w4iTxjRJNofKNAM4WSZ_8Q="),
    ("Rapport_RSE_Ferrero_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEieadSIaxl40THFa0qmPIn-qn2fQI8k6_xGfsRkZ0dsNgwcl7gmevL5_R-z7RnFZkwCRCi_RdJilwrO-2QNC5Viw-VobU1LXXRflT6O6Pdow1xfUnU9lYLdUvClEzPK6XSSMWU7j9d-Z1J5qvSFnrwNIdX5Z4Chrn_S9taBRkeZ88oDFQZTPQV7Oai5mwWy6Kv"),
    ("Rapport_RSE_Clayens_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFEyCfm9ByKMvO2TRNpLEhckcw091sySDKDQy-CCTy-gsJi2HxjMDDtD6FphLWai8IVHBrTNOfqG9NJE-3crNmxvv0d3xALrdnIEarWh0lyT7yWxA6ttdn5c4bEw290hUt7E-FV6lfjWKrc1ipVH2St4vmg52Bc5wRAxCwqGs6sVdmVSDYpceolZLZa1UicM15vdXrQu0XtbIeWtmQ="),
    ("Rapport_RSE_Socotec_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEGYNZCjqzuwaRTIBa36YpsgdzymlQIdmihkXqLx6VaMHV0iGU2RRhBE18uNFLAlm3eI84dVbk1WbMTs7y3MZWSC9E_HddpWpKi7v39JBFvHDzruDFn4aMTb5dr7e9iPYjho_kEf2htpt0TDyahugbL41qNN7J9dYnerYzSZeJyd7TW0KC7OeeZnA=="),
    ("Rapport_RSE_Puratos_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF5NPKmttoj_SCcHJrYhLmT-ZJxY05TlOhf5IwdSmXbgtHew1P4y-OZyU7mwFfKNCGtHxMYL0GproVUbwup4cGoHkYzrNS97WyzRU3oS3hNQBNMuIFlJFGEs8ueTp0dAhT-Yk8LjLm8T78R5ZUIPoVHnD5HhWdbkT4Ea5g1s2vws0LnaPpBSIRGWZFgn6T20MueSmGWVVu0tBxgCayycbJ4Xs8="),
    ("Rapport_RSE_Aldes_2023.pdf",
     "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHaPB0tu06MUjx6WKhxDdeAD02iCFUgOOa4F6LlHdOmwlinrKZSXdcw0mheE_EDkZdRy0xV7269jwR6gdgH42ID6s5wuLQ-TGo1NYleqsmaSvcC0llDKthZoJa58-27WcW4HJBhi2KW81XLRxZgfEgVKPdDNoX_ba-ovtJeHn94jQ=="),
]

def download_pdf(name, url):
    dest_path = RAW_PDF_DIR / name
    if dest_path.exists() and dest_path.stat().st_size > 10000:
        print(f"[EXISTE] {name} ({dest_path.stat().st_size} octets)")
        return True

    print(f"[DL] {name}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True, stream=True)
        ct = r.headers.get("Content-Type", "").lower()
        print(f"     Status: {r.status_code} | Type: {ct}")

        if r.status_code != 200:
            print(f"     [ERR] HTTP {r.status_code}")
            return False

        content = b""
        for chunk in r.iter_content(chunk_size=8192):
            content += chunk

        if len(content) < 5000:
            print(f"     [ERR] Fichier trop petit ({len(content)} octets)")
            return False

        # Vérifier l'en-tête PDF
        if not content[:5] == b"%PDF-" and "pdf" not in ct:
            print(f"     [ERR] Pas un PDF valide (en-tête: {content[:20]})")
            return False

        with open(dest_path, "wb") as f:
            f.write(content)
        print(f"     [OK] {name} — {len(content)} octets")
        return True

    except Exception as e:
        print(f"     [ERR] {e}")
        return False

def main():
    print(f"=== Téléchargement de {len(REPORTS)} rapports ===")
    ok = 0
    for name, url in REPORTS:
        if download_pdf(name, url):
            ok += 1
        time.sleep(1.5)
    print(f"=== Fin: {ok}/{len(REPORTS)} téléchargés ===")

if __name__ == "__main__":
    main()
