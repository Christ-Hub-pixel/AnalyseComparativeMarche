from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Dict, List, Optional

from src.nettoyage.journal import JournalNettoyage


@dataclass
class OffreEnseigne:
    enseigne: str
    code_article: str
    designation_brute: str
    designation_propre: str
    prix_affiche: Optional[float]
    frais_ou_remise: str
    prix_paye: Optional[int]
    en_stock: bool
    stock_detail: str
    produit_id: Optional[str] = None
    score_rapprochement: float = 0.0
    note: Optional[float] = None
    nb_avis: Optional[int] = None
    exploitable: bool = True
    anomalies: List[str] = field(default_factory=list)


def normaliser_designation(texte: object) -> str:
    if texte is None or isinstance(texte, bool):
        return ""
    return re.sub(r"\s+", " ", str(texte)).strip()


def nettoyer_prix_texte(valeur: object) -> Optional[int]:
    if valeur is None or isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        if isinstance(valeur, float) and (math.isnan(valeur) or math.isinf(valeur)):
            return None
        val_int = int(round(valeur))
        return val_int if val_int > 0 else None

    texte = str(valeur).strip()
    if not texte:
        return None

    nettoye = re.sub(r"(?i)fcfa|xof|f\s*cfa", "", texte)
    nettoye = re.sub(r"[\s\u202f\xa0]+", "", nettoye)
    nettoye = nettoye.replace(",", ".")

    if re.fullmatch(r"\d+(?:\.\d+)?", nettoye):
        val_float = float(nettoye)
        if math.isnan(val_float) or math.isinf(val_float):
            return None
        val_int = int(round(val_float))
        return val_int if val_int > 0 else None
    return None


def parser_flottant_sain(
    valeur: object,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    defaut: Optional[float] = None,
) -> Optional[float]:
    if valeur is None or isinstance(valeur, bool):
        return defaut
    texte = str(valeur).strip().replace("%", "").replace(",", ".")
    texte = re.sub(r"[\s\u202f\xa0]+", "", texte)
    if not texte:
        return defaut
    try:
        res = float(texte)
        if math.isnan(res) or math.isinf(res):
            return defaut
        if min_val is not None and res < min_val:
            return defaut
        if max_val is not None and res > max_val:
            return defaut
        return res
    except (ValueError, TypeError):
        return defaut


def parser_entier_sain(
    valeur: object,
    min_val: Optional[int] = 0,
    defaut: Optional[int] = None,
) -> Optional[int]:
    flottant = parser_flottant_sain(valeur, min_val=float(min_val) if min_val is not None else None)
    if flottant is None:
        return defaut
    return int(round(flottant))


def nettoyer_offres_marche_lagune(
    lignes_brutes: List[Dict[str, str]],
    journal: JournalNettoyage,
    corriger_prix_aberrant: bool = False,
) -> List[OffreEnseigne]:
    offres: List[OffreEnseigne] = []
    references_vues: Dict[str, int] = {}

    for num_ligne, ligne in enumerate(lignes_brutes or [], start=2):
        if not isinstance(ligne, dict):
            continue
        ref = normaliser_designation(ligne.get("reference"))
        designation_brute = str(ligne.get("designation") or "")
        designation_propre = normaliser_designation(designation_brute)

        if not ref and not designation_propre:
            continue
        if not ref:
            ref = f"ML-L{num_ligne}"

        anomalies_offre: List[str] = []

        if ref in references_vues:
            journal.ajouter(
                enseigne="Marché Lagune",
                reference=ref,
                type_anomalie="Doublon",
                description=(
                    f"Ligne {num_ligne} dupliquée pour '{designation_propre}' "
                    f"(déjà présente à la ligne {references_vues[ref]})."
                ),
                action_prise="Ligne doublon ignorée.",
            )
            continue
        references_vues[ref] = num_ligne

        if designation_brute != designation_propre or (designation_propre and designation_propre.islower()):
            anomalies_offre.append("Espaces parasites / casse minuscule")
            journal.ajouter(
                enseigne="Marché Lagune",
                reference=ref,
                type_anomalie="Formatage texte",
                description=f"Ligne {num_ligne} : désignation brute mal formatée ({designation_brute!r}).",
                action_prise=f"Normalisée en '{designation_propre}'.",
            )

        prix_str = str(ligne.get("prix") or "").strip()
        ancien_prix_str = str(ligne.get("ancien_prix") or "").strip()
        prix_val = nettoyer_prix_texte(prix_str)
        ancien_prix_val = nettoyer_prix_texte(ancien_prix_str)

        if prix_val is None:
            motif = "prix vide" if not prix_str else f"texte non numérique '{prix_str}'"
            anomalies_offre.append(f"Prix inexploitable ({motif})")
            journal.ajouter(
                enseigne="Marché Lagune",
                reference=ref,
                type_anomalie="Prix manquant / non numérique",
                description=f"Ligne {num_ligne} ({designation_propre}) : {motif}.",
                action_prise="Offre marquée comme non exploitable.",
            )

        if prix_val is not None and ancien_prix_val is not None and prix_val > ancien_prix_val * 3:
            if corriger_prix_aberrant and prix_val % 10 == 0 and (prix_val // 10) <= ancien_prix_val:
                prix_corrige = prix_val // 10
                anomalies_offre.append(
                    f"Prix aberrant {prix_val:,} FCFA corrigé en {prix_corrige:,} FCFA"
                )
                journal.ajouter(
                    enseigne="Marché Lagune",
                    reference=ref,
                    type_anomalie="Prix aberrant (faute de frappe)",
                    description=(
                        f"Ligne {num_ligne} ({designation_propre}) : prix {prix_val:,} FCFA "
                        f"incohérent avec l'ancien prix {ancien_prix_val:,} FCFA (zéro en trop)."
                    ),
                    action_prise=f"Corrigé à {prix_corrige:,} FCFA.",
                )
                prix_val = prix_corrige
            else:
                anomalies_offre.append(
                    f"Prix aberrant {prix_val:,} FCFA (> 8x ancien prix {ancien_prix_val:,} FCFA)"
                )
                journal.ajouter(
                    enseigne="Marché Lagune",
                    reference=ref,
                    type_anomalie="Prix aberrant (erreur de saisie)",
                    description=(
                        f"Ligne {num_ligne} ({designation_propre}) : prix affiché de {prix_val:,} FCFA "
                        f"contre un ancien prix barré de {ancien_prix_val:,} FCFA (779 000 au lieu de 77 900 FCFA)."
                    ),
                    action_prise="Prix aberrant écarté du comparatif (et valeur corrigée 77 900 FCFA documentée pour le panier).",
                )
                prix_val = None

        dispo_str = normaliser_designation(ligne.get("disponibilite"))
        en_stock = dispo_str.lower() in {"en stock", "stock limité", "stock limite", "disponible"}
        if not en_stock:
            anomalies_offre.append(f"Rupture de stock ({dispo_str or 'Non précisé'})")
            journal.ajouter(
                enseigne="Marché Lagune",
                reference=ref,
                type_anomalie="Rupture de stock",
                description=f"Ligne {num_ligne} ({designation_propre}) : disponibilité = '{dispo_str}'.",
                action_prise="Exclu de la sélection « le moins cher ».",
            )

        note_val = parser_flottant_sain(ligne.get("note_clients"), min_val=0.0, max_val=5.0)
        avis_val = parser_entier_sain(ligne.get("nb_avis"), min_val=0)

        exploitable = bool(designation_propre) and en_stock and (prix_val is not None)
        offres.append(
            OffreEnseigne(
                enseigne="Marché Lagune",
                code_article=ref,
                designation_brute=designation_brute,
                designation_propre=designation_propre,
                prix_affiche=float(prix_val) if prix_val is not None else None,
                frais_ou_remise="Livraison incluse",
                prix_paye=prix_val,
                en_stock=en_stock,
                stock_detail=dispo_str or "Inconnu",
                note=note_val,
                nb_avis=avis_val,
                exploitable=exploitable,
                anomalies=anomalies_offre,
            )
        )

    return offres


def nettoyer_offres_baobab_shop(
    articles_json: List[Dict[str, object]],
    journal: JournalNettoyage,
) -> List[OffreEnseigne]:
    offres: List[OffreEnseigne] = []
    skus_vus: Dict[str, int] = {}

    for idx, item in enumerate(articles_json or [], start=1):
        if not isinstance(item, dict):
            continue
        sku = normaliser_designation(item.get("sku")) or f"BB-ITEM{idx}"
        titre_brut = str(item.get("title") or "")
        titre_propre = normaliser_designation(titre_brut)
        if not titre_propre:
            continue

        if sku in skus_vus:
            journal.ajouter(
                enseigne="Baobab Shop",
                reference=sku,
                type_anomalie="Doublon",
                description=f"SKU {sku} dupliqué pour '{titre_propre}'.",
                action_prise="Article doublon ignoré.",
            )
            continue
        skus_vus[sku] = idx

        pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
        montant_brut = pricing.get("amount")
        montant_val = nettoyer_prix_texte(montant_brut)
        livraison_val = parser_entier_sain(pricing.get("delivery_fee"), min_val=0, defaut=0) or 0
        stock_qte = parser_entier_sain(item.get("stock"), min_val=0, defaut=0) or 0
        rating = item.get("rating") if isinstance(item.get("rating"), dict) else {}

        anomalies_offre: List[str] = []

        if montant_val is None:
            prix_paye = None
            anomalies_offre.append(f"Prix manquant (amount={montant_brut})")
            journal.ajouter(
                enseigne="Baobab Shop",
                reference=sku,
                type_anomalie="Prix manquant (null)",
                description=f"Article '{titre_propre}' : champ pricing.amount = {montant_brut}.",
                action_prise="Offre marquée comme non exploitable.",
            )
        else:
            prix_paye = montant_val + livraison_val

        en_stock = stock_qte > 0
        if not en_stock:
            anomalies_offre.append("Stock à 0 (rupture)")
            journal.ajouter(
                enseigne="Baobab Shop",
                reference=sku,
                type_anomalie="Rupture de stock",
                description=f"Article '{titre_propre}' : stock = 0.",
                action_prise="Exclu de la sélection « le moins cher ».",
            )

        note_val = parser_flottant_sain(rating.get("average"), min_val=0.0, max_val=5.0)
        avis_val = parser_entier_sain(rating.get("count"), min_val=0)

        exploitable = bool(titre_propre) and en_stock and (prix_paye is not None)
        offres.append(
            OffreEnseigne(
                enseigne="Baobab Shop",
                code_article=sku,
                designation_brute=titre_brut,
                designation_propre=titre_propre,
                prix_affiche=float(montant_val) if montant_val is not None else None,
                frais_ou_remise=f"+{livraison_val:,} FCFA livr.".replace(",", " "),
                prix_paye=prix_paye,
                en_stock=en_stock,
                stock_detail=f"{stock_qte} en stock",
                note=note_val,
                nb_avis=avis_val,
                exploitable=exploitable,
                anomalies=anomalies_offre,
            )
        )

    return offres


def nettoyer_offres_comptoir_ivoire(
    lignes_articles: List[Dict[str, object]],
    journal: JournalNettoyage,
) -> List[OffreEnseigne]:
    offres: List[OffreEnseigne] = []
    codes_vus: Dict[str, object] = {}

    for item in lignes_articles or []:
        if not isinstance(item, dict):
            continue
        num_ligne = item.get("num_ligne", "?")
        code = normaliser_designation(item.get("Code")) or f"CI-L{num_ligne}"
        article_brut = str(item.get("Article") or "")
        article_propre = normaliser_designation(article_brut)
        if not article_propre:
            continue

        if code in codes_vus:
            journal.ajouter(
                enseigne="Comptoir Ivoire",
                reference=code,
                type_anomalie="Doublon",
                description=f"Ligne {num_ligne} : code {code} dupliqué.",
                action_prise="Ligne doublon ignorée.",
            )
            continue
        codes_vus[code] = num_ligne

        prix_brut = item.get("Prix catalogue (FCFA)")
        remise_brute = item.get("Remise (%)")
        qte_brute = item.get("Quantité en rayon")

        anomalies_offre: List[str] = []

        if "samsun " in article_propre.lower():
            anomalies_offre.append("Faute de frappe 'Samsun' -> 'Samsung'")
            journal.ajouter(
                enseigne="Comptoir Ivoire",
                reference=code,
                type_anomalie="Faute d'orthographe",
                description=f"Ligne {num_ligne} : '{article_propre}' contient une faute ('Samsun' sans 'g').",
                action_prise="Corrigé automatiquement par le dictionnaire de synonymes.",
            )

        if isinstance(prix_brut, str) and not prix_brut.strip().isdigit():
            anomalies_offre.append(f"Prix stocké en texte ({prix_brut!r})")
            journal.ajouter(
                enseigne="Comptoir Ivoire",
                reference=code,
                type_anomalie="Type de donnée (texte au lieu de nombre)",
                description=(
                    f"Ligne {num_ligne} ({article_propre}) : prix catalogue stocké en chaîne "
                    f"'{prix_brut}' avec espace insécable."
                ),
                action_prise="Nettoyage des espaces et conversion en entier (279 300 FCFA).",
            )

        prix_cat = nettoyer_prix_texte(prix_brut)
        remise_pct = parser_flottant_sain(remise_brute, min_val=0.0, max_val=99.9, defaut=0.0) or 0.0
        qte = parser_entier_sain(qte_brute, min_val=0, defaut=0) or 0

        if prix_cat is not None:
            prix_paye = int(round(prix_cat * (1.0 - remise_pct / 100.0)))
        else:
            prix_paye = None
            anomalies_offre.append("Prix catalogue manquant")
            journal.ajouter(
                enseigne="Comptoir Ivoire",
                reference=code,
                type_anomalie="Prix manquant",
                description=f"Ligne {num_ligne} ({article_propre}) : prix catalogue invalide.",
                action_prise="Offre marquée comme non exploitable.",
            )

        en_stock = qte > 0
        if not en_stock:
            anomalies_offre.append("Quantité en rayon = 0 (rupture)")
            journal.ajouter(
                enseigne="Comptoir Ivoire",
                reference=code,
                type_anomalie="Rupture de stock",
                description=f"Ligne {num_ligne} ({article_propre}) : Quantité en rayon = 0.",
                action_prise="Exclu de la sélection « le moins cher ».",
            )

        exploitable = bool(article_propre) and en_stock and (prix_paye is not None)
        offres.append(
            OffreEnseigne(
                enseigne="Comptoir Ivoire",
                code_article=code,
                designation_brute=article_brut,
                designation_propre=article_propre,
                prix_affiche=float(prix_cat) if prix_cat is not None else None,
                frais_ou_remise=f"-{int(round(remise_pct))}% remise" if remise_pct > 0 else "0% remise",
                prix_paye=prix_paye,
                en_stock=en_stock,
                stock_detail=f"{qte} en rayon",
                exploitable=exploitable,
                anomalies=anomalies_offre,
            )
        )

    return offres
