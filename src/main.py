from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

sys.dont_write_bytecode = True


RACINE_PROJET = Path(__file__).resolve().parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from src.analyse.comparateur import ENSEIGNES, comparer_produits, construire_index_offres
from src.analyse.historique import analyser_historique
from src.analyse.panier import PANIER_RENTREE, evaluer_panier
from src.analyse.performance import mesurer_performances
from src.analyse.synthese import calculer_synthese
from src.chargement.csv_loader import charger_historique_csv, charger_marche_lagune
from src.chargement.excel_loader import charger_comptoir_ivoire
from src.chargement.json_loader import charger_baobab_shop
from src.exportation.export_csv import exporter_comparatif_csv, exporter_historique_csv
from src.exportation.rapport import (
    construire_rapport_synthese,
    exporter_rapport_synthese,
    formater_fcfa,
)
from src.nettoyage.journal import JournalNettoyage
from src.rapprochement.catalogue import charger_catalogue_reference
from src.rapprochement.correspondance import (
    associer_offres_au_catalogue,
    rapprocher_produit,
)


BLEU = "\033[94m"
CYAN = "\033[96m"
VERT = "\033[92m"
JAUNE = "\033[93m"
ROUGE = "\033[91m"
GRAS = "\033[1m"
RESET = "\033[0m"


def executer_pipeline(
    dossier_data: Path = RACINE_PROJET / "data",
    dossier_output: Path = RACINE_PROJET / "output",
    afficher_console: bool = True,
) -> dict:
    t0 = time.perf_counter()
    dossier_output.mkdir(parents=True, exist_ok=True)


    journal = JournalNettoyage()
    catalogue = charger_catalogue_reference(dossier_data / "catalogue_reference.csv")

    offres_ml = charger_marche_lagune(
        dossier_data / "marche_lagune.csv", journal=journal, corriger_prix_aberrant=False
    )
    offres_bb = charger_baobab_shop(dossier_data / "baobab_shop.json", journal=journal)
    offres_ci = charger_comptoir_ivoire(dossier_data / "comptoir_ivoire.xlsx", journal=journal)


    toutes_offres = offres_ml + offres_bb + offres_ci
    associer_offres_au_catalogue(toutes_offres, catalogue)
    index_offres = construire_index_offres(toutes_offres)


    lignes_comparatif = comparer_produits(catalogue, index_offres)


    synthese = calculer_synthese(lignes_comparatif)


    panier_std = evaluer_panier(index_offres)

    journal_temp = JournalNettoyage()
    offres_ml_corr = charger_marche_lagune(
        dossier_data / "marche_lagune.csv", journal=journal_temp, corriger_prix_aberrant=True
    )
    associer_offres_au_catalogue(offres_ml_corr, catalogue)
    index_offres_corr = construire_index_offres(offres_ml_corr + offres_bb + offres_ci)
    panier_corrige = evaluer_panier(index_offres_corr)


    lignes_historique = charger_historique_csv(dossier_data / "historique_prix.csv")
    stats_historique = analyser_historique(lignes_historique, catalogue=catalogue)
    stats_perf = mesurer_performances(lignes_historique)

    duree_totale_s = time.perf_counter() - t0


    journal.exporter(dossier_output / "journal_nettoyage.txt")
    exporter_comparatif_csv(lignes_comparatif, dossier_output / "comparatif_prix.csv")
    exporter_historique_csv(
        stats_historique["lignes_detail_csv"], dossier_output / "comparatif_historique.csv"
    )

    texte_rapport = construire_rapport_synthese(
        catalogue=catalogue,
        offres_ml=offres_ml,
        offres_bb=offres_bb,
        offres_ci=offres_ci,
        journal=journal,
        lignes_comparatif=lignes_comparatif,
        synthese=synthese,
        panier_std=panier_std,
        panier_corrige=panier_corrige,
        stats_historique=stats_historique,
        stats_perf=stats_perf,
        duree_totale_s=duree_totale_s,
    )
    exporter_rapport_synthese(texte_rapport, dossier_output / "rapport_synthese.txt")

    if afficher_console:
        print(texte_rapport)

    return {
        "catalogue": catalogue,
        "offres": toutes_offres,
        "offres_ml": offres_ml,
        "offres_bb": offres_bb,
        "offres_ci": offres_ci,
        "index_offres": index_offres,
        "index_offres_corr": index_offres_corr,
        "journal": journal,
        "comparatif": lignes_comparatif,
        "synthese": synthese,
        "panier_std": panier_std,
        "panier_corrige": panier_corrige,
        "lignes_historique": lignes_historique,
        "historique": stats_historique,
        "performance": stats_perf,
        "texte_rapport": texte_rapport,
    }


def pause_retour() -> None:
    try:
        input(f"\n{CYAN}Appuyez sur [Entrée] pour revenir au menu principal...{RESET}")
    except EOFError:
        pass


def menu_journal_nettoyage(donnees: dict) -> None:
    journal: JournalNettoyage = donnees["journal"]
    print(f"\n{GRAS}{BLEU}=== ÉTAPES 1 & 2 : CHARGEMENT ET JOURNAL DE NETTOYAGE ==={RESET}")
    print(f"  • Catalogue de référence : {len(donnees['catalogue'])} produits (P01 à P30)")
    print(f"  • Marché Lagune (CSV)    : {len(donnees['offres_ml'])} offres uniques (sur 30 lignes)")
    print(f"  • Baobab Shop (JSON)     : {len(donnees['offres_bb'])} offres")
    print(f"  • Comptoir Ivoire (XLSX) : {len(donnees['offres_ci'])} offres")
    print(f"  • Anomalies consignées   : {len(journal)} événements\n")

    print("  Filtrer le journal par enseigne :")
    print("    [1] Toutes les enseignes (23 événements)")
    print("    [2] Marché Lagune uniquement")
    print("    [3] Baobab Shop uniquement")
    print("    [4] Comptoir Ivoire uniquement")
    choix = input(f"\n{JAUNE}Votre choix (1-4, défaut=1) : {RESET}").strip() or "1"

    filtre_map = {
        "2": "Marché Lagune",
        "3": "Baobab Shop",
        "4": "Comptoir Ivoire",
    }
    if choix in filtre_map:
        entrees = journal.filtrer_par_enseigne(filtre_map[choix])
        titre = f"ANOMALIES — {filtre_map[choix].upper()}"
    else:
        entrees = journal.entrees
        titre = "TOUTES LES ANOMALIES DÉTECTÉES"

    print(f"\n{GRAS}{titre} ({len(entrees)} entrées) :{RESET}")
    print("-" * 92)
    for idx, e in enumerate(entrees, start=1):
        print(f"  {VERT}[{idx:02d}]{RESET} {GRAS}{e.enseigne:<15}{RESET} | Réf: {e.reference:<11} | {JAUNE}{e.type_anomalie}{RESET}")
        print(f"       Problème   : {e.description}")
        print(f"       Traitement : {e.action_prise}")
    print("-" * 92)
    pause_retour()


def menu_recherche_produit(donnees: dict) -> None:
    catalogue = donnees["catalogue"]
    index_offres = donnees["index_offres"]

    print(f"\n{GRAS}{BLEU}=== ÉTAPE 3 : RECHERCHE & RAPPROCHEMENT D'UN PRODUIT ==={RESET}")
    print("  Saisissez un identifiant (ex: P01, P11, P24) ou un nom/mot-clé (ex: 'Samsung', 'Frigo', 'iPhone', 'Clé USB')")
    print_liste = input(f"  (Tapez {JAUNE}'liste'{RESET} pour voir les 30 produits du catalogue, ou directement votre recherche) : ").strip()

    if print_liste.lower() == "liste" or not print_liste:
        print("\n  Catalogue de référence (P01 à P30) :")
        for pid in sorted(catalogue):
            p = catalogue[pid]
            print(f"    • {GRAS}{pid}{RESET} : {p.nom:<40} ({p.categorie} - {p.marque})")
        requete = input(f"\n{JAUNE}Entrez le code ou le nom du produit à inspecter : {RESET}").strip()
    else:
        requete = print_liste

    if not requete:
        return

    req_upper = requete.upper()
    if req_upper in catalogue:
        pid_trouve = req_upper
        score = 1.0
    else:
        pid_trouve, score = rapprocher_produit(requete, catalogue)

    if not pid_trouve:
        print(f"\n{ROUGE}Aucun produit correspondant à '{requete}' n'a été trouvé dans le catalogue.{RESET}")
        pause_retour()
        return

    prod = catalogue[pid_trouve]
    print(f"\n{VERT}✔ Produit rapproché :{RESET} {GRAS}{prod.produit_id} — {prod.nom}{RESET}")
    print(f"  Catégorie : {prod.categorie} | Marque : {prod.marque} | Score de rapprochement : {score * 100:.1f} %")
    print("-" * 92)
    print(f"  {'Enseigne':<16} | {'Réf':<8} | {'Désignation enseigne':<32} | {'Prix payé':>12} | {'Statut / Stock'}")
    print("  " + "-" * 88)

    offres_prod = index_offres.get(pid_trouve, {})
    prix_exploitables = {}
    for ens in ENSEIGNES:
        off = offres_prod.get(ens)
        if not off:
            print(f"  {ens:<16} | {'—':<8} | {'Non référencé dans cette enseigne':<32} | {'—':>12} | Absent")
            continue
        statut = f"{VERT}Exploitable ({off.stock_detail}, {off.frais_ou_remise}){RESET}" if off.exploitable else f"{ROUGE}Écarté ({', '.join(off.anomalies)}){RESET}"
        px_str = formater_fcfa(off.prix_paye) if off.prix_paye is not None else "Invalide"
        print(f"  {ens:<16} | {off.code_article:<8} | {off.designation_propre[:32]:<32} | {px_str:>12} | {statut}")
        if off.exploitable and off.prix_paye is not None:
            prix_exploitables[ens] = off.prix_paye

    print("-" * 92)
    if len(prix_exploitables) >= 2:
        p_min = min(prix_exploitables.values())
        p_max = max(prix_exploitables.values())
        gagnants = [e for e, p in prix_exploitables.items() if p == p_min]
        ecart_f = p_max - p_min
        ecart_p = (ecart_f / p_min) * 100.0
        print(
            f"  {VERT}➜ Décision d'achat :{RESET} acheter chez {GRAS}{' / '.join(gagnants)}{RESET} "
            f"à {GRAS}{formater_fcfa(p_min)}{RESET} (économie jusqu'à {formater_fcfa(ecart_f)}, soit {ecart_p:.1f} %)."
        )
    elif len(prix_exploitables) == 1:
        ens_seule, p_seul = next(iter(prix_exploitables.items()))
        print(f"  {JAUNE}➜ Disponible dans une seule enseigne ({ens_seule} à {formater_fcfa(p_seul)}) : écarté du comparatif.{RESET}")
    else:
        print(f"  {ROUGE}➜ Aucune offre exploitable en stock pour ce produit.{RESET}")

    pause_retour()


def menu_comparatif_interactif(donnees: dict) -> None:
    lignes = list(donnees["comparatif"])
    print(f"\n{GRAS}{BLEU}=== ÉTAPE 4 : TABLEAU COMPARATIF INTERACTIF ({len(lignes)} PRODUITS) ==={RESET}")
    print("  Filtrer par catégorie :")
    print("    [1] Toutes les catégories")
    print("    [2] Smartphone")
    print("    [3] Informatique")
    print("    [4] Électroménager")
    cat_choix = input(f"{JAUNE}  Catégorie (1-4, défaut=1) : {RESET}").strip() or "1"

    cat_map = {"2": "Smartphone", "3": "Informatique", "4": "Électroménager"}
    if cat_choix in cat_map:
        lignes = [l for l in lignes if l["categorie"] == cat_map[cat_choix]]

    print("\n  Trier les résultats par :")
    print("    [1] Identifiant produit (P01 -> P30)")
    print("    [2] Écart en FCFA (du plus grand au plus petit)")
    print("    [3] Écart en % (du plus grand au plus petit)")
    print("    [4] Prix le plus bas (du moins cher au plus cher)")
    tri_choix = input(f"{JAUNE}  Critère de tri (1-4, défaut=2) : {RESET}").strip() or "2"

    if tri_choix == "2":
        lignes.sort(key=lambda r: r["ecart_fcfa"], reverse=True)
    elif tri_choix == "3":
        lignes.sort(key=lambda r: r["ecart_pct"], reverse=True)
    elif tri_choix == "4":
        lignes.sort(key=lambda r: r["prix_min"])
    else:
        lignes.sort(key=lambda r: r["produit_id"])

    print(f"\n  {GRAS}Résultat ({len(lignes)} produits affichés) :{RESET}")
    entete = (
        f"  {'ID':<3} | {'Produit':<32} | {'Marché Lagune':>13} | {'Baobab Shop':>13} | "
        f"{'Comptoir Iv.':>13} | {'Moins cher':<15} | {'Écart FCFA':>11} | {'Écart %':>7}"
    )
    print(entete)
    print("  " + "-" * (len(entete) - 2))
    for l in lignes:
        ml_s = f"{l['prix_marche_lagune']:,}".replace(",", " ") if l["prix_marche_lagune"] else "—"
        bb_s = f"{l['prix_baobab_shop']:,}".replace(",", " ") if l["prix_baobab_shop"] else "—"
        ci_s = f"{l['prix_comptoir_ivoire']:,}".replace(",", " ") if l["prix_comptoir_ivoire"] else "—"
        ec_s = f"{l['ecart_fcfa']:,}".replace(",", " ")
        print(
            f"  {l['produit_id']:<3} | {str(l['nom'])[:32]:<32} | {ml_s:>13} | {bb_s:>13} | "
            f"{ci_s:>13} | {str(l['meilleure_enseigne'])[:15]:<15} | {ec_s:>11} | {l['ecart_pct']:>6.1f}%"
        )
    pause_retour()


def menu_synthese(donnees: dict) -> None:
    synthese = donnees["synthese"]
    print(f"\n{GRAS}{BLEU}=== ÉTAPE 5 : SYNTHÈSE DU MARCHÉ ==={RESET}")
    print(f"\n  {GRAS}1. Nombre de fois où chaque enseigne est la moins chère :{RESET}")
    for ens in ENSEIGNES:
        v = synthese["victoires"][ens]
        em = synthese["ecart_moyen"][ens]
        barre = "█" * v
        print(f"     • {ens:<16} : {VERT}{v:2d} victoires{RESET} {barre} (sur {int(em['nb_produits_dispo'])} produits en stock)")

    print(f"\n  {GRAS}2. Écart moyen de chaque enseigne par rapport au prix le plus bas :{RESET}")
    for ens in ENSEIGNES:
        em = synthese["ecart_moyen"][ens]
        print(
            f"     • {ens:<16} : +{em['ecart_moyen_fcfa']:,.0f} FCFA en moyenne "
            f"(soit {JAUNE}+{em['ecart_moyen_pct']:.2f} %{RESET} au-dessus du prix minimum)".replace(",", " ")
        )

    print(f"\n  {GRAS}3. Top 3 des produits où il y a le plus à gagner à comparer :{RESET}")
    print("     a) En valeur absolue (FCFA) :")
    for rang, l in enumerate(synthese["top3_fcfa"], start=1):
        print(
            f"        {rang}. {GRAS}{l['produit_id']} - {l['nom']}{RESET} : "
            f"économie de {VERT}{formater_fcfa(l['ecart_fcfa'])}{RESET} (+{l['ecart_pct']:.1f} %) "
            f"chez {l['meilleure_enseigne']} ({formater_fcfa(l['prix_min'])} vs {formater_fcfa(l['prix_max'])})"
        )
    print("     b) En pourcentage (%) :")
    for rang, l in enumerate(synthese["top3_pct"], start=1):
        print(
            f"        {rang}. {GRAS}{l['produit_id']} - {l['nom']}{RESET} : "
            f"{VERT}+{l['ecart_pct']:.1f} % d'écart{RESET} ({formater_fcfa(l['ecart_fcfa'])}) "
            f"chez {l['meilleure_enseigne']} ({formater_fcfa(l['prix_min'])} vs {formater_fcfa(l['prix_max'])})"
        )
    pause_retour()


def afficher_resultat_panier(res_panier: dict, titre: str) -> None:
    print(f"\n  {GRAS}{titre}{RESET}")
    print("  " + "-" * 86)
    print("  Coût du panier par enseigne :")
    for ens in ENSEIGNES:
        info = res_panier["par_enseigne"][ens]
        if info["complet"]:
            print(f"    • {ens:<16} : {GRAS}{formater_fcfa(info['total'])}{RESET}")
        else:
            manq = ", ".join(info["articles_manquants"])
            print(
                f"    • {ens:<16} : {ROUGE}Panier incomplet{RESET} "
                f"(indisponible sur : {manq} | sous-total partiel : {formater_fcfa(info['total_partiel'])})"
            )

    print(
        f"\n  {VERT}➜ Panier optimal multi-enseignes : {GRAS}{formater_fcfa(res_panier['optimal_total'])}{RESET}"
    )
    for det in res_panier["optimal_details"]:
        print(
            f"    - {det['quantite']}x {det['produit_id']} ({det['nom'][:34]:<34}) "
            f"chez {GRAS}{det['enseigne']:<15}{RESET} : "
            f"{formater_fcfa(det['prix_unitaire'])} x {det['quantite']} = {formater_fcfa(det['sous_total'])}"
        )


def menu_panier(donnees: dict) -> None:
    catalogue = donnees["catalogue"]
    index_offres_corr = donnees["index_offres_corr"]

    print(f"\n{GRAS}{BLEU}=== ÉTAPE 6 : SIMULATEUR DE PANIER D'ACHAT ==={RESET}")
    print("  [1] Afficher le panier de rentrée officiel (P04, P12, 2x P14, P15, P28)")
    print("  [2] Composer votre propre panier personnalisé")
    choix = input(f"\n{JAUNE}Votre choix (1-2, défaut=1) : {RESET}").strip() or "1"

    if choix == "1":
        afficher_resultat_panier(
            donnees["panier_corrige"],
            "PANIER DE RENTRÉE OFFICIEL (avec P04 corrigé à 77 900 FCFA chez Marché Lagune)",
        )
        print(
            f"\n  {JAUNE}Note :{RESET} Si l'on écarte strictement P04 chez Marché Lagune (affiché par erreur à 779 000 FCFA),"
        )
        print("        le panier Marché Lagune est incomplet, mais cela ne change pas le panier optimal (477 575 FCFA).")
        pause_retour()
        return


    print("\n  Catalogue disponible (P01 à P30) :")
    pids = sorted(catalogue.keys())
    for i in range(0, len(pids), 2):
        p1 = catalogue[pids[i]]
        s1 = f"{p1.produit_id}: {p1.nom[:34]:<34}"
        if i + 1 < len(pids):
            p2 = catalogue[pids[i + 1]]
            s2 = f"{p2.produit_id}: {p2.nom[:34]:<34}"
        else:
            s2 = ""
        print(f"    {s1} | {s2}")

    print(f"\n  Entrez vos articles sous la forme {GRAS}CODE:QUANTITE{RESET} séparés par des virgules")
    print("  Exemple : P01:1, P11:1, P14:2, P20:1")
    saisie = input(f"{JAUNE}  Votre panier : {RESET}").strip()
    if not saisie:
        return

    composition: List[Tuple[str, str, int]] = []
    for morceau in saisie.split(","):
        morceau = morceau.strip()
        if not morceau:
            continue
        if ":" in morceau:
            code_brut, qte_str = morceau.split(":", 1)
            qte = int(qte_str.strip()) if qte_str.strip().isdigit() else 1
        else:
            code_brut = morceau
            qte = 1
        pid = code_brut.strip().upper()
        if pid in catalogue and qte > 0:
            composition.append((pid, catalogue[pid].nom, qte))
        else:
            print(f"  {ROUGE}Article ignoré (code inconnu) : {morceau}{RESET}")

    if not composition:
        print(f"  {ROUGE}Aucun article valide sélectionné.{RESET}")
        pause_retour()
        return

    res_perso = evaluer_panier(index_offres_corr, composition_panier=composition)
    afficher_resultat_panier(res_perso, "RÉSULTAT DE VOTRE PANIER PERSONNALISÉ")
    pause_retour()


def menu_historique(donnees: dict) -> None:
    stats_hist = donnees["historique"]
    catalogue = donnees["catalogue"]

    print(f"\n{GRAS}{BLEU}=== ÉTAPE 7 : HISTORIQUE DES PRIX (20 876 LIGNES) & BLACK FRIDAY ==={RESET}")
    print("  [1] Comparatif global par enseigne (Semaine Black Friday 24-30 nov. 2025 vs Année)")
    print("  [2] Inspecter l'évolution annuelle d'un produit précis (P01 à P30)")
    choix = input(f"\n{JAUNE}Votre choix (1-2, défaut=1) : {RESET}").strip() or "1"

    if choix == "1":
        print("\n   Synthèse annuelle et impact du Black Friday par enseigne :")
        print("  " + "-" * 88)
        for ens in ENSEIGNES:
            st = stats_hist["par_enseigne"][ens]
            mj = st["meilleur_jour"]
            mm = st["meilleur_mois"]
            couleur = VERT if st["ecart_global_pct"] < 0 else ROUGE
            print(f"  • {GRAS}{ens}{RESET} ({st['nb_lignes']:,} relevés) :".replace(",", " "))
            print(
                f"    - Moyenne annuelle : {formater_fcfa(st['moyenne_annuelle'])} | "
                f"Black Friday : {formater_fcfa(st['moyenne_bf'])} "
                f"({couleur}{st['ecart_global_pct']:+.2f} %{RESET} global, {st['ecart_moyen_par_produit_pct']:+.2f} % par produit)"
            )
            print(
                f"    - Produits en promotion au Black Friday : {st['nb_produits_promo']} / {st['nb_produits_total']}"
            )
            print(
                f"    - Jour le moins cher de l'année : {VERT}{mj[1]}{RESET} ({formater_fcfa(mj[0])}) | "
                f"Mois le plus bas : {mm[1]} ({formater_fcfa(mm[0])})"
            )
        print("\n  " + "-" * 88)
        print(f"  {VERT}Conclusion :{RESET} Il fallait acheter pendant le Black Friday (24-30 nov. 2025) chez")
        print("  Marché Lagune (-11,3 %) et Baobab Shop (-11,7 %), mais en septembre 2026 chez Comptoir Ivoire.")
        pause_retour()
        return

    pid_req = input(f"\n{JAUNE}Entrez l'identifiant du produit (P01 à P30, ex: P09) : {RESET}").strip().upper()
    if pid_req not in catalogue:
        print(f"  {ROUGE}Identifiant '{pid_req}' inconnu.{RESET}")
        pause_retour()
        return

    prod = catalogue[pid_req]
    lignes_prod = [
        l for l in stats_hist["lignes_detail_csv"] if l["produit_id"] == pid_req
    ]
    print(f"\n  {GRAS}Historique annuel pour {pid_req} — {prod.nom} :{RESET}")
    print("  " + "-" * 90)
    print(
        f"  {'Enseigne':<16} | {'Relevés':>7} | {'Moy. Annuelle':>14} | {'Black Friday':>14} | {'Écart BF':>9} | {'Min Année':>12} | {'Max Année':>12}"
    )
    print("  " + "-" * 90)
    for l in lignes_prod:
        print(
            f"  {l['enseigne']:<16} | {l['nb_releves_annee']:>7} | "
            f"{formater_fcfa(l['prix_moyen_annuel_fcfa']):>14} | "
            f"{formater_fcfa(l['prix_moyen_black_friday_fcfa']):>14} | "
            f"{l['ecart_bf_pct']:>+8.2f}% | "
            f"{formater_fcfa(l['prix_min_annuel_fcfa']):>12} | "
            f"{formater_fcfa(l['prix_max_annuel_fcfa']):>12}"
        )
    pause_retour()


def menu_performance(donnees: dict) -> None:
    print(f"\n{GRAS}{BLEU}=== ÉTAPE 8 : BENCHMARK DE COMPLEXITÉ EN DIRECT (20 876 LIGNES) ==={RESET}")
    print("  Exécution des mesures de performance (time.perf_counter) en cours...\n")
    perf = mesurer_performances(donnees["lignes_historique"])
    donnees["performance"] = perf

    print(f"  {GRAS}1. Agrégation de {int(perf['nb_requetes'])} requêtes (enseigne × produit) sur {int(perf['nb_lignes']):,} lignes :{RESET}".replace(",", " "))
    print(f"     • Approche naïve (boucles imbriquées O(K × N)) : {ROUGE}{perf['temps_naif_ms']:.2f} ms{RESET}")
    print(f"     • Approche indexée (dictionnaire O(N + K))     : {VERT}{perf['temps_opt_ms']:.2f} ms{RESET}")
    print(f"     ➜ Gain de vitesse mesuré                       : {GRAS}{VERT}x{perf['facteur_gain']:.1f} plus rapide{RESET}\n")

    print(f"  {GRAS}2. Recherche unitaire d'un tarif précis (enseigne, produit, date) :{RESET}")
    print(f"     • Parcours linéaire d'une list O(N)            : {ROUGE}{perf['temps_lookup_liste_us']:.2f} µs{RESET}")
    print(f"     • Accès direct par clé dans un dict O(1)       : {VERT}{perf['temps_lookup_dict_us']:.3f} µs{RESET}")
    print(f"     ➜ Gain de vitesse mesuré                       : {GRAS}{VERT}x{perf['facteur_gain_lookup']:,.0f} plus rapide{RESET}".replace(",", " "))
    pause_retour()


def lancer_menu_interactif(donnees: dict) -> None:
    while True:
        print("\n" + "=" * 78)
        print(f"  {GRAS}{CYAN}ANALYSE COMPARATIVE DE MARCHÉ — MENU INTERACTIF (ABIDJAN){RESET}")
        print("=" * 78)
        print(f"  {VERT}[1]{RESET} Afficher le rapport complet des 8 étapes")
        print(f"  {VERT}[2]{RESET} Explorer le chargement & le journal de nettoyage (par enseigne)")
        print(f"  {VERT}[3]{RESET} Rechercher un produit (P01..P30 ou mot-clé) et comparer ses prix")
        print(f"  {VERT}[4]{RESET} Tableau comparatif interactif (filtrer par catégorie / trier)")
        print(f"  {VERT}[5]{RESET} Synthèse du marché (victoires par enseigne, écart moyen, Top 3)")
        print(f"  {VERT}[6]{RESET} Simulateur de Panier (panier de rentrée ou panier personnalisé)")
        print(f"  {VERT}[7]{RESET} Explorer l'historique annuel (20 876 lignes) & Black Friday")
        print(f"  {VERT}[8]{RESET} Lancer le benchmark de complexité algorithmique en direct")
        print(f"  {ROUGE}[0]{RESET} Quitter")
        print("-" * 78)
        print(f"  Fichiers à jour dans {CYAN}output/{RESET} : comparatif_prix.csv, journal_nettoyage.txt,")
        print("                            rapport_synthese.txt, comparatif_historique.csv")
        print("=" * 78)

        try:
            choix = input(f"\n{GRAS}{JAUNE}Choisissez une option [0-8] : {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{VERT}Au revoir !{RESET}")
            break

        if choix == "0" or choix.lower() in {"q", "quit", "exit"}:
            print(f"\n{VERT}Fin de la session interactive. Tous les fichiers sont disponibles dans output/.{RESET}")
            break
        elif choix == "1":
            print("\n" + donnees["texte_rapport"])
            pause_retour()
        elif choix == "2":
            menu_journal_nettoyage(donnees)
        elif choix == "3":
            menu_recherche_produit(donnees)
        elif choix == "4":
            menu_comparatif_interactif(donnees)
        elif choix == "5":
            menu_synthese(donnees)
        elif choix == "6":
            menu_panier(donnees)
        elif choix == "7":
            menu_historique(donnees)
        elif choix == "8":
            menu_performance(donnees)
        else:
            print(f"\n{ROUGE}Option invalide ('{choix}'). Veuillez entrer un chiffre entre 0 et 8.{RESET}")


if __name__ == "__main__":

    if "--rapport" in sys.argv or "--batch" in sys.argv:
        executer_pipeline(afficher_console=True)
    else:
        donnees_pipeline = executer_pipeline(afficher_console=False)
        lancer_menu_interactif(donnees_pipeline)
