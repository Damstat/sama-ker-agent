"""Essai de la validation humaine (exercice 4) sur les emails « Test validation »."""
from agent.gmail_tools import (
    lire_demandes_non_traitees,
    preparer_libelles,
    proposer_reponse,
    service_gmail,
)

service = service_gmail()
ids = preparer_libelles(service)
demandes = lire_demandes_non_traitees(service, ids)
tests = sorted(
    (d for d in demandes if d["sujet"].startswith("Test validation")),
    key=lambda d: d["sujet"],
)

for d in tests:
    texte = f"""Bonjour {d['expediteur_nom']},

Merci pour votre message.

Nous avons un appartement disponible qui correspond à votre recherche :

SK-017 · Appartement F2 · Ouakam
- Loyer : 180 000 F CFA par mois
- Adresse : Rue OK-9, Ouakam, Dakar
- Description : F2 en rez-de-chaussée

Les visites ont lieu du lundi au samedi, de 9 h à 18 h, et durent 45 minutes. Un conseiller vous proposera très prochainement des créneaux disponibles.

Pour information, nos conditions de location sont les suivantes : caution de 2 mois, 1 mois d'avance à la signature et 1 mois de frais d'agence.

Nous restons à votre disposition pour toute question.

Cordialement,
L'équipe Sama Kër Immobilier"""
    resultat = proposer_reponse(service, ids, d, texte)
    print(f"→ {d['sujet']} : {resultat}\n")
