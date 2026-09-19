"""
Script de test du module de conformité ESG multi-standards (GRI & ESRS).
Simule différentes configurations d'indicateurs et vérifie les calculs.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.compliance_checker import (
    normaliser_reference,
    calculer_score_conformite,
    generer_resume_conformite_textuel
)


def test_normalisation():
    """Teste la normalisation des codes GRI et ESRS."""
    print("\n========================================")
    print(" TEST 1 : Normalisation des références")
    print("========================================")

    tests = [
        ("GRI 305-1", "GRI 305"),
        ("GRI305", "GRI 305"),
        ("gri 302", "GRI 302"),
        ("GRI-403", "GRI 403"),
        ("305-2", "GRI 305"),
        ("E1-5", "E1-5"),
        ("e1-6", "E1-6"),
        ("S1-14", "S1-14"),
        ("G1-3", "G1-3"),
    ]

    ok = 0
    for raw, expected in tests:
        result = normaliser_reference(raw)
        status = "✅" if result == expected else f"❌ (obtenu: {result})"
        print(f"  '{raw}' → '{expected}' {status}")
        if result == expected:
            ok += 1

    print(f"\n  Résultat: {ok}/{len(tests)} tests passés.")
    return ok == len(tests)


def test_score_rapport_vide():
    """Teste le comportement avec un rapport vide (0 indicateur trouvé)."""
    print("\n==========================================")
    print(" TEST 2 : Rapport vide (0 indicateurs)")
    print("==========================================")

    references = set()
    result = calculer_score_conformite(references)

    assert result["score_global_gri"] == 0.0, "Score GRI doit être 0%"
    assert result["score_global_esrs"] == 0.0, "Score ESRS doit être 0%"
    assert result["score_global_combine"] == 0.0, "Score combiné doit être 0%"

    for dim in ["Environnemental", "Social", "Gouvernance"]:
        assert result["dimensions"][dim]["gri"]["score"] == 0.0
        assert result["dimensions"][dim]["esrs"]["score"] == 0.0

    print("  ✅ Rapport vide : Tous les scores sont bien à 0%")
    return True


def test_score_partiel():
    """Teste le calcul de score avec des références GRI partielles."""
    print("\n=================================================")
    print(" TEST 3 : Score partiel (indicateurs GRI seuls)")
    print("=================================================")

    # Suppose GRI 302, GRI 305 présents en Environnemental → 50%
    # Suppose GRI 401, GRI 403 présents en Social → 50%
    # Suppose GRI 205 présent en Gouvernance → 25%
    references = {"GRI 302", "GRI 305", "GRI 401", "GRI 403", "GRI 205"}
    result = calculer_score_conformite(references)

    env_gri = result["dimensions"]["Environnemental"]["gri"]["score"]
    soc_gri = result["dimensions"]["Social"]["gri"]["score"]
    gov_gri = result["dimensions"]["Gouvernance"]["gri"]["score"]
    global_gri = result["score_global_gri"]

    print(f"  Score GRI Environnemental : {env_gri}% (attendu: 50.0%)")
    print(f"  Score GRI Social          : {soc_gri}% (attendu: 50.0%)")
    print(f"  Score GRI Gouvernance     : {gov_gri}% (attendu: 25.0%)")
    print(f"  Score GRI Global          : {global_gri}% (attendu: 41.7%)")

    env_ok = abs(env_gri - 50.0) < 0.2
    soc_ok = abs(soc_gri - 50.0) < 0.2
    gov_ok = abs(gov_gri - 25.0) < 0.2
    global_ok = abs(global_gri - 41.7) < 0.2

    all_ok = env_ok and soc_ok and gov_ok and global_ok
    print(f"  {'✅ Tous les scores corrects!' if all_ok else '❌ Scores incorrects'}")
    return all_ok


def test_score_complet():
    """Teste le calcul avec tous les indicateurs présents (100% conformité)."""
    print("\n=================================================")
    print(" TEST 4 : Conformité totale (100% GRI & ESRS)")
    print("=================================================")

    references = {
        # Environnemental GRI
        "GRI 302", "GRI 303", "GRI 305", "GRI 306",
        # Social GRI
        "GRI 401", "GRI 403", "GRI 404", "GRI 405",
        # Gouvernance GRI
        "GRI 205", "GRI 206", "GRI 415", "GRI 419",
    }
    result = calculer_score_conformite(references)

    gri_global = result["score_global_gri"]
    esrs_global = result["score_global_esrs"]

    print(f"  Score GRI global   : {gri_global}% (attendu: 100.0%)")
    print(f"  Score ESRS global  : {esrs_global}% (attendu: 100.0% car mapping GRI-ESRS activé)")

    gri_ok = abs(gri_global - 100.0) < 0.1
    esrs_ok = abs(esrs_global - 100.0) < 0.1

    all_ok = gri_ok and esrs_ok
    print(f"  {'✅ Conformité totale validée!' if all_ok else '❌ Conformité incorrecte'}")
    return all_ok


def test_resume_textuel():
    """Teste la génération du texte de résumé de conformité."""
    print("\n==============================================")
    print(" TEST 5 : Génération du résumé textuel")
    print("==============================================")

    references = {"GRI 302", "GRI 305", "GRI 401"}
    result = calculer_score_conformite(references)
    resume = generer_resume_conformite_textuel(result)

    checks = [
        "RAPPORT DE CONFORMITÉ ESG" in resume,
        "Score global GRI" in resume,
        "Score global ESRS" in resume,
        "Environnemental" in resume,
        "Social" in resume,
        "Gouvernance" in resume,
    ]

    print(f"  Longueur du résumé : {len(resume)} caractères")
    print(f"  Extraits du résumé :")
    for line in resume.split("\n")[:6]:
        print(f"    {line}")
    print(f"  ...")

    all_ok = all(checks)
    print(f"  {'✅ Résumé bien formé!' if all_ok else '❌ Résumé incomplet ou mal formé'}")
    return all_ok


def test_manquants():
    """Teste la liste des indicateurs manquants pour un rapport partiel."""
    print("\n===================================================")
    print(" TEST 6 : Identification des indicateurs manquants")
    print("===================================================")

    # Seulement GRI 302 présent en Environnemental → 3 GRI manquants
    references = {"GRI 302"}
    result = calculer_score_conformite(references)

    env_gri_manquants = result["dimensions"]["Environnemental"]["gri"]["manquants"]
    manquant_codes = [m["code"] for m in env_gri_manquants]

    expected_missing = {"GRI 303", "GRI 305", "GRI 306"}
    ok = expected_missing == set(manquant_codes)

    print(f"  Indicateurs GRI manquants en Environnemental : {manquant_codes}")
    print(f"  Attendu : {sorted(expected_missing)}")
    print(f"  {'✅ Correct!' if ok else '❌ Incorrect'}")
    return ok


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print(" TESTS DU MODULE DE CONFORMITÉ ESG (GRI & ESRS)")
    print("=" * 55)

    tests = [
        test_normalisation,
        test_score_rapport_vide,
        test_score_partiel,
        test_score_complet,
        test_resume_textuel,
        test_manquants,
    ]

    resultats = []
    for test_fn in tests:
        try:
            ok = test_fn()
            resultats.append((test_fn.__name__, ok))
        except Exception as e:
            print(f"  ❌ ERREUR EXCEPTION: {e}")
            resultats.append((test_fn.__name__, False))

    print("\n" + "=" * 55)
    print(" RÉSUMÉ DES TESTS")
    print("=" * 55)
    for name, ok in resultats:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    passed = sum(1 for _, ok in resultats if ok)
    total = len(resultats)
    print(f"\n  Score final : {passed}/{total} tests réussis.")
    if passed == total:
        print("  🎉 Tous les tests sont passés avec succès !")
    else:
        print("  ⚠️  Certains tests ont échoué. Vérifier le module de conformité.")
    print()
