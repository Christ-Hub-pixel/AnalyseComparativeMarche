from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class EntreeJournal:
    enseigne: str
    reference: str
    type_anomalie: str
    description: str
    action_prise: str


class JournalNettoyage:

    def __init__(self) -> None:
        self._entrees: List[EntreeJournal] = []

    def ajouter(
        self,
        enseigne: str,
        reference: str,
        type_anomalie: str,
        description: str,
        action_prise: str,
    ) -> None:
        self._entrees.append(
            EntreeJournal(
                enseigne=str(enseigne or "Inconnue").strip(),
                reference=str(reference or "N/A").strip(),
                type_anomalie=str(type_anomalie or "Anomalie").strip(),
                description=str(description or "").strip(),
                action_prise=str(action_prise or "").strip(),
            )
        )

    @property
    def entrees(self) -> List[EntreeJournal]:
        return list(self._entrees)

    def __len__(self) -> int:
        return len(self._entrees)

    def filtrer_par_enseigne(self, enseigne: str) -> List[EntreeJournal]:
        cible = str(enseigne or "").strip().lower()
        return [e for e in self._entrees if e.enseigne.lower() == cible]

    def exporter(self, chemin_fichier: Path) -> None:
        chemin_cible = Path(chemin_fichier)
        chemin_cible.parent.mkdir(parents=True, exist_ok=True)
        with open(chemin_cible, mode="w", encoding="utf-8") as f:
            f.write("=" * 88 + "\n")
            f.write("JOURNAL DE NETTOYAGE DES DONNÉES — ANALYSE COMPARATIVE DE MARCHÉ\n")
            f.write("=" * 88 + "\n\n")
            f.write(f"Nombre total d'événements et d'anomalies répertoriés : {len(self._entrees)}\n\n")

            for idx, entree in enumerate(self._entrees, start=1):
                f.write(f"[{idx:02d}] Enseigne : {entree.enseigne} | Référence : {entree.reference}\n")
                f.write(f"     Catégorie : {entree.type_anomalie}\n")
                f.write(f"     Anomalie  : {entree.description}\n")
                f.write(f"     Traitement: {entree.action_prise}\n")
                f.write("-" * 88 + "\n")
