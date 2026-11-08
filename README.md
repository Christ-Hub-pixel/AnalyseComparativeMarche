📊 Analyse comparative du marché

Comparaison des prix, qualité des données et optimisation d'un panier d'achat

"Python" (https://img.shields.io/badge/Python-3-blue?logo=python)
"Projet" (https://img.shields.io/badge/Projet-académique-orange)
"Données" (https://img.shields.io/badge/Données-fictives-informational)
"Licence" (https://img.shields.io/badge/Niveau-Licence%202-success)

Ce projet consiste à développer avec Python un programme d'analyse comparative des prix de produits électroniques et électroménagers proposés par trois enseignes fictives : Marché Lagune, Baobab Shop et Comptoir Ivoire.

Le programme importe des données provenant de plusieurs formats, les nettoie, rapproche les désignations des produits avec un catalogue de référence, compare les prix réellement payés et produit des rapports permettant d'identifier les offres les plus avantageuses.

«Note sur les données : toutes les enseignes, les offres et les données de cet exercice sont fictives. Elles ont été créées à des fins pédagogiques et ne représentent pas des commerces ni des prix réels.»

---

📌 Sommaire

- "Contexte et objectifs" (#-contexte-et-objectifs)
- "Fonctionnalités" (#-fonctionnalités-principales)
- "Sources de données" (#-sources-de-données)
- "Architecture du projet" (#-architecture-du-projet)
- "Méthodes et algorithmes" (#-méthodes-et-algorithmes)
- "Installation" (#-installation)
- "Exécution" (#-exécution-du-programme)
- "Résultats obtenus" (#-résultats-obtenus-sur-les-données-de-lexercice)
- "Fichiers générés" (#-fichiers-générés)
- "Limites et améliorations possibles" (#-limites-et-améliorations-possibles)
- "Contexte académique" (#-contexte-académique)

---

🎯 Contexte et objectifs

Les prix d'un même produit peuvent varier d'une enseigne à une autre. Une comparaison pertinente doit cependant tenir compte de la disponibilité, des remises et des frais supplémentaires, et pas uniquement du prix affiché.

L'objectif du projet est de construire une chaîne de traitement capable de :

1. Lire des données issues de plusieurs formats de fichiers.
2. Uniformiser les informations provenant des différentes enseignes.
3. Détecter et consigner les données manquantes, incohérentes ou en double.
4. Associer les désignations commerciales à un catalogue commun.
5. Comparer les prix disponibles et calculer les écarts.
6. Simuler un panier d'achat et rechercher une combinaison moins coûteuse.
7. Étudier l'évolution historique des prix.
8. Comparer le temps d'exécution de deux approches algorithmiques.

---

⚙️ Fonctionnalités principales

Module| Rôle
Chargement| Lecture des fichiers CSV, JSON et XLSX
Nettoyage| Normalisation des données, validation des prix et détection des anomalies
Journalisation| Enregistrement des opérations et anomalies détectées
Rapprochement| Association des offres au catalogue de référence
Comparaison| Comparaison des prix par produit et par enseigne
Synthèse| Calcul des écarts et identification des offres les moins chères
Panier| Comparaison du panier par enseigne et optimisation multi-enseignes
Historique| Analyse des prix par année, période, jour et mois
Performance| Mesure et comparaison de plusieurs méthodes de recherche
Exportation| Génération de fichiers CSV et de rapports texte

---

🗂️ Sources de données

Le projet utilise les fichiers présents dans le dossier "data/".

Fichier| Format| Utilisation
"catalogue_reference.csv"| CSV| Catalogue commun de 30 produits (P01 à P30)
"marche_lagune.csv"| CSV| Offres de Marché Lagune
"baobab_shop.json"| JSON| Offres de Baobab Shop
"comptoir_ivoire.xlsx"| Excel XLSX| Offres de Comptoir Ivoire
"historique_prix.csv"| CSV| Historique des prix sur la période étudiée

Les trois enseignes présentent volontairement des formats et des conventions différents. Par exemple, les prix peuvent contenir des espaces, des séparateurs décimaux ou des indications de devise. Les désignations peuvent aussi être en français ou en anglais.

---

🏗️ Architecture du projet

Le programme est organisé en modules séparés par responsabilité. "main.py" orchestre les traitements ; les autres modules prennent en charge le chargement, le nettoyage, le rapprochement, l'analyse et l'exportation. Cette organisation reprend certaines idées du modèle MVC, sans constituer une implémentation stricte d'un framework MVC.

AnalyseComparativeMarche/
│
├── data/                         # Données d'entrée
│   ├── catalogue_reference.csv
│   ├── marche_lagune.csv
│   ├── baobab_shop.json
│   ├── comptoir_ivoire.xlsx
│   └── historique_prix.csv
│
├── src/
│   ├── main.py                   # Point d'entrée et orchestration
│   │
│   ├── chargement/               # Lecture des sources
│   │   ├── csv_loader.py
│   │   ├── json_loader.py
│   │   └── excel_loader.py
│   │
│   ├── nettoyage/                # Nettoyage et journalisation
│   │   ├── nettoyeur.py
│   │   └── journal.py
│   │
│   ├── rapprochement/            # Catalogue et correspondance produits
│   │   ├── catalogue.py
│   │   └── correspondance.py
│   │
│   ├── analyse/                   # Analyses et calculs
│   │   ├── comparateur.py
│   │   ├── synthese.py
│   │   ├── panier.py
│   │   ├── historique.py
│   │   └── performance.py
│   │
│   └── exportation/               # Création des résultats
│       ├── export_csv.py
│       └── rapport.py
│
├── output/                        # Résultats générés
│   ├── comparatif_prix.csv
│   ├── comparatif_historique.csv
│   ├── journal_nettoyage.txt
│   └── rapport_synthese.txt
│
├── requirements.txt
├── .gitignore
└── README.md

Rôle des principaux dossiers

- "chargement/" : lit les fichiers CSV, JSON et XLSX et prépare les données pour les traitements suivants.
- "nettoyage/" : uniformise les valeurs, contrôle les prix et conserve une trace des anomalies.
- "rapprochement/" : charge le catalogue de référence et associe les désignations des enseignes aux produits communs.
- "analyse/" : réalise les comparaisons, les synthèses, la simulation du panier, l'analyse historique et le benchmark.
- "exportation/" : prépare les rapports texte et les fichiers CSV.
- "output/" : reçoit les résultats produits par l'exécution du programme.

---

🧠 Méthodes et algorithmes

1. Lecture de plusieurs formats

Le programme possède un module de chargement adapté à chaque source : CSV, JSON et Excel XLSX. Le lecteur XLSX exploite le fait qu'un classeur Excel est une archive ZIP contenant des fichiers XML. Cette approche permet de lire les cellules nécessaires à l'exercice sans ajouter de bibliothèque Excel externe.

2. Nettoyage et validation des prix

Le nettoyage prend notamment en charge :

- les espaces ordinaires et insécables dans les montants ;
- les indications de devise telles que "FCFA" et "XOF" ;
- les formats numériques avec virgule décimale ;
- les prix absents ou non numériques ;
- les produits en rupture de stock ;
- les doublons et les désignations mal formatées ;
- certaines valeurs aberrantes identifiées à partir des informations disponibles.

Le programme calcule également un prix payé adapté à la source : prix affiché, prix augmenté des frais de livraison ou prix après remise.

3. Rapprochement des produits

Les désignations sont normalisées avant comparaison : casse, accents, unités et certains termes français/anglais sont harmonisés. Un score hybride associe le rappel des jetons et l'indice de Jaccard :

score = 0.65 * rappel + 0.35 * jaccard

Le rapprochement s'effectue avec le catalogue de référence afin de comparer un même produit même lorsque les enseignes utilisent des noms différents.

4. Indexation et sélection des résultats

Les offres sont regroupées dans des dictionnaires indexés par produit et par enseigne. Cette organisation évite de reparcourir inutilement toutes les offres pour chaque recherche. Le module de synthèse utilise également "heapq.nlargest" pour sélectionner les meilleurs écarts sans effectuer systématiquement un tri complet.

5. Analyse historique et benchmark

L'historique est parcouru pour calculer des indicateurs par enseigne et par période, notamment autour de la semaine du Black Friday définie dans le programme. Le module de performance compare une recherche par parcours linéaire avec une recherche reposant sur un index dictionnaire.

Les temps mesurés dépendent de la machine et des conditions d'exécution : les valeurs du rapport sont des mesures expérimentales, et non des performances garanties.

---

💻 Installation

Prérequis

- Python 3 installé (Python 3.9 ou version ultérieure recommandé).
- Git, si le projet est récupéré depuis GitHub.
- Un terminal ou un éditeur de code comme Visual Studio Code.

1. Cloner le dépôt

git clone https://github.com/Christ-Hub-pixel/AnalyseComparativeMarche.git

2. Entrer dans le dossier du projet

cd AnalyseComparativeMarche

3. (Facultatif) Créer un environnement virtuel

python3 -m venv .venv

Sur Windows :

.venv\Scripts\activate

Sur Linux ou macOS :

source .venv/bin/activate

4. Dépendances

Le code actuel utilise les modules de la bibliothèque standard de Python. Le fichier "requirements.txt" est donc vide et aucune installation de paquet externe n'est nécessaire pour exécuter la version fournie.

---

▶️ Exécution du programme

Depuis la racine du projet, lancer le menu interactif :

python3 src/main.py

Pour exécuter directement le pipeline et afficher le rapport complet sans passer par le menu :

python3 src/main.py --rapport

L'option suivante lance également le pipeline en mode batch :

python3 src/main.py --batch

«Il est important de lancer les commandes depuis le dossier racine du projet afin que les imports "src..." et les chemins des données soient correctement résolus.»

---

📈 Résultats obtenus sur les données de l'exercice

Les chiffres ci-dessous correspondent aux données et aux fichiers de résultats présents dans ce dépôt. Ils sont reproductibles à partir du jeu de données fourni, sous réserve de l'environnement d'exécution.

Chargement et nettoyage

Indicateur| Résultat
Produits dans le catalogue de référence| 30
Offres chargées| 76
Offres en stock avec un prix exploitable| 62
Événements de nettoyage consignés| 23
Offres associées au catalogue| 76 / 76
Produits comparables (disponibles dans au moins 2 enseignes)| 23

Enseignes les plus souvent les moins chères

Sur les 23 produits comparables, le rapport généré présente la répartition suivante :

Enseigne| Nombre de fois la moins chère
Marché Lagune| 6
Baobab Shop| 9
Comptoir Ivoire| 10

Deux produits présentent une égalité entre enseignes dans les résultats.

Exemples d'écarts constatés

- HP 250 G9 : écart de 52 800 FCFA entre l'offre la moins chère et l'offre la plus chère comparée.
- iPhone 13 128 Go : écart de 26 500 FCFA.
- Climatiseur LG 1 CV : écart de 26 000 FCFA.

Simulation du panier de rentrée

Le panier d'exemple contient cinq références, dont deux unités de clé USB :

Scénario| Coût calculé
Marché Lagune (après correction documentée du prix P04)| 504 300 FCFA
Baobab Shop| 491 500 FCFA
Comptoir Ivoire| 484 075 FCFA
Panier optimal multi-enseignes| 477 575 FCFA

Le panier multi-enseignes choisit, pour chaque référence, l'offre exploitable la moins chère parmi les enseignes.

Historique et performance

L'historique fourni contient 20 876 lignes couvrant la période du 1er novembre 2025 au 31 octobre 2026. Le rapport compare notamment les prix moyens annuels avec ceux de la semaine du Black Friday (24 au 30 novembre 2025).

Le benchmark enregistré dans le rapport compare 90 recherches sur l'historique :

Approche| Temps mesuré dans le rapport
Parcours avec boucles imbriquées| 968,35 ms
Approche indexée par dictionnaire| 50,90 ms
Accélération mesurée| environ 19 fois

Ces mesures peuvent varier lors d'une nouvelle exécution.

---

📄 Fichiers générés

Après exécution, les principaux résultats sont disponibles dans "output/" :

Fichier| Contenu
"comparatif_prix.csv"| Comparaison des prix par produit et par enseigne
"comparatif_historique.csv"| Indicateurs issus de l'analyse historique
"journal_nettoyage.txt"| Détail des anomalies et opérations de nettoyage
"rapport_synthese.txt"| Rapport textuel regroupant les principales analyses

---

🔧 Limites et améliorations possibles

Le projet est réalisé dans un cadre pédagogique avec des données fictives et un catalogue limité à 30 produits. Plusieurs améliorations pourraient être envisagées :

- ajouter des tests automatisés pour les fonctions de chargement, nettoyage et calcul ;
- améliorer la validation des correspondances ambiguës entre produits ;
- ajouter une interface graphique ou un tableau de bord ;
- permettre l'ajout de nouvelles enseignes et de nouveaux formats de données ;
- enrichir les indicateurs et les visualisations historiques ;
- documenter davantage les cas limites et les hypothèses de calcul.

---

🎓 Contexte académique

- Matière : Data Analysis avec Python
- Niveau : Licence 2 – Informatique
- Séance : Séance 3
- Nature : Travail pratique pédagogique
- Thème : Analyse comparative du marché

👨‍💻 Auteur

Christ
Étudiant en Licence 2 – Génie logiciel
GitHub : "@Christ-Hub-pixel" (https://github.com/Christ-Hub-pixel)

---

Projet réalisé dans le but de mettre en pratique la programmation Python, le traitement de données, les algorithmes de comparaison et l'analyse de résultats.