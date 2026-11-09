from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def exporter_comparatif_csv(
    lignes_comparatif: List[Dict[str, object]], chemin_sortie: Path
) -> None:
    chemin = Path(chemin_sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    colonnes = [
        "produit_id",
        "nom",
        "categorie",
        "prix_marche_lagune_fcfa",
        "prix_baobab_shop_fcfa",
        "prix_comptoir_ivoire_fcfa",
        "enseigne_moins_chere",
        "prix_min_fcfa",
        "prix_max_fcfa",
        "ecart_fcfa",
        "ecart_pct",
    ]
    with open(chemin, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes)
        writer.writeheader()
        for l in lignes_comparatif or []:
            if not isinstance(l, dict):
                continue
            ecart_pct_val = float(l.get("ecart_pct") or 0.0)
            writer.writerow(
                {
                    "produit_id": l.get("produit_id", ""),
                    "nom": l.get("nom", ""),
                    "categorie": l.get("categorie", ""),
                    "prix_marche_lagune_fcfa": (
                        l.get("prix_marche_lagune")
                        if l.get("prix_marche_lagune") is not None
                        else "Indisponible"
                    ),
                    "prix_baobab_shop_fcfa": (
                        l.get("prix_baobab_shop")
                        if l.get("prix_baobab_shop") is not None
                        else "Indisponible"
                    ),
                    "prix_comptoir_ivoire_fcfa": (
                        l.get("prix_comptoir_ivoire")
                        if l.get("prix_comptoir_ivoire") is not None
                        else "Indisponible"
                    ),
                    "enseigne_moins_chere": l.get("meilleure_enseigne", ""),
                    "prix_min_fcfa": l.get("prix_min", ""),
                    "prix_max_fcfa": l.get("prix_max", ""),
                    "ecart_fcfa": l.get("ecart_fcfa", ""),
                    "ecart_pct": f"{ecart_pct_val:.2f}",
                }
            )


def exporter_historique_csv(
    lignes_detail_hist: List[Dict[str, object]], chemin_sortie: Path
) -> None:
    chemin = Path(chemin_sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    colonnes = [
        "enseigne",
        "produit_id",
        "nom",
        "nb_releves_annee",
        "prix_moyen_annuel_fcfa",
        "prix_moyen_black_friday_fcfa",
        "ecart_bf_fcfa",
        "ecart_bf_pct",
        "prix_min_annuel_fcfa",
        "prix_max_annuel_fcfa",
    ]
    with open(chemin, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, extrasaction="ignore")
        writer.writeheader()
        for l in lignes_detail_hist or []:
            if isinstance(l, dict):
                writer.writerow(l)
