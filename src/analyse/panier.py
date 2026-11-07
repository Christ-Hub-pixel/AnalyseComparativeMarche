from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from src.analyse.comparateur import ENSEIGNES
from src.nettoyage.nettoyeur import OffreEnseigne


PANIER_RENTREE: List[Tuple[str, str, int]] = [
    ("P04", "Tecno Spark 20 128 Go", 1),
    ("P12", "Lenovo IdeaPad 3 Core i3 8 Go 256 Go", 1),
    ("P14", "Clé USB SanDisk 64 Go", 2),
    ("P15", "Disque dur externe Seagate 1 To", 1),
    ("P28", "Micro-ondes Samsung 23 L", 1),
]


def evaluer_panier(
    index_offres: Dict[str, Dict[str, OffreEnseigne]],
    composition_panier: Optional[List[Tuple[str, str, int]]] = None,
) -> Dict[str, object]:
    articles_bruts = composition_panier if composition_panier is not None else PANIER_RENTREE
    articles_panier: List[Tuple[str, str, int]] = []
    for entree in articles_bruts or []:
        if not isinstance(entree, (tuple, list)) or len(entree) < 3:
            continue
        pid = str(entree[0] or "").strip()
        nom = str(entree[1] or pid).strip()
        try:
            qte = int(entree[2])
        except (ValueError, TypeError):
            continue
        if pid and qte > 0:
            articles_panier.append((pid, nom, qte))

    par_enseigne: Dict[str, Dict[str, object]] = {}

    for ens in ENSEIGNES:
        total = 0
        complet = bool(articles_panier)
        articles_manquants: List[str] = []
        details = []

        for pid, nom, qte in articles_panier:
            offre = (index_offres or {}).get(pid, {}).get(ens)
            if offre and offre.exploitable and offre.prix_paye is not None and offre.prix_paye > 0:
                sous_total = int(offre.prix_paye) * qte
                total += sous_total
                details.append(
                    {
                        "produit_id": pid,
                        "nom": nom,
                        "quantite": qte,
                        "prix_unitaire": int(offre.prix_paye),
                        "sous_total": sous_total,
                    }
                )
            else:
                complet = False
                articles_manquants.append(pid)
                details.append(
                    {
                        "produit_id": pid,
                        "nom": nom,
                        "quantite": qte,
                        "prix_unitaire": None,
                        "sous_total": None,
                    }
                )

        par_enseigne[ens] = {
            "complet": complet,
            "total": total if complet else None,
            "total_partiel": total,
            "articles_manquants": articles_manquants,
            "details": details,
        }

    total_optimal = 0
    optimal_complet = bool(articles_panier)
    details_optimal = []
    for pid, nom, qte in articles_panier:
        offres_dispo = {
            ens: int(off.prix_paye)
            for ens, off in (index_offres or {}).get(pid, {}).items()
            if off and off.exploitable and off.prix_paye is not None and off.prix_paye > 0
        }
        if not offres_dispo:
            optimal_complet = False
            details_optimal.append(
                {
                    "produit_id": pid,
                    "nom": nom,
                    "quantite": qte,
                    "enseigne": "Aucune (rupture totale)",
                    "prix_unitaire": None,
                    "sous_total": None,
                }
            )
            continue
        meilleure_ens = min(offres_dispo, key=offres_dispo.get)
        prix_unitaire = offres_dispo[meilleure_ens]
        sous_total = prix_unitaire * qte
        total_optimal += sous_total
        details_optimal.append(
            {
                "produit_id": pid,
                "nom": nom,
                "quantite": qte,
                "enseigne": meilleure_ens,
                "prix_unitaire": prix_unitaire,
                "sous_total": sous_total,
            }
        )

    return {
        "par_enseigne": par_enseigne,
        "optimal_complet": optimal_complet,
        "optimal_total": total_optimal,
        "optimal_details": details_optimal,
    }
