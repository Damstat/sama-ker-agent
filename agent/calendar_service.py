
"""Service Google Calendar de l'agence Sama Kër Immobilier."""

import os
from googleapiclient.discovery import build

from agent.google_auth import get_credentials


def get_calendar_service():
    """Construit et retourne le service Google Calendar."""
    creds = get_credentials()

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def get_calendar_id(conseiller_id: int) -> str:
    """Récupère l'identifiant Google Calendar d'un conseiller."""

    if conseiller_id not in (1, 2, 3):
        raise ValueError(
            "Identifiant conseiller invalide. Utiliser 1, 2 ou 3."
        )

    calendar_id = os.getenv(
        f"CALENDAR_ID_CONSEILLER_{conseiller_id}"
    )

    if not calendar_id or calendar_id.startswith("xxxx"):
        raise ValueError(
            f"Agenda du conseiller {conseiller_id} non configuré dans le fichier .env."
        )

    return calendar_id