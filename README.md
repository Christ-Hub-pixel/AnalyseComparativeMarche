# Analyse Comparative de Marché

Outil en ligne de commande d'ingestion, de normalisation et d'analyse comparative de prix multi-enseignes (Abidjan, montants en `FCFA`). Le projet agrège des catalogues hétérogènes, rapproche les offres sur un référentiel commun, simule des paniers d'achat et analyse l'historique annuel des tarifs ainsi que la saisonnalité (dont le Black Friday).

---

## Fonctionnalités principales

- **Ingestion multi-formats sans dépendance externe** : lecture de sources `.csv`, `.json` et `.xlsx` uniquement avec la bibliothèque standard Python.
- **Nettoyage et journalisation des anomalies** : normalisation des devises et formats numériques, prise en compte des frais de livraison et remises, détection des prix aberrants et suivi des rejets dans un journal dédié.
- **Rapprochement inter-enseignes** : mise en correspondance automatique des libellés produits hétérogènes avec le catalogue de référence.
- **Comparatif et simulation de paniers** : identification des enseignes les moins chères par produit, calcul des écarts moyens, simulation de paniers prédéfinis ou personnalisés et optimisation multi-enseignes.
- **Analyse historique et saisonnalité** : suivi des tendances annuelles, comparaison avec la période du Black Friday et benchmark des temps de traitement.
- **Interface interactive et mode batch** : navigation par menu dans le terminal (8 modules d'exploration) ou génération directe du rapport complet.

---

## Prérequis et installation

- **Python 3.10+** (aucune bibliothèque tierce requise).

```bash
git clone <url-du-depot>
cd AnalyseComparativeMarche
```

*(Optionnel)* Si vous souhaitez isoler votre environnement :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Utilisation

### Mode interactif (menu principal)

```bash
python3 Controleur/main.py
```

Le menu donne accès à la consultation du rapport complet, au journal de nettoyage, à la recherche par produit, au tableau comparatif filtrable, à la synthèse du marché, au simulateur de panier, à l'explorateur d'historique et au benchmark de performance.

### Mode batch (génération directe du rapport)

```bash
python3 Controleur/main.py --rapport
```

*(L'option `--batch` est également acceptée.)*

---

## Données en entrée et fichiers générés

### Entrées (`data/`)

| Fichier | Description |
|---|---|
| `catalogue_reference.csv` | Référentiel des produits et catégories |
| `marche_lagune.csv` | Offres de l'enseigne Marché Lagune |
| `baobab_shop.json` | Offres de l'enseigne Baobab Shop (prix et frais de livraison) |
| `comptoir_ivoire.xlsx` | Offres de l'enseigne Comptoir Ivoire (tarifs catalogue et remises) |
| `historique_prix.csv` | Relevés historiques quotidiens sur l'année |

### Sorties (`output/`)

| Fichier | Description |
|---|---|
| `comparatif_prix.csv` | Tableau comparatif des prix exploitables par produit et par enseigne |
| `comparatif_historique.csv` | Synthèse annuelle et comparaison Black Friday par enseigne et produit |
| `journal_nettoyage.txt` | Détail des anomalies détectées et des offres écartées lors du chargement |
| `rapport_synthese.txt` | Rapport consolidé de l'ensemble de l'analyse |

---

## Architecture

Le projet suit une séparation **MVC** :

```text
AnalyseComparativeMarche/
├── data/                # Jeux de données sources (.csv, .json, .xlsx)
├── Models/              # Chargement, nettoyage, rapprochement et calculs analytiques
│   ├── chargement/
│   ├── nettoyage/
│   ├── rapprochement/
│   └── analyse/
├── Vue/                 # Formatage FCFA, construction des tableaux et exports
│   └── exportation/
├── Controleur/          # Point d'entrée, orchestration du pipeline et menu CLI
│   └── main.py
├── output/              # Rapports et exports CSV générés
├── requirements.txt
└── README.md
```
