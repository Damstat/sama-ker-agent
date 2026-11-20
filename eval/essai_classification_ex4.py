"""Essai de la classification (exercice 4) sur les demandes non traitées. Ne modifie rien."""
from agent.classifieur import classer_email
from agent.gmail_tools import lire_demandes_non_traitees, preparer_libelles, service_gmail

# Résultat attendu, repéré par un mot de l'objet
ATTENDU = {
    "loyer": "hors_perimetre",
    "Yoff": "visite",
    "Ouakam": "visite",
    "urgente": "hors_perimetre",
    "Sacré": "visite",
}

service = service_gmail()
ids = preparer_libelles(service)
demandes = lire_demandes_non_traitees(service, ids)

reussis = 0
for d in demandes:
    resultat = classer_email(d["sujet"], d["corps"])
    attendu = next((v for mot, v in ATTENDU.items() if mot in d["sujet"]), "?")
    ok = resultat["categorie"] == attendu
    reussis += ok
    print(f"{'✅' if ok else '❌'} {d['sujet'][:35]:35} → {resultat['categorie']:15} "
          f"(attendu : {attendu}, méthode : {resultat['methode']})")
    print(f"   raison : {resultat['raison']}\n")

print(f"Score : {reussis}/{len(demandes)}")
