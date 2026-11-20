
"""Service Google Calendar de l'agence Sama Kër Immobilier."""

import os

from datetime import datetime
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build

from agent.google_auth import get_credentials

TIMEZONE = ZoneInfo("Africa/Dakar")

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


def verifier_disponibilite(
    conseiller_id: int,
    debut: datetime,
    fin: datetime
) -> bool:
    """Vérifie si un conseiller est disponible sur un créneau."""

    if debut.tzinfo is None or fin.tzinfo is None:
        raise ValueError("Les dates doivent contenir un fuseau horaire.")

    debut = debut.astimezone(TIMEZONE)
    fin = fin.astimezone(TIMEZONE)

    if fin <= debut:
        raise ValueError("La date de fin doit être après la date de début.")

    calendar = get_calendar_service()
    calendar_id = get_calendar_id(conseiller_id)

    evenements = calendar.events().list(
        calendarId=calendar_id,
        timeMin=debut.isoformat(),
        timeMax=fin.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    return len(evenements.get("items", [])) == 0
