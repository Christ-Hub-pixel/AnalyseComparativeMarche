from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import zipfile

from src.nettoyage.journal import JournalNettoyage
from src.nettoyage.nettoyeur import OffreEnseigne, nettoyer_offres_comptoir_ivoire


def lire_feuille_xlsx_standard(
    chemin_xlsx: Path, nom_feuille: str = "Tarifs octobre 2026"
) -> List[List[Optional[str]]]:
    chemin = Path(chemin_xlsx)
    if not chemin.exists() or not chemin.is_file():
        raise FileNotFoundError(f"Fichier Excel introuvable : {chemin}")

    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    try:
        with zipfile.ZipFile(chemin, "r") as archive:
            noms_fichiers = set(archive.namelist())
            chaines_partagees: List[str] = []
            if "xl/sharedStrings.xml" in noms_fichiers:
                racine_ss = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for si in racine_ss.findall("main:si", ns):
                    textes = [t.text or "" for t in si.findall(".//main:t", ns)]
                    chaines_partagees.append("".join(textes))

            cible_xml = "xl/worksheets/sheet1.xml"
            if "xl/workbook.xml" in noms_fichiers and "xl/_rels/workbook.xml.rels" in noms_fichiers:
                racine_wb = ET.fromstring(archive.read("xl/workbook.xml"))
                rels_wb = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
                map_rels = {
                    rel.attrib["Id"]: rel.attrib["Target"]
                    for rel in rels_wb
                    if "Id" in rel.attrib and "Target" in rel.attrib
                }

                feuilles = racine_wb.findall(".//main:sheet", ns)
                for sheet in feuilles:
                    nom_courant = (sheet.attrib.get("name") or "").strip()
                    if nom_courant.lower() == nom_feuille.strip().lower():
                        rid = sheet.attrib.get(f"{{{ns['r']}}}id")
                        if rid and rid in map_rels:
                            target = map_rels[rid].lstrip("/")
                            cible_xml = target if target.startswith("xl/") else f"xl/{target}"
                        break

            if cible_xml not in noms_fichiers:
                feuilles_dispo = sorted(f for f in noms_fichiers if f.startswith("xl/worksheets/sheet") and f.endswith(".xml"))
                if not feuilles_dispo:
                    raise ValueError(f"Aucune feuille de calcul trouvée dans {chemin}")
                cible_xml = feuilles_dispo[0]

            racine_ws = ET.fromstring(archive.read(cible_xml))
            lignes: List[List[Optional[str]]] = []

            for row_el in racine_ws.findall(".//main:sheetData/main:row", ns):
                cellules: Dict[int, Optional[str]] = {}
                max_col = 0
                for c_el in row_el.findall("main:c", ns):
                    ref_cell = c_el.attrib.get("r", "A1")
                    lettres_col = "".join(ch for ch in ref_cell if ch.isalpha())
                    idx_col = 0
                    for ch in lettres_col:
                        idx_col = idx_col * 26 + (ord(ch.upper()) - ord("A") + 1)
                    if idx_col <= 0:
                        idx_col = max_col + 1
                    max_col = max(max_col, idx_col)

                    type_cell = c_el.attrib.get("t")
                    v_el = c_el.find("main:v", ns)
                    is_el = c_el.find("main:is", ns)
                    val: Optional[str] = None
                    if v_el is not None and v_el.text is not None:
                        if type_cell == "s":
                            idx_s = int(v_el.text)
                            val = chaines_partagees[idx_s] if 0 <= idx_s < len(chaines_partagees) else ""
                        else:
                            val = v_el.text
                    elif is_el is not None:
                        val = "".join(x.text or "" for x in is_el.findall(".//main:t", ns))
                    cellules[idx_col] = val

                if max_col > 0:
                    lignes.append([cellules.get(i) for i in range(1, max_col + 1)])
                else:
                    lignes.append([])

            return lignes
    except (zipfile.BadZipFile, ET.ParseError) as err:
        raise ValueError(f"Fichier Excel corrompu ou illisible ({chemin}) : {err}") from err


def lire_excel_comptoir_ivoire_brut(
    chemin_xlsx: Path, journal: Optional[JournalNettoyage] = None
) -> List[Dict[str, object]]:
    lignes = lire_feuille_xlsx_standard(chemin_xlsx, "Tarifs octobre 2026")

    if journal is not None:
        journal.ajouter(
            enseigne="Comptoir Ivoire",
            reference="Fichier XLSX",
            type_anomalie="Mise en forme tableur (titre ligne 1, en-têtes ligne 3)",
            description=(
                "La ligne 1 contient un titre général, la ligne 2 est vide et les en-têtes "
                "sont en ligne 3 ; abréviations fréquentes ('Frigo', 'Clim', 'Ventilo', 'DD')."
            ),
            action_prise="Saut des lignes décoratives, lecture dès la ligne 4 et normalisation des abréviations.",
        )

    idx_entete = None
    for i, ligne in enumerate(lignes):
        if ligne and ligne[0] is not None and str(ligne[0]).strip().lower() == "code":
            idx_entete = i
            break

    if idx_entete is None:
        raise ValueError("En-têtes 'Code' introuvables dans comptoir_ivoire.xlsx")

    entetes = [str(col).strip() if col else f"col_{j}" for j, col in enumerate(lignes[idx_entete])]
    articles: List[Dict[str, object]] = []

    for num_ligne_excel, valeurs in enumerate(lignes[idx_entete + 1 :], start=4):
        if not valeurs or not any(v is not None and str(v).strip() for v in valeurs):
            continue
        entree: Dict[str, object] = {"num_ligne": num_ligne_excel}
        for j, nom_col in enumerate(entetes):
            entree[nom_col] = valeurs[j] if j < len(valeurs) else None
        articles.append(entree)

    return articles


def charger_comptoir_ivoire(
    chemin_xlsx: Path, journal: JournalNettoyage
) -> List[OffreEnseigne]:
    articles_bruts = lire_excel_comptoir_ivoire_brut(chemin_xlsx, journal=journal)
    return nettoyer_offres_comptoir_ivoire(articles_bruts, journal=journal)
