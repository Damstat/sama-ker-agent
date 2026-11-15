"""Vérifie que chaque demande de test a des biens attendus qui existent et sont disponibles."""
import json
from pathlib import Path

from mcp_server.catalogue import detail_bien

demandes = json.loads(Path("eval/demandes_ex1.json").read_text(encoding="utf-8"))
erreurs = 0

for d in demandes:
    for id_bien in d["biens_attendus"]:
        fiche = detail_bien(id_bien)
        if "erreur" in fiche:
            print(f" {d['id']} : {id_bien} n'existe pas")
            erreurs += 1
        elif fiche["disponible"] != 1:
            print(f" {d['id']} : {id_bien} n'est pas disponible")
            erreurs += 1

print(f"{len(demandes)} demandes vérifiées, {erreurs} erreur(s)")
