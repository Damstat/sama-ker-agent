"""Crée la base SQLite du catalogue Sama Kër Immobilier (30 biens fictifs)."""
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
DB_PATH = Path(os.getenv("DB_PATH", "data/catalogue.db"))

SCHEMA = """
CREATE TABLE biens (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,
    quartier    TEXT NOT NULL,
    loyer       INTEGER NOT NULL CHECK (loyer > 0),
    pieces      INTEGER NOT NULL CHECK (pieces > 0),
    adresse     TEXT NOT NULL,
    disponible  INTEGER NOT NULL CHECK (disponible IN (0, 1)),
    description TEXT
);
"""

# (id, type, quartier, loyer, pieces, adresse, disponible, description)
BIENS = [
    ("SK-001", "Appartement", "Mermoz", 350000, 3, "Rue MZ-45, Mermoz, Dakar", 1, "F3 lumineux, 2 chambres, parking"),
    ("SK-002", "Appartement", "Mermoz", 450000, 3, "Rue MZ-12, Mermoz, Dakar", 1, "F3 standing avec balcon"),
    ("SK-003", "Studio", "Point E", 150000, 1, "Rue PE-8, Point E, Dakar", 0, "Studio meublé, déjà loué"),
    # --- Mermoz ---
    ("SK-004", "Appartement", "Mermoz", 380000, 3, "Cité Mermoz, Villa 112, Dakar", 1, "F3 rénové, cuisine équipée, 2 salles de bain"),
    ("SK-005", "Appartement", "Mermoz", 320000, 3, "Rue MZ-78, Mermoz, Dakar", 0, "F3 calme, déjà loué"),
    ("SK-006", "Appartement", "Mermoz", 550000, 4, "Rue MZ-30, Mermoz, Dakar", 1, "F4 familial, 3 chambres, gardien"),
    ("SK-007", "Studio", "Mermoz", 175000, 1, "Rue MZ-5, Mermoz, Dakar", 1, "Studio meublé proche de la VDN"),
    # --- Sacré-Cœur ---
    ("SK-008", "Appartement", "Sacré-Cœur", 300000, 3, "Sacré-Cœur 3, Villa 8541, Dakar", 1, "F3 au 2e étage, climatisé"),
    ("SK-009", "Appartement", "Sacré-Cœur", 220000, 2, "Sacré-Cœur 2, Villa 8210, Dakar", 1, "F2 avec balcon"),
    ("SK-010", "Appartement", "Sacré-Cœur", 420000, 4, "Sacré-Cœur 3, Villa 9012, Dakar", 1, "F4 spacieux, parking"),
    # --- Point E ---
    ("SK-011", "Studio", "Point E", 160000, 1, "Rue PE-14, Point E, Dakar", 1, "Studio meublé, idéal étudiant"),
    ("SK-012", "Appartement", "Point E", 400000, 3, "Rue PE-3, Point E, Dakar", 1, "F3 proche université, terrasse"),
    # --- Almadies ---
    ("SK-013", "Villa", "Almadies", 1500000, 6, "Route des Almadies, Lot 22, Dakar", 1, "Villa avec piscine, 5 chambres"),
    ("SK-014", "Villa", "Almadies", 1200000, 5, "Zone Almadies, Lot 47, Dakar", 1, "Villa avec jardin, 4 chambres"),
    ("SK-015", "Appartement", "Almadies", 700000, 3, "Résidence Les Almadies, Dakar", 1, "F3 haut standing, vue mer"),
    # --- Ouakam ---
    ("SK-016", "Appartement", "Ouakam", 250000, 3, "Cité Avion, Villa 31, Ouakam, Dakar", 1, "F3 proche de la mosquée de la Divinité"),
    ("SK-017", "Appartement", "Ouakam", 180000, 2, "Rue OK-9, Ouakam, Dakar", 1, "F2 rez-de-chaussée"),
    ("SK-018", "Chambre", "Ouakam", 75000, 1, "Rue OK-21, Ouakam, Dakar", 1, "Chambre avec salle de bain"),
    # --- Plateau ---
    ("SK-019", "Appartement", "Plateau", 500000, 3, "Avenue Pompidou, Plateau, Dakar", 1, "F3 centre-ville, ascenseur"),
    ("SK-020", "Studio", "Plateau", 200000, 1, "Rue Carnot, Plateau, Dakar", 0, "Studio meublé, déjà loué"),
    ("SK-021", "Appartement", "Plateau", 350000, 2, "Rue Félix Faure, Plateau, Dakar", 1, "F2 rénové, proche des bureaux"),
    # --- Liberté 6 ---
    ("SK-022", "Appartement", "Liberté 6", 230000, 3, "Liberté 6 Extension, Villa 410, Dakar", 1, "F3 avec cour"),
    ("SK-023", "Appartement", "Liberté 6", 160000, 2, "Liberté 6, Villa 6789, Dakar", 1, "F2 lumineux"),
    ("SK-024", "Chambre", "Liberté 6", 80000, 1, "Liberté 6, Villa 6512, Dakar", 1, "Chambre meublée"),
    # --- Parcelles Assainies ---
    ("SK-025", "Appartement", "Parcelles Assainies", 150000, 3, "Unité 15, Villa 233, Parcelles Assainies, Dakar", 1, "F3 familial"),
    ("SK-026", "Appartement", "Parcelles Assainies", 110000, 2, "Unité 22, Villa 118, Parcelles Assainies, Dakar", 1, "F2 proche du marché"),
    ("SK-027", "Chambre", "Parcelles Assainies", 65000, 1, "Unité 10, Villa 47, Parcelles Assainies, Dakar", 1, "Chambre simple"),
    # --- Ngor ---
    ("SK-028", "Villa", "Ngor", 900000, 5, "Village de Ngor, Lot 12, Dakar", 1, "Villa près de la plage, 4 chambres"),
    ("SK-029", "Appartement", "Ngor", 450000, 3, "Route de Ngor, Dakar", 1, "F3 vue mer"),
    # --- Fann ---
    ("SK-030", "Appartement", "Fann", 600000, 4, "Fann Résidence, Rue F-7, Dakar", 1, "F4 standing, quartier calme"),
]


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)          # on repart de zéro à chaque lancement
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO biens VALUES (?, ?, ?, ?, ?, ?, ?, ?)", BIENS)
    print(f"{len(BIENS)} biens créés dans {DB_PATH}")


if __name__ == "__main__":
    main()
