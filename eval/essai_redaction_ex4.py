"""Essai de la rédaction (exercice 4) sur les 3 demandes de visite. Ne crée aucun brouillon."""
import asyncio
import re

from agent.agent import ouvrir_agent
from agent.gmail_tools import lire_demandes_non_traitees, preparer_libelles, service_gmail
from agent.traiter_emails import rediger_reponse

# Biens attendus, repérés par un mot de l'objet (vérifiés dans la base)
ATTENDU = {
    "Yoff": set(),
    "Ouakam": {"SK-017"},
    "Sacré": {"SK-008", "SK-009", "SK-010"},
}


async def main() -> None:
    service = service_gmail()
    ids = preparer_libelles(service)
    demandes = lire_demandes_non_traitees(service, ids)

    async with ouvrir_agent() as agent:
        for mot, attendus in ATTENDU.items():
            demande = next((d for d in demandes if mot in d["sujet"]), None)
            if demande is None:
                print(f"⚠️ Aucune demande non traitée contenant « {mot} »\n")
                continue

            resultat = await rediger_reponse(agent, demande)
            cites = set(re.findall(r"SK-\d{3}", resultat["reponse"]))
            ok = resultat["statut"] == "ok" and cites == attendus
            print("=" * 70)
            print(f"{'✅' if ok else '❌'} {demande['sujet']}")
            print(f"   biens cités : {sorted(cites) or 'aucun'} | attendus : {sorted(attendus) or 'aucun'}")
            print(f"   {resultat['appels_outils']} appel(s) d'outil · {resultat['tokens']} tokens · "
                  f"{resultat['duree_s']} s · {resultat['statut']}")
            print("-" * 70)
            print(resultat["reponse"])
            await asyncio.sleep(5)  # ménage le quota du palier gratuit


asyncio.run(main())
