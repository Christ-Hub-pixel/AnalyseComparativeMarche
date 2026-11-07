from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple
import unicodedata

if TYPE_CHECKING:
    from src.nettoyage.nettoyeur import OffreEnseigne
    from src.rapprochement.catalogue import ProduitReference


SYNONYMES: Dict[str, str] = {
    "samsun": "samsung",
    "gb": "go",
    "tb": "to",
    "fridge": "refrigerateur",
    "frigo": "refrigerateur",
    "clim": "climatiseur",
    "conditioner": "climatiseur",
    "ventilo": "ventilateur",
    "blender": "mixeur",
    "iron": "fer",
    "steam": "repasser",
    "microwave": "microondes",
    "kettle": "bouilloire",
    "electric": "electrique",
    "mouse": "souris",
    "printer": "imprimante",
    "monitor": "ecran",
    "expansion": "externe",
}


MOTS_VIDES: Set[str] = {
    "de", "sur", "a", "le", "la", "les", "sans", "fil", "pied",
    "pc", "portable", "core", "ssd", "ultra", "uhd", "4k", "crystal",
    "ac1200", "wireless", "air", "galaxy", "laptop",
}


def normaliser_texte(texte: object) -> str:
    if texte is None or isinstance(texte, bool):
        return ""
    t = str(texte).lower().strip()
    if not t:
        return ""
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace(",", ".")
    t = re.sub(r'(\d+)\s*"+', r"\1pouces ", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(gb|go)\b", r"\1go", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(tb|to)\b", r"\1to", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*l\b", r"\1l", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(cv|hp)\b", r"\1cv", t)
    t = re.sub(r"(\d+)\s*pouces\b", r"\1pouces", t)
    t = t.replace("micro-ondes", "microondes")
    t = t.replace("disque dur", "disquedur")
    t = re.sub(r"\bdd\b", "disquedur", t)
    return re.sub(r"\s+", " ", t).strip()


def extraire_jetons(texte: object) -> Set[str]:
    t = normaliser_texte(texte)
    if not t:
        return set()
    jetons_bruts = re.findall(r"[a-z0-9.]+", t)
    jetons: Set[str] = set()
    for j in jetons_bruts:
        j_norm = SYNONYMES.get(j, j)
        if j_norm not in MOTS_VIDES:
            jetons.add(j_norm)
    return jetons


def rapprocher_produit(
    designation: object,
    catalogue: Dict[str, "ProduitReference"],
    seuil_minimal: float = 0.25,
) -> Tuple[Optional[str], float]:
    if not catalogue:
        return None, 0.0
    jetons_article = extraire_jetons(designation)
    if not jetons_article:
        return None, 0.0

    meilleur_id: Optional[str] = None
    meilleur_score: float = -1.0

    for pid, prod in catalogue.items():
        if not prod.tokens:
            continue
        inter = len(jetons_article & prod.tokens)
        if inter == 0:
            continue
        union = len(jetons_article | prod.tokens)
        if union == 0:
            continue
        rappel = inter / len(jetons_article)
        jaccard = inter / union
        score = 0.65 * rappel + 0.35 * jaccard
        if score > meilleur_score:
            meilleur_score = score
            meilleur_id = pid

    if meilleur_id is None or meilleur_score < seuil_minimal:
        return None, 0.0
    return meilleur_id, round(meilleur_score, 4)


def associer_offres_au_catalogue(
    offres: List["OffreEnseigne"], catalogue: Dict[str, "ProduitReference"]
) -> None:
    for offre in offres or []:
        pid, score = rapprocher_produit(offre.designation_propre, catalogue)
        offre.produit_id = pid
        offre.score_rapprochement = score
