from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True

RACINE_PROJET = Path(__file__).resolve().parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from src.chargement.csv_loader import charger_marche_lagune
from src.chargement.excel_loader import charger_comptoir_ivoire
from src.chargement.json_loader import charger_baobab_shop
from src.nettoyage.journal import JournalNettoyage
from src.nettoyage.nettoyeur import (
    nettoyer_offres_baobab_shop,
    nettoyer_offres_comptoir_ivoire,
    nettoyer_offres_marche_lagune,
    nettoyer_prix_texte,
    normaliser_designation,
    parser_entier_sain,
    parser_flottant_sain,
)
from src.rapprochement.catalogue import charger_catalogue_reference
from src.rapprochement.correspondance import associer_offres_au_catalogue, rapprocher_produit


class TestNettoyageEtRapprochement(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dossier_data = RACINE_PROJET / "data"
        cls.catalogue = charger_catalogue_reference(cls.dossier_data / "catalogue_reference.csv")

    def test_nettoyer_prix_texte(self) -> None:
        self.assertEqual(nettoyer_prix_texte("102\u202f900 FCFA"), 102900)
        self.assertEqual(nettoyer_prix_texte("279\u202f300"), 279300)
        self.assertEqual(nettoyer_prix_texte("15 700,40 XOF"), 15700)
        self.assertIsNone(nettoyer_prix_texte("Prix sur demande"))
        self.assertIsNone(nettoyer_prix_texte(""))
        self.assertIsNone(nettoyer_prix_texte(None))
        self.assertIsNone(nettoyer_prix_texte(True))
        self.assertIsNone(nettoyer_prix_texte(-5000))
        self.assertIsNone(nettoyer_prix_texte(0))
        self.assertIsNone(nettoyer_prix_texte(float("nan")))
        self.assertIsNone(nettoyer_prix_texte(float("inf")))

    def test_parsers_numeriques_robustes(self) -> None:
        self.assertEqual(parser_flottant_sain("4,5", min_val=0.0, max_val=5.0), 4.5)
        self.assertIsNone(parser_flottant_sain("8,5", min_val=0.0, max_val=5.0))
        self.assertIsNone(parser_flottant_sain("N/A", min_val=0.0, max_val=5.0))
        self.assertEqual(parser_flottant_sain("15%", min_val=0.0, max_val=100.0), 15.0)
        self.assertEqual(parser_entier_sain("25", min_val=0), 25)
        self.assertEqual(parser_entier_sain("-3", min_val=0, defaut=0), 0)

    def test_normaliser_designation(self) -> None:
        self.assertEqual(
            normaliser_designation("  souris sans fil logitech m185 "),
            "souris sans fil logitech m185",
        )
        self.assertEqual(normaliser_designation(None), "")
        self.assertEqual(normaliser_designation(False), "")

    def test_dedoublonnage_et_anomalies_marche_lagune(self) -> None:
        journal = JournalNettoyage()
        offres = charger_marche_lagune(self.dossier_data / "marche_lagune.csv", journal=journal)
        self.assertEqual(len(offres), 28)
        par_ref = {o.code_article: o for o in offres}
        self.assertFalse(par_ref["ML-1021"].exploitable)
        self.assertFalse(par_ref["ML-1119"].exploitable)
        self.assertGreaterEqual(len(journal), 10)

    def test_rapprochement_100_pourcent_et_seuil_inconnu(self) -> None:
        journal = JournalNettoyage()
        offres = (
            charger_marche_lagune(self.dossier_data / "marche_lagune.csv", journal=journal)
            + charger_baobab_shop(self.dossier_data / "baobab_shop.json", journal=journal)
            + charger_comptoir_ivoire(self.dossier_data / "comptoir_ivoire.xlsx", journal=journal)
        )
        associer_offres_au_catalogue(offres, self.catalogue)
        self.assertEqual(len(offres), 76)
        self.assertTrue(all(o.produit_id is not None for o in offres))

        pid_samsun, _ = rapprocher_produit("Samsun Galaxy A15 128Go", self.catalogue)
        self.assertEqual(pid_samsun, "P01")
        pid_iron, _ = rapprocher_produit("Philips Steam Iron", self.catalogue)
        self.assertEqual(pid_iron, "P27")
        pid_frigo, _ = rapprocher_produit("Frigo Hisense 205L", self.catalogue)
        self.assertEqual(pid_frigo, "P20")

        pid_inconnu, score_inconnu = rapprocher_produit("Chaussures de sport pointure 42", self.catalogue)
        self.assertIsNone(pid_inconnu)
        self.assertEqual(score_inconnu, 0.0)

    def test_robustesse_entrees_corrompues(self) -> None:
        journal = JournalNettoyage()
        self.assertEqual(nettoyer_offres_marche_lagune([{}, {"reference": "", "designation": ""}], journal), [])
        self.assertEqual(nettoyer_offres_baobab_shop([{}, {"sku": "X", "title": ""}], journal), [])
        self.assertEqual(nettoyer_offres_comptoir_ivoire([{}, {"Code": "X", "Article": ""}], journal), [])


if __name__ == "__main__":
    unittest.main()
