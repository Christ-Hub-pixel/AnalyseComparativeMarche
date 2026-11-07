from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from src.nettoyage.nettoyeur import OffreEnseigne
from src.rapprochement.catalogue import ProduitReference

ENSEIGNES = ["Marché Lagune", "Baobab Shop", "Comptoir Ivoire"]


def construire_index_offres(
    offres: List[OffreEnseigne],
) -> Dict[str, Dict[str, OffreEnseigne]]:
    index: Dict[str, Dict[str, OffreEnseigne]] = defaultdict(dict)
    for offre in offres or []:
        if isinstance(offre, OffreEnseigne) and offre.produit_id and offre.enseigne:
            index[offre.produit_id][offre.enseigne] = offre
    return index


def comparer_produits(
    catalogue: Dict[str, ProduitReference],
    index_offres: Dict[str, Dict[str, OffreEnseigne]],
) -> List[Dict[str, object]]:
    lignes_comparatif: List[Dict[str, object]] = []
    if not catalogue or not index_offres:
        return lignes_comparatif

    for pid in sorted(catalogue.keys()):
        prod = catalogue[pid]
        offres_prod = index_offres.get(pid, {})

        prix_valides: Dict[str, int] = {
            ens: int(off.prix_paye)
            for ens, off in offres_prod.items()
            if off is not None and off.exploitable and off.prix_paye is not None and off.prix_paye > 0
        }

        if len(prix_valides) < 2:
            continue

        prix_min = min(prix_valides.values())
        prix_max = max(prix_valides.values())
        prix_moyen = round(sum(prix_valides.values()) / len(prix_valides))
        ecart_fcfa = prix_max - prix_min
        ecart_pct = round((ecart_fcfa / prix_min) * 100.0, 2) if prix_min > 0 else 0.0

        moins_cheres = [ens for ens, p in prix_valides.items() if p == prix_min]
        meilleure_enseigne = " / ".join(moins_cheres)

        lignes_comparatif.append(
            {
                "produit_id": pid,
                "nom": prod.nom,
                "categorie": prod.categorie,
                "marque": prod.marque,
                "prix_marche_lagune": prix_valides.get("Marché Lagune"),
                "prix_baobab_shop": prix_valides.get("Baobab Shop"),
                "prix_comptoir_ivoire": prix_valides.get("Comptoir Ivoire"),
                "nb_enseignes_dispo": len(prix_valides),
                "meilleure_enseigne": meilleure_enseigne,
                "meilleures_liste": moins_cheres,
                "prix_min": prix_min,
                "prix_max": prix_max,
                "prix_moyen": prix_moyen,
                "ecart_fcfa": ecart_fcfa,
                "ecart_pct": ecart_pct,
                "prix_par_enseigne": prix_valides,
            }
        )

    return lignes_comparatif
