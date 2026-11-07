from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

from src.chargement.csv_loader import _ouvrir_texte_robuste
from src.rapprochement.correspondance import extraire_jetons


@dataclass
class ProduitReference:
    produit_id: str
    nom: str
    categorie: str
    marque: str
    tokens: Set[str] = field(default_factory=set)


def charger_catalogue_reference(chemin_csv: Path) -> Dict[str, ProduitReference]:
    contenu = _ouvrir_texte_robuste(Path(chemin_csv))
    lignes_texte = [l for l in contenu.splitlines() if l.strip()]
    if not lignes_texte:
        return {}

    delimiteur = ";" if ";" in lignes_texte[0] and "," not in lignes_texte[0] else ","
    lecteur = csv.DictReader(lignes_texte, delimiter=delimiteur)
    catalogue: Dict[str, ProduitReference] = {}

    for ligne in lecteur:
        if not ligne:
            continue
        pid = str(ligne.get("produit_id") or "").strip()
        nom = str(ligne.get("nom") or "").strip()
        categorie = str(ligne.get("categorie") or "").strip()
        marque = str(ligne.get("marque") or "").strip()
        if not pid or not nom:
            continue
        catalogue[pid] = ProduitReference(
            produit_id=pid,
            nom=nom,
            categorie=categorie or "Non classé",
            marque=marque or "Inconnue",
            tokens=extraire_jetons(f"{nom} {marque}"),
        )
    return catalogue
