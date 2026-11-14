"""Outils métier du catalogue (exercice 1). Déplacés dans le serveur MCP à l'exercice 2."""
import os
import sqlite3
import unicodedata
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/catalogue.db")

TYPES_VALIDES = ["Appartement", "Studio", "Villa", "Chambre"]


def _sans_accents(texte: str) -> str:
    """'Sacré-Cœur' -> 'sacre-coeur' : permet de trouver un quartier mal orthographié."""
    if texte is None:
        return ""
    texte = texte.replace("œ", "oe").replace("Œ", "OE").replace("-", " ")
    texte = unicodedata.normalize("NFD", texte)
    return "".join(c for c in texte if unicodedata.category(c) != "Mn").lower()


def _connexion() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row                          # lignes lisibles comme des dictionnaires
    conn.create_function("SANS_ACCENTS", 1, _sans_accents)  # utilisable dans le SQL
    return conn


def rechercher_biens(
    quartier: Optional[str] = None,
    type_bien: Optional[str] = None,
    loyer_max: Optional[int] = None,
    pieces_min: Optional[int] = None,
) -> dict:
    """Recherche les biens DISPONIBLES du catalogue Sama Kër correspondant aux critères.

    Args:
        quartier: quartier de Dakar, ex. "Mermoz", "Point E". Laisser vide si non précisé.
        type_bien: "Appartement", "Studio", "Villa" ou "Chambre".
        loyer_max: loyer mensuel maximum en F CFA, ex. 400000.
        pieces_min: nombre minimum de pièces. Un "F3" correspond à pieces_min=3.

    Returns:
        {"nombre": n, "biens": [...]} ; si aucun bien ne correspond, nombre vaut 0
        et un message l'indique. Ne jamais proposer un bien absent de cette liste.
    """
# 1. Vérifier les arguments : une erreur claire que le modèle peut corriger
    if loyer_max is not None and loyer_max <= 0:
        return {"erreur": f"loyer_max invalide : {loyer_max}",
                "conseil": "Donner un loyer mensuel positif en F CFA, ex. 400000."}
    if pieces_min is not None and pieces_min <= 0:
        return {"erreur": f"pieces_min invalide : {pieces_min}",
                "conseil": "Donner un nombre de pièces positif, ex. 3 pour un F3."}
    if type_bien is not None and type_bien.capitalize() not in TYPES_VALIDES:
        return {"erreur": f"type_bien inconnu : {type_bien}",
                "conseil": f"Utiliser l'un de : {', '.join(TYPES_VALIDES)}."}

# 2. Construire la requête : une condition par critère fourni, toujours avec des ?
    sql = "SELECT * FROM biens WHERE disponible = 1"
    params: list = []
    if quartier:
        sql += " AND SANS_ACCENTS(quartier) LIKE ?"
        params.append(f"%{_sans_accents(quartier)}%")
    if type_bien:
        sql += " AND type = ?"
        params.append(type_bien.capitalize())
    if loyer_max is not None:
        sql += " AND loyer <= ?"
        params.append(loyer_max)
    if pieces_min is not None:
        sql += " AND pieces >= ?"
        params.append(pieces_min)


# 3. Trier du moins cher au plus cher, 5 résultats maximum
    sql += " ORDER BY loyer ASC LIMIT 5"

    try:
        with _connexion() as conn:
            biens = [dict(ligne) for ligne in conn.execute(sql, params)]
    except (sqlite3.Error, FileNotFoundError) as e:
        return {"erreur": f"Catalogue inaccessible : {e}",
                "conseil": "Lancer python data/create_catalogue.py puis réessayer."}

    # 4. Dire clairement quand rien ne correspond
    if not biens:
        return {"nombre": 0, "biens": [], "message": "Aucun bien ne correspond aux critères de recherche."}
    return {"nombre": len(biens), "biens": biens}


def detail_bien(id_bien: str) -> dict:
    """Renvoie la fiche complète d'un bien à partir de son identifiant (ex. "SK-001").

    Returns:
        Les informations du bien, ou {"erreur": ...} si l'identifiant n'existe pas.
    """
    try:
        with _connexion() as conn:
            ligne = conn.execute("SELECT * FROM biens WHERE id = ?",
                                 (id_bien.strip().upper(),)).fetchone()
    except (sqlite3.Error, FileNotFoundError) as e:
        return {"erreur": f"Catalogue inaccessible : {e}",
                "conseil": "Lancer python data/create_catalogue.py puis réessayer."}

    if ligne is None:
        return {"erreur": f"Bien {id_bien} introuvable dans le catalogue.",
                "conseil": "Utiliser rechercher_biens pour obtenir des identifiants valides."}
    return dict(ligne)
