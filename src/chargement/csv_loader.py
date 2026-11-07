from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from src.nettoyage.journal import JournalNettoyage
from src.nettoyage.nettoyeur import OffreEnseigne, nettoyer_offres_marche_lagune, nettoyer_prix_texte


def _ouvrir_texte_robuste(chemin_fichier: Path) -> str:
    chemin = Path(chemin_fichier)
    if not chemin.exists() or not chemin.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")
    donnees_octets = chemin.read_bytes()
    for encodage in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return donnees_octets.decode(encodage)
        except UnicodeDecodeError:
            continue
    return donnees_octets.decode("utf-8", errors="replace")


def lire_csv_marche_lagune_brut(
    chemin_csv: Path, journal: Optional[JournalNettoyage] = None
) -> List[Dict[str, str]]:
    chemin = Path(chemin_csv)
    if not chemin.exists() or not chemin.is_file():
        raise FileNotFoundError(f"Fichier CSV introuvable : {chemin}")

    if journal is not None:
        with open(chemin, "rb") as fb:
            if fb.read(3) == b"\xef\xbb\xbf":
                journal.ajouter(
                    enseigne="Marché Lagune",
                    reference="Fichier CSV",
                    type_anomalie="Encodage BOM UTF-8 & Format FR",
                    description=(
                        "Présence d'un BOM UTF-8 (\\ufeff), séparateur ';', virgule décimale "
                        "et espaces insécables (\\u202f) dans les prix."
                    ),
                    action_prise="Lecture avec encoding='utf-8-sig', delimiter=';' et nettoyage regex.",
                )

    contenu = _ouvrir_texte_robuste(chemin)
    lignes_texte = [l for l in contenu.splitlines() if l.strip()]
    if not lignes_texte:
        return []

    delimiteur = ";" if ";" in lignes_texte[0] else ","
    lecteur = csv.DictReader(lignes_texte, delimiter=delimiteur)
    lignes_normalisees: List[Dict[str, str]] = []
    for ligne in lecteur:
        if not ligne:
            continue
        propre = {
            str(cle).strip().lower(): (str(val) if val is not None else "")
            for cle, val in ligne.items()
            if cle is not None
        }
        if any(v.strip() for v in propre.values()):
            lignes_normalisees.append(propre)
    return lignes_normalisees


def charger_marche_lagune(
    chemin_csv: Path,
    journal: JournalNettoyage,
    corriger_prix_aberrant: bool = False,
) -> List[OffreEnseigne]:
    lignes_brutes = lire_csv_marche_lagune_brut(chemin_csv, journal=journal)
    return nettoyer_offres_marche_lagune(
        lignes_brutes, journal=journal, corriger_prix_aberrant=corriger_prix_aberrant
    )


def charger_historique_csv(chemin_csv: Path) -> List[Dict[str, str]]:
    contenu = _ouvrir_texte_robuste(Path(chemin_csv))
    lignes_texte = [l for l in contenu.splitlines() if l.strip()]
    if not lignes_texte:
        return []

    delimiteur = ";" if ";" in lignes_texte[0] and "," not in lignes_texte[0] else ","
    lecteur = csv.DictReader(lignes_texte, delimiter=delimiteur)
    lignes_valides: List[Dict[str, str]] = []

    for ligne in lecteur:
        if not ligne:
            continue
        date_str = str(ligne.get("date") or "").strip()
        source_str = str(ligne.get("source") or "").strip()
        pid_str = str(ligne.get("produit_id") or "").strip()
        prix_val = nettoyer_prix_texte(ligne.get("prix_fcfa"))
        if len(date_str) >= 10 and source_str and pid_str and prix_val is not None:
            lignes_valides.append(
                {
                    "date": date_str[:10],
                    "source": source_str,
                    "produit_id": pid_str,
                    "prix_fcfa": str(prix_val),
                }
            )
    return lignes_valides
