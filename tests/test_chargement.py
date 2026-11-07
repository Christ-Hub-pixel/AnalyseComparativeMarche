from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True

RACINE_PROJET = Path(__file__).resolve().parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from src.chargement.csv_loader import charger_historique_csv, lire_csv_marche_lagune_brut
from src.chargement.excel_loader import lire_excel_comptoir_ivoire_brut
from src.chargement.json_loader import lire_json_baobab_brut
from src.rapprochement.catalogue import charger_catalogue_reference


class TestChargement(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dossier_data = RACINE_PROJET / "data"

    def test_catalogue_reference(self) -> None:
        catalogue = charger_catalogue_reference(self.dossier_data / "catalogue_reference.csv")
        self.assertEqual(len(catalogue), 30)
        self.assertIn("P01", catalogue)
        self.assertIn("P30", catalogue)
        self.assertEqual(catalogue["P04"].marque, "Tecno")

    def test_chargement_csv_marche_lagune(self) -> None:
        lignes = lire_csv_marche_lagune_brut(self.dossier_data / "marche_lagune.csv")
        self.assertEqual(len(lignes), 30)
        self.assertIn("reference", lignes[0])
        self.assertIn("designation", lignes[0])

    def test_chargement_json_baobab_shop(self) -> None:
        items = lire_json_baobab_brut(self.dossier_data / "baobab_shop.json")
        self.assertEqual(len(items), 26)
        self.assertEqual(items[0]["sku"], "BB01412")

    def test_chargement_excel_comptoir_ivoire(self) -> None:
        articles = lire_excel_comptoir_ivoire_brut(self.dossier_data / "comptoir_ivoire.xlsx")
        self.assertEqual(len(articles), 22)
        self.assertEqual(articles[0]["Code"], "CI200")
        self.assertEqual(articles[-1]["Code"], "CI221")

    def test_chargement_historique(self) -> None:
        lignes_hist = charger_historique_csv(self.dossier_data / "historique_prix.csv")
        self.assertEqual(len(lignes_hist), 20876)

    def test_fichier_introuvable_leve_exception(self) -> None:
        chemin_fictif = self.dossier_data / "fichier_inexistant_12345.csv"
        with self.assertRaises(FileNotFoundError):
            lire_csv_marche_lagune_brut(chemin_fictif)
        with self.assertRaises(FileNotFoundError):
            lire_excel_comptoir_ivoire_brut(chemin_fictif)


if __name__ == "__main__":
    unittest.main()
