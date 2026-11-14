"""Critère d'acceptation de l'exercice 1 : rejoue les 10 demandes et vérifie les réponses.

Une demande est réussie si :
  - l'agent ne cite QUE des biens qui existent et sont disponibles dans la base ;
  - il cite exactement les biens attendus ;
  - s'il n'y a aucun bien attendu, il le dit clairement ("aucun").

Usage : python -m eval.evaluer_ex1
"""
import json
import re
import sqlite3
import time
from pathlib import Path

from agent.agent_ex1 import DB_PATH_DEFAUT, construire_agent, repondre

PAUSE_S = 12          # respecte la limite de requêtes par minute du palier gratuit
ATTENTE_QUOTA_S = 45  # attente avant de réessayer après une erreur 429 (quota)
ESSAIS_MAX = 3


def repondre_avec_quota(demande: str, agent) -> dict:
    """Relance la demande si l'API répond 'quota dépassé' (ce n'est pas une erreur de l'agent)."""
    for essai in range(1, ESSAIS_MAX + 1):
        r = repondre(demande, agent=agent)
        if "RateLimit" not in r["statut"] and "RESOURCE_EXHAUSTED" not in r["statut"]:
            return r
        print(f"   quota atteint, nouvel essai dans {ATTENTE_QUOTA_S} s ({essai}/{ESSAIS_MAX})")
        time.sleep(ATTENTE_QUOTA_S)
    return r


def ids_disponibles() -> set[str]:
    with sqlite3.connect(DB_PATH_DEFAUT) as conn:
        return {row[0] for row in conn.execute("SELECT id FROM biens WHERE disponible = 1")}


def main() -> None:
    demandes = json.loads(Path("eval/demandes_ex1.json").read_text(encoding="utf-8"))
    base = ids_disponibles()
    agent = construire_agent()
    lignes, reussites = [], 0

    for i, d in enumerate(demandes):
        if i:
            time.sleep(PAUSE_S)
        r = repondre_avec_quota(d["demande"], agent)
        cites = set(re.findall(r"SK-\d{3}", r["reponse"]))
        attendus = set(d["biens_attendus"])

        fonde = cites <= base                      # aucun bien inventé ni indisponible
        exact = cites == attendus
        dit_aucun = bool(attendus) or "aucun" in r["reponse"].lower()
        ok = fonde and exact and dit_aucun and r["statut"] == "ok"
        reussites += ok

        lignes.append((d["id"], "✅" if ok else "❌", ", ".join(sorted(cites)) or "-",
                       ", ".join(sorted(attendus)) or "aucun", r["appels_outils"], r["tokens"], r["duree_s"]))
        print(f"{d['id']} {'✅' if ok else '❌'}  cités={sorted(cites)} attendus={sorted(attendus)}"
              f"  [{r['statut']}]  trace={r.get('fichier_trace')}")

    print("\n| Demande | Résultat | Biens cités | Biens attendus | Appels d'outils | Tokens | Durée (s) |")
    print("|---|---|---|---|---|---|---|")
    for l in lignes:
        print("| " + " | ".join(str(x) for x in l) + " |")
    print(f"\nTaux de réussite : {reussites}/{len(demandes)}")


if __name__ == "__main__":
    main()
