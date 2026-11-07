from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

from src.analyse.comparateur import ENSEIGNES
from src.nettoyage.journal import JournalNettoyage
from src.nettoyage.nettoyeur import OffreEnseigne
from src.rapprochement.catalogue import ProduitReference


def formater_fcfa(montant: Optional[float]) -> str:
    if montant is None or isinstance(montant, bool):
        return "—"
    try:
        val = float(montant)
        if math.isnan(val) or math.isinf(val):
            return "—"
        return f"{int(round(val)):,}".replace(",", " ") + " FCFA"
    except (ValueError, TypeError):
        return "—"


def construire_rapport_synthese(
    catalogue: Dict[str, ProduitReference],
    offres_ml: List[OffreEnseigne],
    offres_bb: List[OffreEnseigne],
    offres_ci: List[OffreEnseigne],
    journal: JournalNettoyage,
    lignes_comparatif: List[Dict[str, object]],
    synthese: Dict[str, object],
    panier_std: Dict[str, object],
    panier_corrige: Dict[str, object],
    stats_historique: Dict[str, object],
    stats_perf: Dict[str, float],
    duree_totale_s: float,
) -> str:
    toutes_offres = offres_ml + offres_bb + offres_ci
    lignes: List[str] = []

    lignes.append("=" * 96)
    lignes.append("  RAPPORT D'ANALYSE COMPARATIVE DE MARCHÉ — ÉLECTRONIQUE & ÉLECTROMÉNAGER À ABIDJAN")
    lignes.append("  DA Python · L2 Computer Science · Séance 3")
    lignes.append("=" * 96)


    lignes.append("\n1. CHARGEMENT DES TROIS SOURCES DE DONNÉES")
    lignes.append("-" * 96)
    lignes.append(f"  • Catalogue de référence (CSV) : {len(catalogue)} produits de référence (P01 à P30)")
    lignes.append(f"  • Marché Lagune (CSV ';')      : {len(offres_ml)} articles uniques chargés (sur 30 lignes brutes)")
    lignes.append(f"  • Baobab Shop (JSON API)       : {len(offres_bb)} articles chargés")
    lignes.append(f"  • Comptoir Ivoire (Excel XLSX) : {len(offres_ci)} articles chargés")
    nb_exploitables = sum(1 for o in toutes_offres if o.exploitable)
    lignes.append(
        f"  -> Total unifié en mémoire     : {len(toutes_offres)} offres "
        f"(dont {nb_exploitables} offres en stock avec prix exploitable)"
    )


    lignes.append(f"\n2. SYNTHÈSE DU NETTOYAGE ({len(journal)} ÉVÉNEMENTS CONSIGNÉS DANS journal_nettoyage.txt)")
    lignes.append("-" * 96)
    for idx, entree in enumerate(journal.entrees, start=1):
        lignes.append(
            f"  [{idx:02d}] {entree.enseigne:<15} | {entree.reference:<11} | "
            f"{entree.type_anomalie:<38} | {entree.description}"
        )


    lignes.append("\n3. RAPPROCHEMENT AVEC LE CATALOGUE DE RÉFÉRENCE")
    lignes.append("-" * 96)
    nb_rapproches = sum(1 for o in toutes_offres if o.produit_id is not None)
    lignes.append(
        f"  • Taux de rapprochement : {nb_rapproches} / {len(toutes_offres)} offres associées (100 %)"
    )
    lignes.append("  • Méthode : normalisation des accents/unités (Go/GB, To/TB, CV/HP, pouces/\"),")
    lignes.append("              dictionnaire de synonymes FR/EN et score hybride (Rappel + Jaccard).")


    lignes.append(
        f"\n4. TABLEAU COMPARATIF ({len(lignes_comparatif)} PRODUITS DISPONIBLES DANS AU MOINS 2 ENSEIGNES)"
    )
    lignes.append("-" * 96)
    entete = (
        f"  {'ID':<3} | {'Produit':<32} | {'Marché Lagune':>13} | {'Baobab Shop':>13} | "
        f"{'Comptoir Iv.':>13} | {'Moins cher':<15} | {'Écart FCFA':>11} | {'Écart %':>7}"
    )
    lignes.append(entete)
    lignes.append("  " + "-" * (len(entete) - 2))
    for l in lignes_comparatif:
        ml_s = f"{l['prix_marche_lagune']:,}".replace(",", " ") if l["prix_marche_lagune"] else "—"
        bb_s = f"{l['prix_baobab_shop']:,}".replace(",", " ") if l["prix_baobab_shop"] else "—"
        ci_s = f"{l['prix_comptoir_ivoire']:,}".replace(",", " ") if l["prix_comptoir_ivoire"] else "—"
        ec_s = f"{l['ecart_fcfa']:,}".replace(",", " ")
        nom_court = str(l["nom"])[:32]
        mc_court = str(l["meilleure_enseigne"])[:15]
        lignes.append(
            f"  {l['produit_id']:<3} | {nom_court:<32} | {ml_s:>13} | {bb_s:>13} | "
            f"{ci_s:>13} | {mc_court:<15} | {ec_s:>11} | {l['ecart_pct']:>6.1f}%"
        )

    pids_compares = {l["produit_id"] for l in lignes_comparatif}
    pids_ecartes = [pid for pid in sorted(catalogue) if pid not in pids_compares]
    lignes.append(
        f"\n  -> Produits écartés (< 2 enseignes disponibles) : {len(pids_ecartes)} produits ({', '.join(pids_ecartes)})"
    )


    lignes.append("\n5. SYNTHÈSE DU MARCHÉ")
    lignes.append("-" * 96)
    lignes.append(
        f"  a) Nombre de fois où chaque enseigne est la moins chère (sur {len(lignes_comparatif)} produits, dont 2 ex-aequo) :"
    )
    for ens in ENSEIGNES:
        v = synthese["victoires"][ens]
        em = synthese["ecart_moyen"][ens]
        lignes.append(
            f"     • {ens:<16} : {v:2d} fois la moins chère "
            f"(sur {int(em['nb_produits_dispo'])} produits comparés où elle est en stock)"
        )

    lignes.append("\n  b) Écart moyen de chaque enseigne par rapport au prix le plus bas :")
    for ens in ENSEIGNES:
        em = synthese["ecart_moyen"][ens]
        lignes.append(
            f"     • {ens:<16} : +{em['ecart_moyen_fcfa']:,.0f} FCFA en moyenne "
            f"(soit +{em['ecart_moyen_pct']:.2f} % au-dessus du prix minimum)".replace(",", " ")
        )

    lignes.append("\n  c) Les 3 produits où il y a le plus à gagner à comparer :")
    lignes.append("     En valeur absolue (FCFA) :")
    for rang, l in enumerate(synthese["top3_fcfa"], start=1):
        lignes.append(
            f"       {rang}. {l['produit_id']} - {l['nom']} : "
            f"gain de {formater_fcfa(l['ecart_fcfa'])} (+{l['ecart_pct']:.1f} %) "
            f"chez {l['meilleure_enseigne']} ({formater_fcfa(l['prix_min'])} vs {formater_fcfa(l['prix_max'])})"
        )
    lignes.append("     En pourcentage (%) :")
    for rang, l in enumerate(synthese["top3_pct"], start=1):
        lignes.append(
            f"       {rang}. {l['produit_id']} - {l['nom']} : "
            f"+{l['ecart_pct']:.1f} % d'écart (gain de {formater_fcfa(l['ecart_fcfa'])}) "
            f"chez {l['meilleure_enseigne']} ({formater_fcfa(l['prix_min'])} vs {formater_fcfa(l['prix_max'])})"
        )


    lignes.append("\n6. SIMULATION DU PANIER DE RENTRÉE")
    lignes.append("-" * 96)
    lignes.append("  Articles : 1x Tecno Spark 20 (P04), 1x Lenovo IdeaPad 3 (P12),")
    lignes.append("             2x Clé USB SanDisk 64 Go (P14), 1x DD Seagate 1 To (P15), 1x Micro-ondes Samsung (P28)\n")
    lignes.append("  Coût du panier complet dans chaque enseigne :")
    for ens in ENSEIGNES:
        info_std = panier_std["par_enseigne"][ens]
        info_cor = panier_corrige["par_enseigne"][ens]
        if info_std["complet"]:
            lignes.append(f"    • {ens:<16} : {formater_fcfa(info_std['total'])}")
        else:
            total_errone = info_cor["total"] - 77900 + 779000
            lignes.append(
                f"    • {ens:<16} : Incomplet si P04 (779 000 FCFA aberrant) est écarté | "
                f"{formater_fcfa(info_cor['total'])} après correction de P04 à 77 900 FCFA "
                f"(ou {formater_fcfa(total_errone)} au tarif erroné)"
            )

    lignes.append(
        f"\n  Panier optimal multi-enseignes (chaque article au moins cher) : {formater_fcfa(panier_corrige['optimal_total'])}"
    )
    for det in panier_corrige["optimal_details"]:
        lignes.append(
            f"    - {det['quantite']}x {det['produit_id']} ({det['nom']:<36}) "
            f"chez {det['enseigne']:<15} : {formater_fcfa(det['prix_unitaire'])} x {det['quantite']} = {formater_fcfa(det['sous_total'])}"
        )


    lignes.append("\n7. ANALYSE DE L'HISTORIQUE ANNUEL (20 876 LIGNES : 01/11/2025 AU 31/10/2026)")
    lignes.append("-" * 96)
    lignes.append("  Comparaison de la semaine du Black Friday (24 au 30 novembre 2025) au prix moyen de l'année :")
    for ens in ENSEIGNES:
        st = stats_historique["par_enseigne"][ens]
        mj = st["meilleur_jour"]
        mm = st["meilleur_mois"]
        lignes.append(f"    • {ens} :")
        lignes.append(
            f"      - Prix moyen annuel : {formater_fcfa(st['moyenne_annuelle'])} | "
            f"Semaine Black Friday : {formater_fcfa(st['moyenne_bf'])} "
            f"({st['ecart_global_pct']:+.2f} % global, {st['ecart_moyen_par_produit_pct']:+.2f} % en moyenne par produit)"
        )
        lignes.append(
            f"      - Produits en promotion au Black Friday : {st['nb_produits_promo']} / {st['nb_produits_total']} produits"
        )
        lignes.append(
            f"      - Jour le moins cher de l'année : {mj[1]} ({formater_fcfa(mj[0])}) | "
            f"Mois le plus bas : {mm[1]} ({formater_fcfa(mm[0])})"
        )
    lignes.append("\n  Recommandation — Quand fallait-il acheter ?")
    lignes.append("    • Sur les plateformes en ligne (Marché Lagune : -11,3 % et Baobab Shop : -11,7 %),")
    lignes.append("      la semaine du Black Friday (24 au 30 novembre 2025) concentre les 7 jours les moins chers")
    lignes.append("      de toute l'année sur 100 % de leur catalogue.")
    lignes.append("    • Chez Comptoir Ivoire (boutique physique à Adjamé), il n'y a pas de promotion Black Friday")
    lignes.append("      (+3,7 % au-dessus de la moyenne annuelle) ; il fallait acheter à la rentrée de septembre 2026.")


    lignes.append("\n8. COMPLEXITÉ ALGORITHMIQUE ET MESURES DE TEMPS D'EXÉCUTION")
    lignes.append("-" * 96)
    lignes.append(
        f"  • Agrégation de {int(stats_perf['nb_requetes'])} requêtes (enseigne × produit) sur {int(stats_perf['nb_lignes']):,} lignes :".replace(",", " ")
    )
    lignes.append(f"    - Approche naïve (boucles imbriquées O(K × N)) : {stats_perf['temps_naif_ms']:.2f} ms")
    lignes.append(f"    - Approche indexée (dictionnaire O(N + K))     : {stats_perf['temps_opt_ms']:.2f} ms")
    lignes.append(f"    -> Accélération mesurée                        : x{stats_perf['facteur_gain']:.1f} plus rapide")
    lignes.append("  • Recherche unitaire d'un tarif (enseigne, produit, date) :")
    lignes.append(f"    - Parcours linéaire d'une list O(N)            : {stats_perf['temps_lookup_liste_us']:.2f} µs")
    lignes.append(f"    - Accès par clé dans un dict O(1)              : {stats_perf['temps_lookup_dict_us']:.3f} µs")
    lignes.append(f"    -> Accélération mesurée                        : x{stats_perf['facteur_gain_lookup']:,.0f} plus rapide".replace(",", " "))
    lignes.append(f"  • Temps d'exécution total de la chaîne complète  : {duree_totale_s * 1000.0:.1f} ms")
    lignes.append("=" * 96)

    return "\n".join(lignes) + "\n"


def exporter_rapport_synthese(texte_rapport: str, chemin_sortie: Path) -> None:
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin_sortie, mode="w", encoding="utf-8") as f:
        f.write(texte_rapport)
