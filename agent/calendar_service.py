"""Service Google Calendar de l'agence Sama Kër Immobilier."""

import os
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from agent.google_auth import get_credentials


load_dotenv()

DUREE_VISITE = 45
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Africa/Dakar"))

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

    # Vérifier la présence du fuseau horaire
    if debut.tzinfo is None or fin.tzinfo is None:
        raise ValueError("Les dates doivent contenir un fuseau horaire.")

    # Convertir les dates dans le fuseau horaire de l'agence
    debut = debut.astimezone(TIMEZONE)
    fin = fin.astimezone(TIMEZONE)

    # Vérifier que la fin est après le début
    if fin <= debut:
        raise ValueError("La date de fin doit être après la date de début.")

    # Vérifier que le rendez-vous n'est pas dans le passé
    maintenant = datetime.now(TIMEZONE)

    if debut < maintenant:
        raise ValueError("Impossible de réserver un créneau dans le passé.")

    # Vérifier que le rendez-vous ne tombe pas un dimanche
    if debut.weekday() == 6:
        raise ValueError("Les visites ne sont pas autorisées le dimanche.")

    # Vérifier les horaires de l'agence : 9 h à 18 h
    if debut.hour < 9 or fin.hour > 18 or (
        fin.hour == 18 and fin.minute > 0
    ):
        raise ValueError("Les visites sont possibles entre 9 h et 18 h.")

    # Récupérer le service Google Calendar
    calendar = get_calendar_service()

    # Récupérer l'agenda du conseiller
    calendar_id = get_calendar_id(conseiller_id)

    # Rechercher les événements sur le créneau demandé
    evenements = calendar.events().list(
        calendarId=calendar_id,
        timeMin=debut.isoformat(),
        timeMax=fin.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    # Retourner True si aucun événement n'occupe le créneau
    return len(evenements.get("items", [])) == 0


def lister_creneaux_libres(
    conseiller_id: int,
    debut_periode: datetime,
    fin_periode: datetime,
    nombre: int = 3
) -> dict:
    """Liste les premiers créneaux libres d'un conseiller sur une période."""

    # Vérifier que les dates possèdent un fuseau horaire
    if debut_periode.tzinfo is None or fin_periode.tzinfo is None:
        raise ValueError("Les dates doivent contenir un fuseau horaire.")

    # Convertir les dates dans le fuseau de l'agence
    debut_periode = debut_periode.astimezone(TIMEZONE)
    fin_periode = fin_periode.astimezone(TIMEZONE)

    if fin_periode <= debut_periode:
        raise ValueError("La fin de période doit être après le début.")

    if nombre < 1:
        raise ValueError("Le nombre de créneaux doit être supérieur à zéro.")

    # Récupérer le service Google Calendar et l'agenda du conseiller
    calendar = get_calendar_service()
    calendar_id = get_calendar_id(conseiller_id)

    # Récupérer tous les événements de la période en une seule requête
    evenements = calendar.events().list(
        calendarId=calendar_id,
        timeMin=debut_periode.isoformat(),
        timeMax=fin_periode.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    # Préparer les périodes déjà occupées
    periodes_occupees = []

    for evenement in evenements.get("items", []):

        # Ignorer les événements annulés ou transparents
        if evenement.get("status") == "cancelled":
            continue

        if evenement.get("transparency") == "transparent":
            continue

        debut_event = evenement["start"]
        fin_event = evenement["end"]

        # Gérer les événements avec une heure précise
        if "dateTime" in debut_event:
            debut_event = datetime.fromisoformat(
                debut_event["dateTime"].replace("Z", "+00:00")
            ).astimezone(TIMEZONE)

            fin_event = datetime.fromisoformat(
                fin_event["dateTime"].replace("Z", "+00:00")
            ).astimezone(TIMEZONE)

        # Gérer les événements sur une journée entière
        else:
            date_debut = datetime.fromisoformat(
                debut_event["date"]
            ).date()

            date_fin = datetime.fromisoformat(
                fin_event["date"]
            ).date()

            debut_event = datetime.combine(
                date_debut, time.min, tzinfo=TIMEZONE
            )

            fin_event = datetime.combine(
                date_fin, time.min, tzinfo=TIMEZONE
            )

        periodes_occupees.append((debut_event, fin_event))

    # Rechercher les créneaux disponibles
    creneaux = []
    date_actuelle = debut_periode.date()
    derniere_date = fin_periode.date()
    maintenant = datetime.now(TIMEZONE)

    while date_actuelle <= derniere_date and len(creneaux) < nombre:

        # Les visites sont interdites le dimanche
        if date_actuelle.weekday() != 6:

            ouverture = datetime.combine(
                date_actuelle, time(9, 0), tzinfo=TIMEZONE
            )

            fermeture = datetime.combine(
                date_actuelle, time(18, 0), tzinfo=TIMEZONE
            )

            debut_creneau = ouverture

            # Examiner les départs possibles toutes les 15 minutes
            while debut_creneau + timedelta(minutes=DUREE_VISITE) <= fermeture:

                fin_creneau = debut_creneau + timedelta(
                    minutes=DUREE_VISITE
                )

                # Vérifier que le créneau appartient à la période demandée
                if (
                    debut_creneau >= debut_periode
                    and fin_creneau <= fin_periode
                    and debut_creneau >= maintenant
                ):

                    # Vérifier qu'aucun événement ne chevauche le créneau
                    occupe = any(
                        debut_creneau < fin_event
                        and fin_creneau > debut_event
                        for debut_event, fin_event in periodes_occupees
                    )

                    if not occupe:
                        creneaux.append({
                            "debut": debut_creneau.isoformat(),
                            "fin": fin_creneau.isoformat()
                        })

                        if len(creneaux) >= nombre:
                            break

                debut_creneau += timedelta(minutes=15)

        date_actuelle += timedelta(days=1)

    return {
        "conseiller_id": conseiller_id,
        "nombre": len(creneaux),
        "creneaux": creneaux,
        "message": (
            "Créneaux disponibles trouvés."
            if creneaux
            else "Aucun créneau disponible sur cette période."
        )
    }


def creer_rendez_vous(
    conseiller_id: int,
    nom_client: str,
    telephone: str,
    adresse: str,
    debut: datetime
) -> dict:
    """Crée un rendez-vous de visite immobilière dans Google Calendar."""

    # Vérifier la présence du fuseau horaire
    if debut.tzinfo is None:
        raise ValueError("La date de début doit contenir un fuseau horaire.")

    # Convertir la date dans le fuseau horaire de l'agence
    debut = debut.astimezone(TIMEZONE)

    # Calculer automatiquement la fin de la visite (45 minutes)
    fin = debut + timedelta(minutes=DUREE_VISITE)

    # Vérifier la disponibilité du conseiller
    disponible = verifier_disponibilite(
        conseiller_id,
        debut,
        fin
    )

    if not disponible:
        raise ValueError("Ce créneau est déjà occupé.")

    # Récupérer le service Google Calendar
    calendar = get_calendar_service()

    # Récupérer l'agenda du conseiller
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
           "timeZone": str(TIMEZONE)
        },
        "end": {
            "dateTime": fin.isoformat(),
           "timeZone": str(TIMEZONE)
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

    # Vérifier que l'identifiant du rendez-vous est fourni
    if not event_id or not event_id.strip():
        raise ValueError("L'identifiant du rendez-vous est obligatoire.")

    # Récupérer le service Google Calendar
    calendar = get_calendar_service()

    # Récupérer l'agenda du conseiller
    calendar_id = get_calendar_id(conseiller_id)

    try:
        # Supprimer le rendez-vous de l'agenda
        calendar.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

    except HttpError as erreur:
        if erreur.resp.status == 404:
            raise ValueError(
                "Ce rendez-vous n'existe pas dans l'agenda du conseiller."
            ) from erreur

        raise

    return {
        "event_id": event_id,
        "message": "Rendez-vous annulé avec succès."
    }