from __future__ import annotations

import heapq
from typing import Dict, List

from src.analyse.comparateur import ENSEIGNES


def calculer_synthese(lignes_comparatif: List[Dict[str, object]]) -> Dict[str, object]:
    victoires: Dict[str, int] = {ens: 0 for ens in ENSEIGNES}
    ecarts_fcfa_par_ens: Dict[str, List[int]] = {ens: [] for ens in ENSEIGNES}
    ecarts_pct_par_ens: Dict[str, List[float]] = {ens: [] for ens in ENSEIGNES}

    for ligne in lignes_comparatif or []:
        if not isinstance(ligne, dict):
            continue
        prix_min = int(ligne.get("prix_min") or 0)
        if prix_min <= 0:
            continue

        for ens in ligne.get("meilleures_liste") or []:
            if ens in victoires:
                victoires[ens] += 1

        prix_par_ens = ligne.get("prix_par_enseigne")
        if isinstance(prix_par_ens, dict):
            for ens, prix in prix_par_ens.items():
                if ens in ecarts_fcfa_par_ens and prix is not None:
                    ecart_abs = int(prix) - prix_min
                    ecart_rel = (ecart_abs / prix_min) * 100.0
                    ecarts_fcfa_par_ens[ens].append(ecart_abs)
                    ecarts_pct_par_ens[ens].append(ecart_rel)

    ecart_moyen: Dict[str, Dict[str, float]] = {}
    for ens in ENSEIGNES:
        nb = len(ecarts_fcfa_par_ens[ens])
        ecart_moyen[ens] = {
            "nb_produits_dispo": float(nb),
            "ecart_moyen_fcfa": sum(ecarts_fcfa_par_ens[ens]) / nb if nb > 0 else 0.0,
            "ecart_moyen_pct": sum(ecarts_pct_par_ens[ens]) / nb if nb > 0 else 0.0,
        }

    lignes_valides = [l for l in (lignes_comparatif or []) if isinstance(l, dict) and "ecart_fcfa" in l]
    top3_fcfa = heapq.nlargest(3, lignes_valides, key=lambda r: float(r.get("ecart_fcfa") or 0.0))
    top3_pct = heapq.nlargest(3, lignes_valides, key=lambda r: float(r.get("ecart_pct") or 0.0))

    return {
        "nb_produits_compares": len(lignes_valides),
        "victoires": victoires,
        "ecart_moyen": ecart_moyen,
        "top3_fcfa": top3_fcfa,
        "top3_pct": top3_pct,
    }
