from __future__ import annotations

from collections import defaultdict
import heapq
from typing import Dict, List, Optional, Tuple

from src.analyse.comparateur import ENSEIGNES
from src.nettoyage.nettoyeur import nettoyer_prix_texte
from src.rapprochement.catalogue import ProduitReference

DEBUT_BLACK_FRIDAY = "2025-11-24"
FIN_BLACK_FRIDAY = "2025-11-30"


def analyser_historique(
    lignes_historique: List[Dict[str, str]],
    catalogue: Optional[Dict[str, ProduitReference]] = None,
) -> Dict[str, object]:
    prix_annuels_ens: Dict[str, List[int]] = defaultdict(list)
    prix_bf_ens: Dict[str, List[int]] = defaultdict(list)
    prix_annuels_prod: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    prix_bf_prod: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    prix_par_jour: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    prix_par_mois: Dict[Tuple[str, str], List[int]] = defaultdict(list)

    nb_lignes_valides = 0
    for r in lignes_historique or []:
        if not isinstance(r, dict):
            continue
        ens = str(r.get("source") or "").strip()
        pid = str(r.get("produit_id") or "").strip()
        date_str = str(r.get("date") or "").strip()
        px = nettoyer_prix_texte(r.get("prix_fcfa"))
        if not ens or not pid or len(date_str) < 10 or px is None:
            continue

        nb_lignes_valides += 1
        prix_annuels_ens[ens].append(px)
        prix_annuels_prod[(ens, pid)].append(px)
        prix_par_jour[(ens, date_str[:10])].append(px)
        prix_par_mois[(ens, date_str[:7])].append(px)

        if DEBUT_BLACK_FRIDAY <= date_str[:10] <= FIN_BLACK_FRIDAY:
            prix_bf_ens[ens].append(px)
            prix_bf_prod[(ens, pid)].append(px)

    par_enseigne: Dict[str, Dict[str, object]] = {}
    lignes_detail_csv: List[Dict[str, object]] = []

    for ens in ENSEIGNES:
        vals_ens_an = prix_annuels_ens.get(ens, [])
        vals_ens_bf = prix_bf_ens.get(ens, [])
        moy_an_globale = sum(vals_ens_an) / len(vals_ens_an) if vals_ens_an else 0.0
        moy_bf_globale = sum(vals_ens_bf) / len(vals_ens_bf) if vals_ens_bf else 0.0
        ecart_global_fcfa = moy_bf_globale - moy_an_globale
        ecart_global_pct = (
            (ecart_global_fcfa / moy_an_globale) * 100.0 if moy_an_globale > 0 else 0.0
        )

        produits_ens = sorted({pid for (s, pid) in prix_annuels_prod if s == ens})
        ecarts_produits_pct: List[float] = []
        nb_produits_promo = 0

        for pid in produits_ens:
            vals_an = prix_annuels_prod[(ens, pid)]
            vals_bf = prix_bf_prod.get((ens, pid), [])
            if not vals_an:
                continue
            m_an = sum(vals_an) / len(vals_an)
            m_bf = sum(vals_bf) / len(vals_bf) if vals_bf else m_an
            diff_fcfa = m_bf - m_an
            diff_pct = (diff_fcfa / m_an) * 100.0 if m_an > 0 else 0.0
            ecarts_produits_pct.append(diff_pct)
            if m_bf < m_an:
                nb_produits_promo += 1

            nom_prod = catalogue[pid].nom if (catalogue and pid in catalogue) else pid
            lignes_detail_csv.append(
                {
                    "enseigne": ens,
                    "produit_id": pid,
                    "nom": nom_prod,
                    "nb_releves_annee": len(vals_an),
                    "prix_moyen_annuel_fcfa": round(m_an),
                    "prix_moyen_black_friday_fcfa": round(m_bf),
                    "ecart_bf_fcfa": round(diff_fcfa),
                    "ecart_bf_pct": round(diff_pct, 2),
                    "prix_min_annuel_fcfa": min(vals_an),
                    "prix_max_annuel_fcfa": max(vals_an),
                }
            )

        jours_ens = [
            (sum(vals) / len(vals), d)
            for (s, d), vals in prix_par_jour.items()
            if s == ens and vals
        ]
        meilleurs_jours = heapq.nsmallest(3, jours_ens) if jours_ens else [(0.0, "N/A")]

        mois_ens = [
            (sum(vals) / len(vals), m)
            for (s, m), vals in prix_par_mois.items()
            if s == ens and vals
        ]
        meilleur_mois = min(mois_ens) if mois_ens else (0.0, "N/A")

        par_enseigne[ens] = {
            "nb_lignes": len(vals_ens_an),
            "moyenne_annuelle": moy_an_globale,
            "moyenne_bf": moy_bf_globale,
            "ecart_global_fcfa": ecart_global_fcfa,
            "ecart_global_pct": ecart_global_pct,
            "ecart_moyen_par_produit_pct": (
                sum(ecarts_produits_pct) / len(ecarts_produits_pct)
                if ecarts_produits_pct
                else 0.0
            ),
            "nb_produits_promo": nb_produits_promo,
            "nb_produits_total": len(produits_ens),
            "meilleur_jour": meilleurs_jours[0],
            "top3_jours": meilleurs_jours,
            "meilleur_mois": meilleur_mois,
        }

    return {
        "nb_total_lignes": nb_lignes_valides,
        "par_enseigne": par_enseigne,
        "lignes_detail_csv": lignes_detail_csv,
    }
