"""
Référentiel des indicateurs ESG requis pour les standards GRI Standards 2021 et ESRS (CSRD).

Ce fichier contient la table de correspondance simplifiée entre les indicateurs GRI
et leurs équivalents ESRS pour les trois dimensions de la RSE (E, S, G).
Note : Ce mapping est une simplification pédagogique pour le PFE. La correspondance
officielle complète est plus détaillée et ce mapping couvre les indicateurs les plus courants.
"""

INDICATEURS_REQUIS = {
    "Environnemental": {
        "energie": {
            "GRI": "GRI 302",
            "ESRS": "E1-5",
            "description": "Consommation et intensité énergétique"
        },
        "eau": {
            "GRI": "GRI 303",
            "ESRS": "E3-1",
            "description": "Gestion de l'eau et des effluents"
        },
        "emissions": {
            "GRI": "GRI 305",
            "ESRS": "E1-6",
            "description": "Émissions de GES (Scope 1, 2, 3)"
        },
        "dechets": {
            "GRI": "GRI 306",
            "ESRS": "E5-5",
            "description": "Déchets et économie circulaire"
        },
    },
    "Social": {
        "emploi": {
            "GRI": "GRI 401",
            "ESRS": "S1-6",
            "description": "Caractéristiques des effectifs"
        },
        "sante_securite": {
            "GRI": "GRI 403",
            "ESRS": "S1-14",
            "description": "Santé et sécurité au travail"
        },
        "formation": {
            "GRI": "GRI 404",
            "ESRS": "S1-13",
            "description": "Formation et développement des compétences"
        },
        "diversite": {
            "GRI": "GRI 405",
            "ESRS": "S1-9",
            "description": "Diversité des effectifs et des organes de gouvernance"
        },
    },
    "Gouvernance": {
        "anti_corruption": {
            "GRI": "GRI 205",
            "ESRS": "G1-3",
            "description": "Prévention et détection de la corruption"
        },
        "concurrence": {
            "GRI": "GRI 206",
            "ESRS": "G1-1",
            "description": "Conduite des affaires et concurrence loyale"
        },
        "politiques_publiques": {
            "GRI": "GRI 415",
            "ESRS": "G1-5",
            "description": "Engagement politique et lobbying"
        },
        "conformite": {
            "GRI": "GRI 419",
            "ESRS": "G1-4",
            "description": "Conformité socio-économique et incidents"
        },
    }
}
