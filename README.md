# AnalyseComparativeMarche - Guide Complet du Projet

**DA Python · L2 Computer Science · Séance 3**  
Ce document présente l'architecture **MVC**, le guide d'utilisation, l'explication détaillée des **5 mécanismes algorithmiques clés du code** (sans répétition), ainsi que la synthèse des résultats métier.

---

## 1. Architecture du projet et Patron MVC

```text
AnalyseComparativeMarche/
│
├── data/
│   ├── catalogue_reference.csv
│   ├── marche_lagune.csv
│   ├── baobab_shop.json
│   ├── comptoir_ivoire.xlsx
│   └── historique_prix.csv
│
├── src/
│   ├── main.py
│   │
│   ├── chargement/
│   │   ├── csv_loader.py
│   │   ├── json_loader.py
│   │   └── excel_loader.py
│   │
│   ├── nettoyage/
│   │   ├── nettoyeur.py
│   │   └── journal.py
│   │
│   ├── rapprochement/
│   │   ├── catalogue.py
│   │   └── correspondance.py
│   │
│   ├── analyse/
│   │   ├── comparateur.py
│   │   ├── synthese.py
│   │   ├── panier.py
│   │   ├── historique.py
│   │   └── performance.py
│   │
│   └── exportation/
│       ├── export_csv.py
│       └── rapport.py
│
├── output/
│   ├── comparatif_prix.csv
│   ├── journal_nettoyage.txt
│   ├── rapport_synthese.txt
│   └── comparatif_historique.csv
│
├── requirements.txt
├── README.md
└── .gitignore
```

| Couche MVC | Fichiers correspondants | Responsabilité |
|---|---|---|
| **Modèle (*Model*)** | `src/chargement/`, `src/nettoyage/`, `src/rapprochement/`, `src/analyse/` | Lecture multi-formats (`.csv`, `.json`, `.xlsx`), nettoyage, journalisation des anomalies, rapprochement par jetons et calculs statistiques. Aucun `print()` ni `input()`. |
| **Vue (*View*)** | `src/exportation/rapport.py`, `src/exportation/export_csv.py` | Mise en forme des montants en `FCFA`, construction des tableaux texte et écriture des 4 fichiers dans `output/`. |
| **Contrôleur (*Controller*)** | `src/main.py` | Orchestration du pipeline (`executer_pipeline`) et gestion des interactions utilisateur (`lancer_menu_interactif`). |

---

## 2. Exécution

1. **Lancer le menu interactif** :
   ```bash
   python3 src/main.py
   ```
2. **Afficher directement le rapport complet sans menu interactif** :
   ```bash
   python3 src/main.py --rapport
   ```

---

## 3. Explications du code : les 5 mécanismes clés (sans répétition)

### A. Lecture native d'un fichier Excel `.xlsx` sans bibliothèque externe (`src/chargement/excel_loader.py`)
Un fichier `.xlsx` est une archive ZIP contenant des fichiers XML :
- `xl/sharedStrings.xml` stocke toutes les chaînes de caractères uniques dans une liste indexée `chaines_partagees`.
- `xl/worksheets/sheet1.xml` contient les lignes `<row>` et les cellules `<c r="D20" t="s"><v>12</v></c>`.

```python
for c_el in row_el.findall("main:c", ns):
    ref_cell = c_el.attrib.get("r", "A1")
    lettres_col = "".join(ch for ch in ref_cell if ch.isalpha())
    idx_col = 0
    for ch in lettres_col:
        idx_col = idx_col * 26 + (ord(ch.upper()) - ord("A") + 1)

    type_cell = c_el.attrib.get("t")
    v_el = c_el.find("main:v", ns)
    if v_el is not None and v_el.text is not None:
        val = chaines_partagees[int(v_el.text)] if type_cell == "s" else v_el.text
```
Le calcul `idx_col` en base 26 convertit la lettre de colonne (`A` -> 1, `B` -> 2, `G` -> 7), ce qui garantit l'alignement exact des colonnes même si certaines cellules sont vides, sans dépendre de `openpyxl`.

### B. Nettoyage universel des prix et détection des anomalies (`src/nettoyage/nettoyeur.py`)
Toutes les offres sont converties dans la structure unique `OffreEnseigne`. Trois règles concentrent la logique métier :

1. **Conversion robuste d'un prix** (`nettoyer_prix_texte`) :
   ```python
   def nettoyer_prix_texte(valeur: object) -> Optional[int]:
       if valeur is None or isinstance(valeur, bool):
           return None
       nettoye = re.sub(r"(?i)fcfa|xof|f\s*cfa", "", str(valeur).strip())
       nettoye = re.sub(r"[\s\u202f\xa0]+", "", nettoye).replace(",", ".")
       if re.fullmatch(r"\d+(?:\.\d+)?", nettoye):
           val_int = int(round(float(nettoye)))
           return val_int if val_int > 0 else None
       return None
   ```
   Cette fonction nettoie les espaces insécables (`\u202f`), les devises (`FCFA`), les décimales à virgule et rejette `"Prix sur demande"`, les vides, `NaN` ou les nombres négatifs.

2. **Détection automatique du prix aberrant** (`ML-1021` affiché à `779 000 FCFA` contre un `ancien_prix` de `88 700 FCFA`) :
   ```python
   if prix_val is not None and ancien_prix_val is not None and prix_val > ancien_prix_val * 3:
       if corriger_prix_aberrant and prix_val % 10 == 0 and (prix_val // 10) <= ancien_prix_val:
           prix_val = prix_val // 10
       else:
           prix_val = None
   ```

3. **Calcul du prix final payé (`prix_paye`) et de la disponibilité (`exploitable`)** :
   - **Marché Lagune** : `prix_paye = prix_val`
   - **Baobab Shop** : `prix_paye = montant_val + livraison_val` (`amount + delivery_fee`)
   - **Comptoir Ivoire** : `prix_paye = int(round(prix_cat * (1.0 - remise_pct / 100.0)))`
   - **Validité** : `exploitable = en_stock and (prix_paye is not None)`

### C. Algorithme de rapprochement inter-enseignes (`src/rapprochement/correspondance.py`)
Pour relier `"REFRIGERATEUR HISENSE 205L"`, `"Hisense Fridge 205L"` et `"Frigo Hisense 205L"` au produit **`P20`**, le texte passe par deux étapes :

1. **Normalisation des accents et des unités** (`normaliser_texte`) :
   ```python
   t = unicodedata.normalize("NFD", str(texte).lower().strip())
   t = "".join(c for c in t if unicodedata.category(c) != "Mn")
   t = re.sub(r'(\d+)\s*"+', r"\1pouces ", t)
   t = re.sub(r"(\d+(?:\.\d+)?)\s*(gb|go)\b", r"\1go", t)
   t = re.sub(r"(\d+(?:\.\d+)?)\s*(tb|to)\b", r"\1to", t)
   t = re.sub(r"(\d+(?:\.\d+)?)\s*(cv|hp)\b", r"\1cv", t)
   ```
2. **Traduction par synonymes et score de similarité** (`rapprocher_produit`) :
   Chaque jeton est traduit via `SYNONYMES` (`"fridge"` / `"frigo"` -> `"refrigerateur"`, `"samsun"` -> `"samsung"`, `"iron"` -> `"fer"`), puis comparé aux 30 produits du catalogue selon un score hybride combinant le rappel sur l'article (65 %) et l'indice de Jaccard (35 %) :
   ```python
   rappel = inter / len(jetons_article)
   jaccard = inter / union
   score = 0.65 * rappel + 0.35 * jaccard
   ```

### D. Indexation en $O(1)$ et sélection par tas en $O(N \log k)$ (`src/analyse/comparateur.py` & `synthese.py`)
- `construire_index_offres` regroupe les offres dans un dictionnaire `index[produit_id][enseigne]` en un seul passage $O(N)$, évitant toute boucle imbriquée entre enseignes.
- `calculer_synthese` extrait les 3 produits ayant le plus fort écart avec `heapq.nlargest(3, ...)` en $O(N \log k)$ au lieu d'un tri complet `sorted()` en $O(N \log N)$.

### E. Analyse de l'historique (20 876 lignes) et benchmark de complexité (`src/analyse/historique.py` & `performance.py`)
- `analyser_historique` parcourt les 20 876 lignes de `historique_prix.csv` en **une seule passe** $O(N)$ pour cumuler simultanément les moyennes annuelles, celles de la semaine du Black Friday (`2025-11-24` au `2025-11-30`), ainsi que les moyennes par jour et par mois.
- `mesurer_performances` compare avec `time.perf_counter()` l'exécution de 90 requêtes `(enseigne, produit)` :
  - **Boucles imbriquées $O(K \times N)$** : 90 parcours complets de 20 876 lignes (~550–880 ms).
  - **Index dictionnaire $O(N + K)$** : 1 parcours de 20 876 lignes + 90 accès directs en $O(1)$ (~27–50 ms, soit **11× à 32× plus rapide**).

---

## 4. Synthèse des résultats métier

- **Chargement et Nettoyage** : **76 offres uniques** chargées (dont **62 exploitables** en stock) et **23 anomalies** documentées dans `output/journal_nettoyage.txt`.
- **Rapprochement** : **100 % (76 / 76)** des offres rattachées aux produits `P01` à `P30`.
- **Synthèse comparative** (sur 23 produits comparables dans `output/comparatif_prix.csv`) :
  - **Comptoir Ivoire** : **10 fois** la moins chère (écart moyen : **+2,81 %** / +6 667 FCFA).
  - **Baobab Shop** : **9 fois** la moins chère (écart moyen : **+2 702 FCFA** / +4,67 %).
  - **Marché Lagune** : **6 fois** la moins chère (écart moyen : **+8 042 FCFA** / +3,79 %).
  - **Top 3 des gains en FCFA** : `P11` HP 250 G9 (**52 800 FCFA**), `P09` iPhone 13 (**26 500 FCFA**), `P24` Climatiseur LG 1 CV (**26 000 FCFA**).
  - **Top 3 des gains en %** : `P29` Bouilloire 1,7 L (**+26,1 %**), `P14` Clé USB SanDisk 64 Go (**+19,7 %**), `P21` Congélateur Nasco 200 L (**+16,0 %**).
- **Panier de rentrée** (`1× P04`, `1× P12`, `2× P14`, `1× P15`, `1× P28`) :
  - **Comptoir Ivoire** : `484 075 FCFA` | **Baobab Shop** : `491 500 FCFA` | **Marché Lagune** : `504 300 FCFA` (avec `P04` corrigé à `77 900 FCFA`).
  - **Panier optimal multi-enseignes** : **`477 575 FCFA`**.
- **Historique annuel et Black Friday** (`output/comparatif_historique.csv`) :
  - **Marché Lagune (-11,16 %)** et **Baobab Shop (-11,59 %)** : les 7 jours les moins chers de l'année sont ceux du **Black Friday (24 au 30 novembre 2025)**.
  - **Comptoir Ivoire (+3,72 % au Black Friday)** : pas de promotion Black Friday ; ses meilleurs tarifs sont atteints à la **rentrée de septembre 2026**.
