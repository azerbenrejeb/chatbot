"""
Script de test unitaire pour les 5 nouvelles fonctionnalités ESG.
Vérifie la conversion de valeurs, le calcul du score ESG global sur 100 et le comportement des nouveaux modules.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.compliance_checker import calculer_score_esg_global_100
from app.tendances_detector import clean_float

def test_clean_float():
    """Teste le nettoyage et la conversion de chaînes numériques."""
    print("\n========================================")
    print(" TEST 1 : Nettoyage de valeurs numériques")
    print("========================================")
    
    tests = [
        ("123", 123.0),
        ("12.3", 12.3),
        ("45 200 tCO2e", 45200.0),
        ("12,5 %", 12.5),
        ("  -8.4  ", -8.4),
        ("non numérique", None),
        (None, None),
    ]
    
    ok = 0
    for raw, expected in tests:
        res = clean_float(raw)
        status = "✅" if res == expected else f"❌ (obtenu: {res})"
        print(f"  '{raw}' → {expected} : {status}")
        if res == expected:
            ok += 1
            
    print(f"\n  Résultat : {ok}/{len(tests)} tests passés.")
    return ok == len(tests)

def test_score_esg_100_complet():
    """Teste le calcul du score global sur 100 avec toutes les dimensions."""
    print("\n=========================================")
    print(" TEST 2 : Score global sur 100 complet")
    print("=========================================")
    
    mock_conformite = {
        "dimensions": {
            "Environnemental": {
                "gri": {"score": 80.0, "trouves": ["GRI 302", "GRI 305"]}
            },
            "Social": {
                "gri": {"score": 100.0, "trouves": ["GRI 401"]}
            },
            "Gouvernance": {
                "gri": {"score": 50.0, "trouves": ["GRI 205"]}
            }
        }
    }
    
    res = calculer_score_esg_global_100(mock_conformite)
    
    # 80% de 40 = 32.0
    # 100% de 35 = 35.0
    # 50% de 25 = 12.5
    # Somme = 32.0 + 35.0 + 12.5 = 79.5
    print(f"  Score Env (attendu: 32.0) → {res['score_environnemental_100']}")
    print(f"  Score Soc (attendu: 35.0) → {res['score_social_100']}")
    print(f"  Score Gov (attendu: 12.5) → {res['score_gouvernance_100']}")
    print(f"  Score Global (attendu: 79.5) → {res['score_global_100']}")
    
    assert res["score_environnemental_100"] == 32.0
    assert res["score_social_100"] == 35.0
    assert res["score_gouvernance_100"] == 12.5
    assert res["score_global_100"] == 79.5
    assert len(res["dimensions_non_calculees"]) == 0
    print("  ✅ Tout est conforme pour le test complet.")
    return True

def test_score_esg_100_partiel():
    """Teste la redistribution des poids si une dimension n'est pas calculée."""
    print("\n==========================================")
    print(" TEST 3 : Score global partiel (non calculé)")
    print("==========================================")
    
    mock_conformite = {
        "dimensions": {
            "Environnemental": {
                "gri": {"score": 0.0, "trouves": []}  # Non calculé
            },
            "Social": {
                "gri": {"score": 75.0, "trouves": ["GRI 401"]}
            },
            "Gouvernance": {
                "gri": {"score": 50.0, "trouves": ["GRI 205"]}
            }
        }
    }
    
    res = calculer_score_esg_global_100(mock_conformite)
    
    # Env est exclu. Poids restants : Soc (35) et Gov (25) -> somme = 60
    # Nouveaux poids relatifs :
    # Soc : 35/60 * 100 = 58.33%
    # Gov : 25/60 * 100 = 41.67%
    # Scores sur 100 recalculés :
    # Soc : 75% de 58.33 = 43.75
    # Gov : 50% de 41.67 = 20.835 (arrondi à 20.84)
    # Total global : 43.75 + 20.84 = 64.59
    
    print(f"  Dimensions non calculées (attendu: ['Environnemental']) → {res['dimensions_non_calculees']}")
    print(f"  Score Env (attendu: None) → {res['score_environnemental_100']}")
    print(f"  Score Soc (attendu: 43.75) → {res['score_social_100']}")
    print(f"  Score Gov (attendu: 20.83 ou 20.84) → {res['score_gouvernance_100']}")
    print(f"  Score Global (attendu: ~64.58) → {res['score_global_100']}")
    
    assert "Environnemental" in res["dimensions_non_calculees"]
    assert res["score_environnemental_100"] is None
    assert abs(res["score_global_100"] - 64.58) <= 0.05
    print("  ✅ Tout est conforme pour le test partiel.")
    return True

if __name__ == "__main__":
    t1 = test_clean_float()
    t2 = test_score_esg_100_complet()
    t3 = test_score_esg_100_partiel()
    
    if t1 and t2 and t3:
        print("\n🏆 TOUS LES TESTS UNITAIRES ONT RÉUSSI !")
    else:
        print("\n❌ DES TESTS ONT ÉCHOUÉ.")
        sys.exit(1)
