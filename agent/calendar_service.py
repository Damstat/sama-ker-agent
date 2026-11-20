
"""Service Google Calendar de l'agence Sama Kër Immobilier."""

import os

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build

from agent.google_auth import get_credentials

DUREE_VISITE = 45
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



def creer_rendez_vous(
    conseiller_id: int,
    nom_client: str,
    telephone: str,
    adresse: str,
    debut: datetime
) -> dict:
    """Crée un rendez-vous de visite immobilière dans Google Calendar."""

    if debut.tzinfo is None:
        raise ValueError("La date de début doit contenir un fuseau horaire.")

    debut = debut.astimezone(TIMEZONE)

    # Calculer automatiquement la fin de la visite
    fin = debut + timedelta(minutes=DUREE_VISITE)

    # Vérifier que la visite ne tombe pas un dimanche
    if debut.weekday() == 6:
        raise ValueError("Les visites ne sont pas autorisées le dimanche.")

    # Vérifier les horaires de l'agence : 9 h à 18 h
    if debut.hour < 9 or fin.hour > 18 or (
        fin.hour == 18 and fin.minute > 0
    ):
        raise ValueError("Les visites sont possibles entre 9 h et 18 h.")

    # Vérifier la disponibilité du conseiller
    disponible = verifier_disponibilite(
        conseiller_id,
        debut,
        fin
    )

    if not disponible:
        raise ValueError("Ce créneau est déjà occupé.")

    # Récupérer le service et l'agenda du conseiller
    calendar = get_calendar_service()
    calendar_id = get_calendar_id(conseiller_id)

    # Préparer les informations du rendez-vous
    evenement = {
        "summary": f"Visite immobilière - {nom_client}",
        "description": (
            f"Client : {nom_client}\n"
            f"Téléphone : {telephone}\n"
            f"Adresse du bien : {adresse}"
        ),
        "start": {
            "dateTime": debut.isoformat(),
            "timeZone": "Africa/Dakar"
        },
        "end": {
            "dateTime": fin.isoformat(),
            "timeZone": "Africa/Dakar"
        }
    }

    # Enregistrer le rendez-vous dans Google Calendar
    resultat = calendar.events().insert(
        calendarId=calendar_id,
        body=evenement
    ).execute()

    return {
        "id": resultat["id"],
        "lien": resultat.get("htmlLink"),
        "debut": debut.isoformat(),
        "fin": fin.isoformat(),
        "message": "Rendez-vous créé avec succès."
    }



def annuler_rendez_vous(conseiller_id: int, event_id: str) -> dict:
    """Annule un rendez-vous dans Google Calendar."""

    # Récupérer le service Google Calendar
    calendar = get_calendar_service()

    # Récupérer l'agenda du conseiller
    calendar_id = get_calendar_id(conseiller_id)

    # Supprimer le rendez-vous de l'agenda
    calendar.events().delete(
        calendarId=calendar_id,
        eventId=event_id
    ).execute()

    return {
        "event_id": event_id,
        "message": "Rendez-vous annulé avec succès."
    }
