"""Exercice 6 : rejoue les 15 emails de test et mesure ce que l'agent traite correctement.

Pour chaque email : classification (répondre ou transmettre), puis, s'il faut répondre,
rédaction par l'agent (catalogue + agenda). Rien n'est envoyé et aucun brouillon n'est créé.

Mesures : réussite, appels d'outils, tokens, durée. Résultats dans eval/resultats/.

Usage (une seule commande) :
    python -m eval.evaluer_ex6 --etiquette avant
    python -m eval.evaluer_ex6 --etiquette apres      # produit aussi le tableau avant / après
"""
import argparse
import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from agent.agent import ouvrir_agent
from agent.calendar_service import (
    TIMEZONE,
    annuler_rendez_vous,
    creer_rendez_vous,
    verifier_disponibilite,
)
from agent.classifieur import classer_email
from agent.traiter_emails import rediger_reponse
from agent.visites import creneaux_proposes

DOSSIER = Path(__file__).resolve().parent
RESULTATS = DOSSIER / "resultats"


def prochain(jour_semaine: int) -> datetime:
    """Le prochain jour de la semaine demandé (0 = lundi), à partir de demain."""
    aujourd_hui = datetime.now(TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    ecart = (jour_semaine - aujourd_hui.weekday()) % 7 or 7
    return aujourd_hui + timedelta(days=ecart)


def bloquer_samedi_10h() -> tuple[datetime, list]:
    """Rend le créneau « samedi prochain 10 h » occupé chez les 3 conseillers (scénario E08)."""
    debut = prochain(5).replace(hour=10)
    bloques = []
    for conseiller_id in (1, 2, 3):
        try:
            evt = creer_rendez_vous(conseiller_id, "Créneau bloqué (test ex6)", "-", "test", debut)
            bloques.append((conseiller_id, evt["id"]))
        except ValueError:
            pass  # déjà occupé : c'est ce qu'on veut
    return debut, bloques


def verifier_creneaux(creneaux: list, attendu: dict, interdit: datetime) -> tuple[bool | None, str]:
    """Contrôle les créneaux proposés : présents ou non, réellement libres, au bon moment."""
    regle = attendu.get("creneaux")
    if regle == "non":
        return (not creneaux), ("aucun créneau proposé" if not creneaux else "créneaux alors qu'aucun bien")
    if regle == "oui" and not creneaux:
        return False, "aucun créneau proposé"
    for c in creneaux:
        debut = datetime.fromisoformat(c["debut"]).astimezone(TIMEZONE)
        fin = debut + timedelta(minutes=45)
        if attendu.get("interdit") and debut < interdit + timedelta(minutes=45) and fin > interdit:
            return False, f"créneau occupé proposé ({debut:%a %H:%M})"
        if "jour_semaine" in attendu:
            debut_plage, fin_plage = attendu["plage"]
            if debut.date() != prochain(attendu["jour_semaine"]).date() or not (
                    debut_plage <= debut.hour and fin.hour * 60 + fin.minute <= fin_plage * 60):
                return False, f"créneau hors de la demande ({debut:%d/%m %H:%M})"
        try:
            if not verifier_disponibilite(c["conseiller_id"], debut, fin):
                return False, f"créneau pas réellement libre ({debut:%d/%m %H:%M})"
        except ValueError as erreur:
            return False, f"créneau invalide : {erreur}"
    if regle is None and not attendu.get("interdit"):
        return None, "non contrôlé"
    return True, f"{len(creneaux)} créneau(x) libre(s)"


async def evaluer_un_email(agent, email: dict, interdit: datetime) -> dict:
    attendu = email["attendu"]
    debut = time.perf_counter()
    classement = classer_email(email["sujet"], email["corps"])
    decision = "transmettre" if classement["categorie"] == "hors_perimetre" else "repondre"
    ligne = {"id": email["id"], "categorie": email["categorie"], "decision": decision,
             "methode_classement": classement["methode"], "appels_outils": 0, "tokens": 0,
             "biens_cites": [], "creneaux": [], "trace": None, "statut": "ok"}

    if decision == "repondre":
        demande = {"expediteur_nom": "", "sujet": email["sujet"], "corps": email["corps"]}
        for tentative in range(3):  # quota du palier gratuit : on réessaie après une pause
            redaction = await rediger_reponse(agent, demande)
            if "429" not in redaction["statut"] and "RESOURCE_EXHAUSTED" not in redaction["statut"]:
                break
            await asyncio.sleep(30)
        ligne.update(statut=redaction["statut"], appels_outils=redaction["appels_outils"],
                     tokens=redaction["tokens"], trace=redaction.get("fichier_trace"),
                     reponse=redaction["reponse"])
        ligne["biens_cites"] = sorted(set(re.findall(r"SK-\d{3}", redaction["reponse"])))
        ligne["creneaux"] = creneaux_proposes(redaction["trace"])

    ligne["duree_s"] = round(time.perf_counter() - debut, 2)

    # Contrôles
    controles = {"decision": decision == attendu["decision"]}
    if decision == "repondre" and attendu["decision"] == "repondre":
        controles["statut"] = ligne["statut"] == "ok"
        if attendu.get("biens") is not None:
            controles["biens"] = ligne["biens_cites"] == sorted(attendu["biens"])
        ok_creneaux, detail = verifier_creneaux(ligne["creneaux"], attendu, interdit)
        if ok_creneaux is not None:
            controles["creneaux"] = ok_creneaux
        ligne["detail_creneaux"] = detail
    ligne["controles"] = controles
    ligne["reussi"] = all(controles.values())
    return ligne


def tableau(lignes: list) -> str:
    entete = ("| Email | Catégorie | Décision | Biens cités | Créneaux | Appels d'outils | Tokens "
              "| Durée (s) | Résultat |\n|---|---|---|---|---|---|---|---|---|\n")
    corps = "".join(
        f"| {l['id']} | {l['categorie']} | {l['decision']} | {', '.join(l['biens_cites']) or '-'} "
        f"| {l.get('detail_creneaux', '-')} | {l['appels_outils']} | {l['tokens']} | {l['duree_s']} "
        f"| {'✅' if l['reussi'] else '❌ ' + ', '.join(k for k, v in l['controles'].items() if not v)} |\n"
        for l in lignes)
    n = sum(l["reussi"] for l in lignes)
    total = (f"\n**Taux de réussite : {n}/{len(lignes)}** · appels d'outils : "
             f"{sum(l['appels_outils'] for l in lignes)} · tokens : {sum(l['tokens'] for l in lignes)} · "
             f"durée moyenne : {sum(l['duree_s'] for l in lignes) / len(lignes):.1f} s par email\n")
    return entete + corps + total


def comparaison() -> str | None:
    fichiers = {e: RESULTATS / f"ex6_{e}.json" for e in ("avant", "apres")}
    if not all(f.exists() for f in fichiers.values()):
        return None
    avant, apres = (json.loads(f.read_text(encoding="utf-8")) for f in fichiers.values())
    lignes = "".join(
        f"| {a['id']} | {a['categorie']} | {'✅' if a['reussi'] else '❌'} | {'✅' if b['reussi'] else '❌'} |\n"
        for a, b in zip(avant["lignes"], apres["lignes"]))
    return ("# Exercice 6 · résultats avant / après correction\n\n"
            f"Avant : {avant['date']} · Après : {apres['date']}\n\n"
            "| Email | Catégorie | Avant | Après |\n|---|---|---|---|\n" + lignes +
            f"\n**Taux de réussite : {avant['reussis']}/15 avant → {apres['reussis']}/15 après**\n")


async def main(etiquette: str) -> None:
    emails = json.loads((DOSSIER / "emails_test_ex6.json").read_text(encoding="utf-8"))
    interdit, bloques = bloquer_samedi_10h()
    lignes = []
    try:
        async with ouvrir_agent() as agent:
            for email in emails:
                ligne = await evaluer_un_email(agent, email, interdit)
                print(f"{ligne['id']} {'✅' if ligne['reussi'] else '❌'} {ligne['categorie']} "
                      f"→ {ligne['decision']} {ligne['biens_cites'] or ''} {ligne.get('detail_creneaux', '')}")
                lignes.append(ligne)
                await asyncio.sleep(5)  # ménage le quota du palier gratuit
    finally:
        for conseiller_id, event_id in bloques:  # on libère le créneau bloqué pour le test
            annuler_rendez_vous(conseiller_id, event_id)

    RESULTATS.mkdir(exist_ok=True)
    reussis = sum(l["reussi"] for l in lignes)
    donnees = {"etiquette": etiquette, "date": datetime.now().isoformat(timespec="seconds"),
               "reussis": reussis, "lignes": lignes}
    (RESULTATS / f"ex6_{etiquette}.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"# Exercice 6 · résultats « {etiquette} » ({donnees['date']})\n\n" + tableau(lignes)
    (RESULTATS / f"ex6_{etiquette}.md").write_text(md, encoding="utf-8")
    print("\n" + md)

    comp = comparaison()
    if comp:
        (RESULTATS / "ex6_avant_apres.md").write_text(comp, encoding="utf-8")
        print(comp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Évaluation de l'agent sur 15 emails de test")
    parser.add_argument("--etiquette", default="apres", help="avant ou apres (défaut : apres)")
    asyncio.run(main(parser.parse_args().etiquette))
