"""Serveur MCP du catalogue Sama Kër Immobilier.

Expose (lecture seule) :
  - outil    rechercher_biens       : recherche de biens disponibles par critères
  - outil    detail_bien            : fiche complète d'un bien
  - outil    lister_creneaux_libres : créneaux de visite libres dans les agendas des conseillers
  - outil    verifier_disponibilite : disponibilité d'un conseiller sur un créneau
  - ressource agence://infos        : horaires de visite, zones couvertes, conditions de location

Lancement :
  python -m mcp_server.server                    # transport stdio (local)
  python -m mcp_server.server --http             # transport HTTP sur http://127.0.0.1:8000/mcp
  python -m mcp_server.server --http --port 9000 --host 0.0.0.0
"""
import argparse
import sqlite3
from datetime import datetime
from typing import Optional

from mcp.server.fastmcp import FastMCP

from mcp_server import catalogue
from agent.calendar_service import (
    verifier_disponibilite as verifier_disponibilite_calendar,
    lister_creneaux_libres as lister_creneaux_libres_calendar,
    lister_creneaux_tous_conseillers as lister_creneaux_tous_conseillers_calendar
)

mcp = FastMCP("sama-ker-catalogue", log_level="WARNING")


@mcp.tool()
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
        {"nombre": n, "biens": [...]} triés par loyer croissant (5 au maximum) ; si aucun bien
        ne correspond, nombre vaut 0 et un message l'indique ; en cas d'argument invalide,
        {"erreur": ..., "conseil": ...}. Ne jamais proposer un bien absent de cette liste.
    """
    return catalogue.rechercher_biens(quartier, type_bien, loyer_max, pieces_min)


@mcp.tool()
def detail_bien(id_bien: str) -> dict:
    """Renvoie la fiche complète d'un bien à partir de son identifiant (ex. "SK-001").

    Returns:
        Les informations du bien (id, type, quartier, loyer, pieces, adresse, disponible,
        description), ou {"erreur": ..., "conseil": ...} si l'identifiant n'existe pas.
    """
    return catalogue.detail_bien(id_bien)

@mcp.tool()
def verifier_disponibilite(
    conseiller_id: int,
    debut: str,
    fin: str
) -> dict:
    """Vérifie si un conseiller est disponible sur un créneau.

    Args:
        conseiller_id: Identifiant du conseiller (1, 2 ou 3).
        debut: Date et heure de début au format ISO 8601 avec fuseau horaire.
        fin: Date et heure de fin au format ISO 8601 avec fuseau horaire.
    """
    try:
        debut_datetime = datetime.fromisoformat(debut)
        fin_datetime = datetime.fromisoformat(fin)

        disponible = verifier_disponibilite_calendar(
            conseiller_id,
            debut_datetime,
            fin_datetime
        )

        return {
            "conseiller_id": conseiller_id,
            "debut": debut_datetime.isoformat(),
            "fin": fin_datetime.isoformat(),
            "disponible": disponible,
            "message": (
                "Le conseiller est disponible sur ce créneau."
                if disponible
                else "Le conseiller n'est pas disponible sur ce créneau."
            )
        }

    except ValueError as erreur:
        return {"erreur": str(erreur)}


@mcp.tool()
def lister_creneaux_libres(
    debut_periode: str,
    fin_periode: str,
    nombre: int = 3,
    conseiller_id: Optional[int] = None
) -> dict:
    """Recherche des créneaux de visite libres (45 min, lundi-samedi, 9 h-18 h) sur une période.

    Sans conseiller_id, cherche dans les agendas des 3 conseillers et indique pour chaque
    créneau le conseiller disponible (Moussa = 1, Fatou = 2, Ibrahima = 3).

    Args:
        debut_periode: Début de la période au format ISO 8601 avec fuseau, ex. 2026-11-26T15:00:00+00:00.
        fin_periode: Fin de la période au format ISO 8601 avec fuseau, ex. 2026-11-26T18:00:00+00:00.
        nombre: Nombre maximum de créneaux à proposer (3 par défaut).
        conseiller_id: Facultatif. Pour chercher dans l'agenda d'un seul conseiller (1, 2 ou 3).
    """
    try:
        debut_datetime = datetime.fromisoformat(debut_periode)
        fin_datetime = datetime.fromisoformat(fin_periode)

        if conseiller_id is None:
            return lister_creneaux_tous_conseillers_calendar(
                debut_periode=debut_datetime,
                fin_periode=fin_datetime,
                nombre=nombre
            )

        resultat = lister_creneaux_libres_calendar(
            conseiller_id=conseiller_id,
            debut_periode=debut_datetime,
            fin_periode=fin_datetime,
            nombre=nombre
        )

        return resultat

    except ValueError as erreur:
        return {"erreur": str(erreur)}


# Aucun outil d'écriture (créer, déplacer, annuler une visite) n'est exposé par ce serveur :
# un client MCP quelconque pourrait sinon modifier l'agenda sans l'accord d'un conseiller.
# Les écritures sont faites par le code (agent/visites.py, agent/traiter_emails.py),
# uniquement après la validation humaine.


def _quartiers_couverts() -> str:
    try:
        with sqlite3.connect(catalogue.DB_PATH) as conn:
            lignes = conn.execute("SELECT DISTINCT quartier FROM biens ORDER BY quartier").fetchall()
        return ", ".join(q for (q,) in lignes)
    except sqlite3.Error:
        return "catalogue indisponible"


@mcp.resource("agence://infos", mime_type="text/markdown")
def infos_agence() -> str:
    """Présentation de l'agence : horaires de visite, zones couvertes, conditions de location."""
    return f"""# Sama Kër Immobilier — agence de location à Dakar

## Horaires de visite
- Du lundi au samedi, de 9 h à 18 h (fuseau Africa/Dakar)
- Durée d'une visite : 45 minutes
- Pas de visite le dimanche ni les jours fériés

## Zones couvertes
{_quartiers_couverts()}

## Conditions de location
- Caution : 2 mois de loyer
- Avance : 1 mois de loyer à la signature
- Frais d'agence : 1 mois de loyer
- Pièces demandées : pièce d'identité, justificatif de revenus
- Bail d'un an renouvelable

## Hors périmètre de l'agent (transmis à un conseiller)
Réclamations, négociation de loyer, litiges.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP du catalogue Sama Kër")
    parser.add_argument("--http", action="store_true", help="transport HTTP (streamable) au lieu de stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
