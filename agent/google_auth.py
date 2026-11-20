"""Connexion OAuth au compte Google de test (Gmail + Calendar)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Strict nécessaire, identique à l'écran de consentement
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
]
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")


def get_credentials() -> Credentials:
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("Ancien jeton renouvelé avec succès.")

        except RefreshError:
            print("Ancien jeton refusé. Nouvelle authentification nécessaire.")
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES
        )

        creds = flow.run_local_server(
            port=0,
            prompt="consent",
            access_type="offline"
        )

    Path(TOKEN_FILE).write_text(creds.to_json())

    return creds


if __name__ == "__main__":
    creds = get_credentials()

    gmail = build("gmail", "v1", credentials=creds)
    profil = gmail.users().getProfile(userId="me").execute()
    print("Gmail OK :", profil["emailAddress"])

    calendar = build("calendar", "v3", credentials=creds)
    for i in (1, 2, 3):
        cal_id = os.getenv(f"CALENDAR_ID_CONSEILLER_{i}")
        calendar.events().list(calendarId=cal_id, maxResults=1).execute()
        print(f"Agenda conseiller {i} OK")
