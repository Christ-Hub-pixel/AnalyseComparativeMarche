from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.chargement.csv_loader import _ouvrir_texte_robuste
from src.nettoyage.journal import JournalNettoyage
from src.nettoyage.nettoyeur import OffreEnseigne, nettoyer_offres_baobab_shop


def lire_json_baobab_brut(
    chemin_json: Path, journal: Optional[JournalNettoyage] = None
) -> List[Dict[str, object]]:
    contenu = _ouvrir_texte_robuste(Path(chemin_json))
    try:
        donnees = json.loads(contenu)
    except json.JSONDecodeError as err:
        raise ValueError(f"Fichier JSON invalide ({chemin_json}) : {err}") from err

    if journal is not None:
        journal.ajouter(
            enseigne="Baobab Shop",
            reference="Fichier JSON",
            type_anomalie="Noms en anglais & Livraison séparée",
            description=(
                "Les désignations sont en anglais ('Fridge', 'Steam Iron', '1HP'...) "
                "et les frais de livraison ('delivery_fee') sont séparés de 'amount'."
            ),
            action_prise="Traduction/normalisation des termes anglais et calcul prix_paye = amount + delivery_fee.",
        )

    if isinstance(donnees, dict):
        items = donnees.get("items", [])
        return [x for x in items if isinstance(x, dict)] if isinstance(items, list) else []
    if isinstance(donnees, list):
        return [x for x in donnees if isinstance(x, dict)]
    return []


def charger_baobab_shop(
    chemin_json: Path, journal: JournalNettoyage
) -> List[OffreEnseigne]:
    articles_bruts = lire_json_baobab_brut(chemin_json, journal=journal)
    return nettoyer_offres_baobab_shop(articles_bruts, journal=journal)
