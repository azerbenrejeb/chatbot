"""
Référentiel des indicateurs ESG requis pour les standards GRI Standards 2021 et ESRS (CSRD).

Table de correspondance rigoureuse et enrichie entre les indicateurs GRI Standards 2021
et leurs équivalents CSRD/ESRS (EFRAG) pour les trois dimensions de la RSE (Environnemental, Social, Gouvernance).
Chaque indicateur spécifie le code GRI, la norme ESRS associée, l'intitulé officiel du Disclosure Requirement (DR),
l'unité standard de mesure et la description technique d'audit.
"""

INDICATEURS_REQUIS = {
    "Environnemental": {
        "energie": {
            "GRI": "GRI 302",
            "ESRS": "E1-5",
            "esrs_norme": "ESRS E1 Changement Climatique",
            "dr_titre": "Consommation et mix d'énergie",
            "unite_standard": "kWh / MWh / GJ",
            "description": "Consommation totale d'énergie, intensité énergétique et part des énergies renouvelables"
        },
        "eau": {
            "GRI": "GRI 303",
            "ESRS": "E3-1",
            "esrs_norme": "ESRS E3 Eau et Ressources Marines",
            "dr_titre": "Prélèvements et consommation d'eau",
            "unite_standard": "m³ / Litres",
            "description": "Gestion des prélèvements en zones de stress hydrique, consommation nette et rejets d'effluents"
        },
        "emissions": {
            "GRI": "GRI 305",
            "ESRS": "E1-6",
            "esrs_norme": "ESRS E1 Changement Climatique",
            "dr_titre": "Émissions brutes de GES (Scope 1, 2 et 3)",
            "unite_standard": "tCO₂e",
            "description": "Bilan carbone consolidé : émissions directes (Scope 1), indirectes liées à l'énergie (Scope 2) et chaîne de valeur (Scope 3)"
        },
        "dechets": {
            "GRI": "GRI 306",
            "ESRS": "E5-5",
            "esrs_norme": "ESRS E5 Utilisation des ressources et économie circulaire",
            "dr_titre": "Production et valorisation des flux de déchets",
            "unite_standard": "Tonnes / % recyclage",
            "description": "Production totale de déchets dangereux et non dangereux, valorisation matière et taux d'économie circulaire"
        },
    },
    "Social": {
        "emploi": {
            "GRI": "GRI 401",
            "ESRS": "S1-6",
            "esrs_norme": "ESRS S1 Main-d'œuvre de l'entreprise",
            "dr_titre": "Caractéristiques des effectifs et rotation",
            "unite_standard": "Nombre de salariés (ETP) / % turnover",
            "description": "Effectif consolidé, ventilation par type de contrat (CDI/CDD), embauches, départs et taux de rotation du personnel"
        },
        "sante_securite": {
            "GRI": "GRI 403",
            "ESRS": "S1-14",
            "esrs_norme": "ESRS S1 Main-d'œuvre de l'entreprise",
            "dr_titre": "Indicateurs de santé et sécurité au travail",
            "unite_standard": "Taux de fréquence (TF) / Taux de gravité (TG)",
            "description": "Couverture du système SST, taux de fréquence des accidents avec arrêt, taux de gravité et politique de prévention"
        },
        "formation": {
            "GRI": "GRI 404",
            "ESRS": "S1-13",
            "esrs_norme": "ESRS S1 Main-d'œuvre de l'entreprise",
            "dr_titre": "Formation et développement des compétences",
            "unite_standard": "Heures de formation / Heures par collaborateur",
            "description": "Volume annuel d'heures de formation dispensées, moyenne par salarié et programmes d'upskilling/reskilling"
        },
        "diversite": {
            "GRI": "GRI 405",
            "ESRS": "S1-9",
            "esrs_norme": "ESRS S1 Main-d'œuvre de l'entreprise",
            "dr_titre": "Diversité des effectifs et parité dans la gouvernance",
            "unite_standard": "% femmes total / % femmes direction",
            "description": "Part des femmes dans l'effectif global, part dans les instances dirigeantes, index égalité et inclusion des travailleurs en situation de handicap"
        },
    },
    "Gouvernance": {
        "anti_corruption": {
            "GRI": "GRI 205",
            "ESRS": "G1-3",
            "esrs_norme": "ESRS G1 Conduite des affaires",
            "dr_titre": "Prévention, détection et lutte contre la corruption",
            "unite_standard": "Dispositif actif / % formés",
            "description": "Code de conduite des affaires, cartographie des risques de corruption, formation des équipes exposées et dispositif d'alerte éthique"
        },
        "concurrence": {
            "GRI": "GRI 206",
            "ESRS": "G1-1",
            "esrs_norme": "ESRS G1 Conduite des affaires",
            "dr_titre": "Culture d'entreprise et conformité au droit de la concurrence",
            "unite_standard": "Politique formelle / Nombre de litiges",
            "description": "Politique de respect des règles antitrust et de concurrence loyale, prévention des ententes et des abus de position dominante"
        },
        "politiques_publiques": {
            "GRI": "GRI 415",
            "ESRS": "G1-5",
            "esrs_norme": "ESRS G1 Conduite des affaires",
            "dr_titre": "Activités de lobbying et engagement politique",
            "unite_standard": "Montant dépenses (€) / Déclaration transparence",
            "description": "Transparence des contributions aux partis politiques, dépenses déclarées au registre de transparence et activités de représentation d'intérêts"
        },
        "conformite": {
            "GRI": "GRI 419",
            "ESRS": "G1-4",
            "esrs_norme": "ESRS G1 Conduite des affaires",
            "dr_titre": "Conformité socio-économique et sanctions réglementaires",
            "unite_standard": "Nombre d'amendes / Montant total (€)",
            "description": "Amendes significatives infligées pour non-conformité aux lois et règlements environnementaux, sociaux ou économiques"
        },
    }
}

