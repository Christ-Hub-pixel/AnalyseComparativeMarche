from __future__ import annotations

from collections import defaultdict
import time
from typing import Dict, List, Tuple

from src.analyse.comparateur import ENSEIGNES
from src.analyse.historique import DEBUT_BLACK_FRIDAY, FIN_BLACK_FRIDAY
from src.nettoyage.nettoyeur import nettoyer_prix_texte


def mesurer_performances(lignes_historique: List[Dict[str, str]]) -> Dict[str, float]:
    lignes_propres: List[Dict[str, str]] = []
    for r in lignes_historique or []:
        if not isinstance(r, dict):
            continue
        s = str(r.get("source") or "").strip()
        p = str(r.get("produit_id") or "").strip()
        d = str(r.get("date") or "").strip()
        px = nettoyer_prix_texte(r.get("prix_fcfa"))
        if s and p and len(d) >= 10 and px is not None:
            lignes_propres.append(
                {"source": s, "produit_id": p, "date": d[:10], "prix_fcfa": str(px)}
            )

    if not lignes_propres:
        return {
            "nb_lignes": 0.0,
            "nb_requetes": 0.0,
            "temps_naif_ms": 0.0,
            "temps_opt_ms": 0.0,
            "facteur_gain": 0.0,
            "temps_lookup_liste_us": 0.0,
            "temps_lookup_dict_us": 0.0,
            "facteur_gain_lookup": 0.0,
        }

    requetes = [(ens, f"P{i:02d}") for ens in ENSEIGNES for i in range(1, 31)]

    t0_naif = time.perf_counter()
    res_naif: Dict[Tuple[str, str], Tuple[float, float]] = {}
    for ens_req, pid_req in requetes:
        s_an, n_an = 0, 0
        s_bf, n_bf = 0, 0
        for r in lignes_propres:
            if r["source"] == ens_req and r["produit_id"] == pid_req:
                px = int(r["prix_fcfa"])
                s_an += px
                n_an += 1
                if DEBUT_BLACK_FRIDAY <= r["date"] <= FIN_BLACK_FRIDAY:
                    s_bf += px
                    n_bf += 1
        if n_an > 0:
            res_naif[(ens_req, pid_req)] = (s_an / n_an, s_bf / n_bf if n_bf else 0.0)
    temps_naif_s = time.perf_counter() - t0_naif

    t0_opt = time.perf_counter()
    idx_an: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    idx_bf: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    for r in lignes_propres:
        cle = (r["source"], r["produit_id"])
        px = int(r["prix_fcfa"])
        idx_an[cle].append(px)
        if DEBUT_BLACK_FRIDAY <= r["date"] <= FIN_BLACK_FRIDAY:
            idx_bf[cle].append(px)

    res_opt: Dict[Tuple[str, str], Tuple[float, float]] = {}
    for cle in requetes:
        if cle in idx_an:
            vals_an = idx_an[cle]
            vals_bf = idx_bf[cle]
            res_opt[cle] = (
                sum(vals_an) / len(vals_an),
                sum(vals_bf) / len(vals_bf) if vals_bf else 0.0,
            )
    temps_opt_s = time.perf_counter() - t0_opt

    assert res_naif == res_opt, "Divergence entre le calcul naïf et le calcul indexé !"

    index_exact = {
        (r["source"], r["produit_id"], r["date"]): int(r["prix_fcfa"])
        for r in lignes_propres
    }
    cible = ("Baobab Shop", "P28", "2025-11-28")
    if cible not in index_exact:
        derniere = lignes_propres[-1]
        cible = (derniere["source"], derniere["produit_id"], derniere["date"])

    nb_repetitions = 100
    t0_list = time.perf_counter()
    for _ in range(nb_repetitions):
        for r in lignes_propres:
            if (r["source"], r["produit_id"], r["date"]) == cible:
                _ = int(r["prix_fcfa"])
                break
    temps_lookup_liste_us = ((time.perf_counter() - t0_list) / nb_repetitions) * 1e6

    t0_dict = time.perf_counter()
    for _ in range(nb_repetitions):
        _ = index_exact.get(cible)
    temps_lookup_dict_us = ((time.perf_counter() - t0_dict) / nb_repetitions) * 1e6

    return {
        "nb_lignes": float(len(lignes_propres)),
        "nb_requetes": float(len(requetes)),
        "temps_naif_ms": temps_naif_s * 1000.0,
        "temps_opt_ms": temps_opt_s * 1000.0,
        "facteur_gain": temps_naif_s / temps_opt_s if temps_opt_s > 0 else 0.0,
        "temps_lookup_liste_us": temps_lookup_liste_us,
        "temps_lookup_dict_us": temps_lookup_dict_us,
        "facteur_gain_lookup": (
            temps_lookup_liste_us / temps_lookup_dict_us if temps_lookup_dict_us > 0 else 0.0
        ),
    }
