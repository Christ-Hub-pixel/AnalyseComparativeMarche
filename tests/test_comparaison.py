from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True

RACINE_PROJET = Path(__file__).resolve().parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from src.analyse.comparateur import comparer_produits
from src.analyse.historique import analyser_historique
from src.analyse.panier import evaluer_panier
from src.analyse.performance import mesurer_performances
from src.analyse.synthese import calculer_synthese
from src.main import executer_pipeline


class TestComparaisonEtAnalyse(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resultats = executer_pipeline(afficher_console=False)

    def test_comparatif_produits(self) -> None:
        comparatif = self.resultats["comparatif"]
        self.assertEqual(len(comparatif), 23)
        par_id = {l["produit_id"]: l for l in comparatif}
        self.assertEqual(par_id["P01"]["meilleure_enseigne"], "Comptoir Ivoire")
        self.assertEqual(par_id["P01"]["prix_min"], 92990)
        self.assertEqual(par_id["P01"]["ecart_fcfa"], 11010)

    def test_synthese(self) -> None:
        synthese = self.resultats["synthese"]
        self.assertEqual(synthese["victoires"]["Comptoir Ivoire"], 10)
        self.assertEqual(synthese["victoires"]["Baobab Shop"], 9)
        self.assertEqual(synthese["victoires"]["Marché Lagune"], 6)
        self.assertEqual(synthese["top3_fcfa"][0]["produit_id"], "P11")
        self.assertEqual(synthese["top3_fcfa"][0]["ecart_fcfa"], 52800)
        self.assertEqual(synthese["top3_pct"][0]["produit_id"], "P29")

    def test_panier_rentree(self) -> None:
        panier_corr = self.resultats["panier_corrige"]
        self.assertEqual(panier_corr["par_enseigne"]["Baobab Shop"]["total"], 491500)
        self.assertEqual(panier_corr["par_enseigne"]["Comptoir Ivoire"]["total"], 484075)
        self.assertEqual(panier_corr["par_enseigne"]["Marché Lagune"]["total"], 504300)
        self.assertEqual(panier_corr["optimal_total"], 477575)

    def test_historique_black_friday(self) -> None:
        hist = self.resultats["historique"]["par_enseigne"]
        self.assertLess(hist["Marché Lagune"]["ecart_global_pct"], -10.0)
        self.assertLess(hist["Baobab Shop"]["ecart_global_pct"], -10.0)
        self.assertGreater(hist["Comptoir Ivoire"]["ecart_global_pct"], 0.0)

    def test_robustesse_cas_vides_et_ruptures(self) -> None:
        self.assertEqual(comparer_produits({}, {}), [])
        synthese_vide = calculer_synthese([])
        self.assertEqual(synthese_vide["nb_produits_compares"], 0)

        panier_rupture = evaluer_panier(
            self.resultats["index_offres"],
            composition_panier=[("P03", "Samsung Galaxy A55", 1)],
        )
        self.assertFalse(panier_rupture["optimal_complet"])
        self.assertEqual(panier_rupture["optimal_total"], 0)

        hist_vide = analyser_historique([])
        self.assertEqual(hist_vide["nb_total_lignes"], 0)
        perf_vide = mesurer_performances([])
        self.assertEqual(perf_vide["nb_lignes"], 0.0)


if __name__ == "__main__":
    unittest.main()
