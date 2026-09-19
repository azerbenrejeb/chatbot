import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.module3_llm_rag.rag_engine import interroger_rapports

q = "Quelles sont les émissions de CO2 ?"

print("--- TEST 1 : Recherche dans CGI 2023 ---")
res_cgi = interroger_rapports(q, filtre_rapport="cgi-2023-esg-report-fr.pdf")
print("Réponse :", res_cgi['reponse'])
print("Sources :", [s['document'] for s in res_cgi['sources']])

print("\n--- TEST 2 : Recherche dans Solvay 2025 ---")
res_solvay = interroger_rapports(q, filtre_rapport="Solvay_Rapport-Annuel-Integre_2025.pdf")
print("Réponse :", res_solvay['reponse'])
print("Sources :", [s['document'] for s in res_solvay['sources']])

print("\n--- TEST 3 : Recherche Globale (Tous les rapports) ---")
res_global = interroger_rapports(q, filtre_rapport=None)
print("Réponse :", res_global['reponse'])
print("Sources :", [s['document'] for s in res_global['sources']])
