"""Démonstration du critère de l'exercice 3.

1. « jeudi prochain en fin d'après-midi » -> l'agent propose 3 créneaux réellement libres ;
2. création de la visite après accord du conseiller (bon conseiller, bonne adresse) ;
3. deuxième demande sur le même créneau -> refusée : aucun doublon ;
4. déplacement puis annulation, chacun après accord.

Usage : python -m eval.essai_agenda_ex3
"""
import asyncio

from agent.agent import ouvrir_agent, repondre
from agent.visites import (
    annuler_visite,
    creneaux_proposes,
    date_heure_fr,
    deplacer_visite,
    planifier_visite,
)

DEMANDE = "Bonjour, je voudrais visiter un appartement jeudi prochain en fin d'après-midi. Quels créneaux avez-vous ?"
CLIENT, ADRESSE = "Client Test Ex3", "Rue OK-9, Ouakam, Dakar"


async def main() -> None:
    print("① Demande :", DEMANDE, "\n")
    async with ouvrir_agent() as agent:
        resultat = await repondre(DEMANDE, agent)
    print(resultat["reponse"], "\n")

    creneaux = creneaux_proposes(resultat["trace"])
    print(f"Créneaux renvoyés par l'outil ({len(creneaux)}) :")
    for c in creneaux:
        print(f"  - {date_heure_fr(c['debut'])} avec {c['conseiller']}")
    if len(creneaux) < 2:
        print("Pas assez de créneaux pour la suite de la démonstration.")
        return

    print("\n② Création de la visite sur le premier créneau")
    premier = creneaux[0]
    visite = planifier_visite(premier["conseiller_id"], CLIENT, ADRESSE, premier["debut"])
    print("→", visite)
    if visite["statut"] != "créé":
        return

    print("\n③ Même créneau, même conseiller : il ne doit PAS y avoir de doublon")
    doublon = planifier_visite(premier["conseiller_id"], CLIENT, ADRESSE, premier["debut"])
    print("→", doublon)

    input("\nVérifie la visite dans Google Agenda (conseiller, adresse), puis appuie sur Entrée...")

    print("\n④ Déplacement vers le deuxième créneau")
    print("→", deplacer_visite(premier["conseiller_id"], visite["id"], creneaux[1]["debut"]))

    print("\n⑤ Annulation")
    print("→", annuler_visite(premier["conseiller_id"], visite["id"]))


asyncio.run(main())
