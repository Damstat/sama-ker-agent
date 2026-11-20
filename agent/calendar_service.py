
"""Service Google Calendar de l'agence Sama Kër Immobilier."""

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
