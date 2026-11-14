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
    # ... à compléter jusqu'à SK-030
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
