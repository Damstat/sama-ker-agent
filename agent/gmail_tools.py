"""Outils Gmail de l'agent Sama Kër (exercice 4)."""
import base64
from email.message import EmailMessage
from email.utils import parseaddr

from googleapiclient.discovery import build

from agent.google_auth import get_credentials

# Les 4 états imposés par le sujet : clé utilisée dans le code -> nom affiché dans Gmail
LIBELLES = {
    "a_traiter": "SK - À traiter",
    "en_attente": "SK - En attente de validation",
    "repondu": "SK - Répondu",
    "transmis": "SK - Transmis à un conseiller",
}

# Expéditeurs automatiques à ignorer (ce ne sont pas des clients)
MOTS_AUTOMATIQUES = ("noreply", "no-reply", "notifications", "mailer-daemon")
DOMAINES_IGNORES = ("google.com", "accounts.google.com")


def service_gmail():
    """Ouvre une connexion à l'API Gmail avec le jeton du compte de test."""
    return build("gmail", "v1", credentials=get_credentials())


def preparer_libelles(service) -> dict:
    """Crée les libellés manquants et renvoie leurs ID : {"a_traiter": "Label_12", ...}."""
    reponse = service.users().labels().list(userId="me").execute()
    existants = {lib["name"]: lib["id"] for lib in reponse["labels"]}

    ids = {}
    for cle, nom in LIBELLES.items():
        if nom not in existants:
            cree = service.users().labels().create(userId="me", body={"name": nom}).execute()
            existants[nom] = cree["id"]
            print(f"Libellé créé : {nom}")
        ids[cle] = existants[nom]
    return ids


def _corps_texte(partie: dict) -> str:
    """Cherche la partie text/plain d'un email (parfois imbriquée) et la décode."""
    if partie.get("mimeType") == "text/plain" and partie.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(partie["body"]["data"]).decode("utf-8", errors="replace")
    for sous_partie in partie.get("parts", []):
        texte = _corps_texte(sous_partie)
        if texte:
            return texte
    return ""


def _est_automatique(adresse: str) -> bool:
    """Vrai si l'email vient d'un robot (Google, notifications...) et non d'un client."""
    adresse = adresse.lower()
    domaine = adresse.split("@")[-1]
    return any(mot in adresse for mot in MOTS_AUTOMATIQUES) or domaine in DOMAINES_IGNORES


def lire_demandes_non_traitees(service, ids: dict, maximum: int = 20) -> list[dict]:
    """Renvoie les emails de clients de la boîte de réception pas encore traités.

    « Non traité » = ni en attente de validation, ni répondu, ni transmis.
    Les emails automatiques sont ignorés. Chaque demande retenue reçoit « À traiter ».
    """
    deja_traites = {ids["en_attente"], ids["repondu"], ids["transmis"]}
    reponse = service.users().messages().list(
        userId="me", labelIds=["INBOX"], maxResults=maximum
    ).execute()

    demandes = []
    for resume in reponse.get("messages", []):
        msg = service.users().messages().get(userId="me", id=resume["id"], format="full").execute()
        libelles_du_message = set(msg.get("labelIds", []))
        if libelles_du_message & deja_traites:
            continue  # déjà traité : on l'ignore

        entetes = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}
        nom, adresse = parseaddr(entetes.get("from", ""))
        if _est_automatique(adresse):
            continue  # email d'un robot : ce n'est pas une demande de client

        if ids["a_traiter"] not in libelles_du_message:
            service.users().messages().modify(
                userId="me", id=msg["id"], body={"addLabelIds": [ids["a_traiter"]]}
            ).execute()

        demandes.append({
            "id": msg["id"],
            "thread_id": msg["threadId"],
            "message_id": entetes.get("message-id", ""),
            "expediteur_nom": nom,
            "expediteur_email": adresse,
            "sujet": entetes.get("subject", "(sans objet)"),
            "corps": _corps_texte(msg["payload"]) or msg.get("snippet", ""),
        })
    return demandes


def creer_brouillon(service, demande: dict, texte: str) -> str:
    """Crée un brouillon de réponse DANS LE FIL de la demande. Rien n'est envoyé.

    Renvoie l'identifiant du brouillon, nécessaire pour l'envoyer après validation.
    """
    sujet = demande["sujet"]
    if not sujet.lower().startswith("re:"):
        sujet = "Re: " + sujet

    message = EmailMessage()
    message["To"] = demande["expediteur_email"]
    message["Subject"] = sujet
    if demande["message_id"]:
        message["In-Reply-To"] = demande["message_id"]
        message["References"] = demande["message_id"]
    message.set_content(texte)

    brut = base64.urlsafe_b64encode(message.as_bytes()).decode()
    brouillon = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": brut, "threadId": demande["thread_id"]}},
    ).execute()
    return brouillon["id"]


def changer_etat(service, ids: dict, message_id: str, nouvel_etat: str) -> None:
    """Remplace le libellé d'état d'un email par nouvel_etat ("en_attente", "repondu"...)."""
    a_retirer = [id_lib for cle, id_lib in ids.items() if cle != nouvel_etat]
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [ids[nouvel_etat]], "removeLabelIds": a_retirer},
    ).execute()


def transmettre_conseiller(service, ids: dict, demande: dict) -> None:
    """Demande hors périmètre : aucune réponse automatique, l'email passe à un humain."""
    changer_etat(service, ids, demande["id"], "transmis")


def demander_validation(demande: dict, texte: str) -> bool:
    """Affiche le brouillon au conseiller et attend sa décision. Seul « o » autorise l'envoi."""
    print("=" * 70)
    print(f"À      : {demande['expediteur_nom']} <{demande['expediteur_email']}>")
    print(f"Objet  : Re: {demande['sujet']}")
    print("-" * 70)
    print(texte)
    print("=" * 70)
    reponse = input("Conseiller : envoyer cette réponse ? (o/n) : ").strip().lower()
    return reponse == "o"


def envoyer_brouillon(service, ids: dict, id_brouillon: str, message_id: str) -> None:
    """Envoie un brouillon DÉJÀ VALIDÉ, puis marque l'email comme répondu."""
    service.users().drafts().send(userId="me", body={"id": id_brouillon}).execute()
    changer_etat(service, ids, message_id, "repondu")


def proposer_reponse(service, ids: dict, demande: dict, texte: str) -> str:
    """Brouillon -> « en attente » -> validation humaine -> envoi seulement si accord."""
    id_brouillon = creer_brouillon(service, demande, texte)
    changer_etat(service, ids, demande["id"], "en_attente")
    if demander_validation(demande, texte):
        envoyer_brouillon(service, ids, id_brouillon, demande["id"])
        return "envoyé"
    return "en attente de validation"


if __name__ == "__main__":
    service = service_gmail()
    ids = preparer_libelles(service)
    demandes = lire_demandes_non_traitees(service, ids)
    print(f"\n{len(demandes)} demande(s) non traitée(s)\n")
    for numero, d in enumerate(demandes, start=1):
        print(f"--- Demande {numero} ---")
        print(f"De     : {d['expediteur_nom']} <{d['expediteur_email']}>")
        print(f"Objet  : {d['sujet']}")
        print(f"Fil    : {d['thread_id']}")
        print(d["corps"].strip()[:400])
        print()
