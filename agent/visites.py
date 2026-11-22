"""Gestion des visites dans l'agenda, TOUJOURS après l'accord d'un conseiller (exercice 3).

Le modèle n'a aucun outil d'écriture : il propose des créneaux, et c'est ce module,
appelé par le code, qui crée, déplace ou annule une visite après un « o » du conseiller.
"""
import json
from datetime import datetime

from agent.agent import JOURS, MOIS
from agent.calendar_service import (
    CONSEILLERS,
    TIMEZONE,
    annuler_rendez_vous,
    creer_rendez_vous,
    deplacer_rendez_vous,
)


def date_heure_fr(iso: str) -> str:
    """« 2026-11-26T16:30:00+00:00 » -> « jeudi 26 novembre 2026 à 16 h 30 »."""
    d = datetime.fromisoformat(iso).astimezone(TIMEZONE)
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year} à {d.hour} h {d.minute:02d}"


def demander_accord(resume: str) -> bool:
    """Affiche l'action prévue et attend la décision du conseiller. Seul « o » l'autorise."""
    print("=" * 70)
    print(resume)
    print("=" * 70)
    return input("Conseiller : confirmer cette action ? (o/n) : ").strip().lower() == "o"


def planifier_visite(conseiller_id: int, nom_client: str, adresse: str, debut: str,
                     telephone: str = "non communiqué") -> dict:
    """Crée une visite de 45 min après accord. La disponibilité est revérifiée juste avant."""
    resume = (f"CRÉER une visite\n- Conseiller : {CONSEILLERS[conseiller_id]}\n"
              f"- Client : {nom_client}\n- Bien : {adresse}\n- Date : {date_heure_fr(debut)}")
    if not demander_accord(resume):
        return {"statut": "refusé par le conseiller"}
    try:
        resultat = creer_rendez_vous(conseiller_id, nom_client, telephone, adresse,
                                     datetime.fromisoformat(debut))
        return {"statut": "créé", "conseiller_id": conseiller_id, **resultat}
    except ValueError as erreur:  # créneau pris entre-temps, dimanche, hors horaires...
        return {"statut": "impossible", "erreur": str(erreur)}


def deplacer_visite(conseiller_id: int, event_id: str, nouveau_debut: str) -> dict:
    """Déplace une visite après accord, si le nouveau créneau est libre."""
    resume = (f"DÉPLACER une visite\n- Conseiller : {CONSEILLERS[conseiller_id]}\n"
              f"- Nouvelle date : {date_heure_fr(nouveau_debut)}")
    if not demander_accord(resume):
        return {"statut": "refusé par le conseiller"}
    try:
        resultat = deplacer_rendez_vous(conseiller_id, event_id, datetime.fromisoformat(nouveau_debut))
        return {"statut": "déplacé", **resultat}
    except ValueError as erreur:
        return {"statut": "impossible", "erreur": str(erreur)}


def annuler_visite(conseiller_id: int, event_id: str) -> dict:
    """Annule une visite après accord."""
    resume = f"ANNULER une visite\n- Conseiller : {CONSEILLERS[conseiller_id]}\n- Visite : {event_id}"
    if not demander_accord(resume):
        return {"statut": "refusé par le conseiller"}
    try:
        return {"statut": "annulé", **annuler_rendez_vous(conseiller_id, event_id)}
    except ValueError as erreur:
        return {"statut": "impossible", "erreur": str(erreur)}


def resultats_outil(trace: list, nom_outil: str) -> list[dict]:
    """Relit dans la trace de l'agent les résultats (JSON) renvoyés par un outil donné."""
    resultats = []
    for etape in trace:
        if etape.get("etape") == "resultat_outil" and etape.get("outil") == nom_outil:
            try:
                resultats.append(json.loads(etape["resultat"]))
            except (json.JSONDecodeError, TypeError):
                pass
    return resultats


def creneaux_proposes(trace: list) -> list[dict]:
    """Les créneaux réellement renvoyés par lister_creneaux_libres pendant le traitement."""
    return [c for r in resultats_outil(trace, "lister_creneaux_libres") for c in r.get("creneaux", [])]
