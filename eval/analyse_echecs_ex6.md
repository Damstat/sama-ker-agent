# Exercice 6 · Analyse de trois échecs

Passage « avant » du 22/11/2026 : 14/15 (voir `eval/resultats/ex6_avant.md`).
Traces complètes dans `eval/traces_livrables/`.

## Échec 1 · E05 « Villa à Yoff » (échec, corrigé)

- Trace (`E05_echec_villa_yoff.json`) : `rechercher_biens {"pieces_min": 4, "type_bien": "Villa"}`.
  Le quartier « Yoff » a disparu des arguments.
- Cause : Yoff ne fait pas partie des zones couvertes (ressource `agence://infos`) ; le modèle
  a retiré le quartier, obtenu toutes les villas du catalogue (SK-013, SK-014, SK-028) et les a
  présentées comme des « quartiers voisins », avec des créneaux de visite.
- Origine : la consigne « propose d'élargir la recherche » a été comprise comme « élargis-la toi-même ».
- Correction : la consigne impose de toujours transmettre le quartier demandé, et, si aucun bien
  ne correspond, de citer les zones couvertes sans lancer d'autre recherche ni proposer d'autre bien.
- Résultat après correction : voir `eval/resultats/ex6_avant_apres.md`.

## Échec 2 · E09 « Je cherche un logement » (échec masqué par le jeu de test)

- Trace (`E09_demande_ambigue.json`) : `rechercher_biens {}` sans aucun critère ; l'agent liste les
  5 biens les moins chers et propose des créneaux.
- Cause : la consigne impose d'appeler `rechercher_biens` dans tous les cas.
- Pourquoi le test était vert : l'attendu ne contrôlait pas les biens (`"biens": null`).
  Le jeu de test était trop permissif sur ce cas.
- Piste de correction : sans quartier, type ni budget, demander des précisions au lieu de chercher.

## Échec 3 · E08 « samedi 10 h précises » (cas limite)

- Trace (`E08_creneau_deja_pris.json`) : `lister_creneaux_libres` le samedi 28 de 9 h à 18 h ;
  créneaux proposés 9 h 00, 9 h 15 et 10 h 45. Le créneau bloqué (10 h à 10 h 45) est bien évité.
- Défauts : la réponse n'explique pas que 10 h est pris ; 9 h 00 et 9 h 15 se chevauchent
  (deux propositions presque identiques) ; un budget est redemandé sans nécessité.
- Piste de correction : signaler explicitement l'indisponibilité de l'heure demandée et proposer
  des créneaux qui ne se chevauchent pas.

## Régression observée après la correction · E07 « F4 à Fann, budget 300 000 F »

- Avant : ✅ · Après : ❌ (créneaux recherchés alors qu'aucun bien ne correspond).
- Trace (`E07_regression_budget.json`) : `rechercher_biens {"type_bien": "Appartement", "pieces_min": 4, "quartier": "Fann"}`.
  Le budget (`loyer_max: 300000`) a disparu des arguments : le catalogue renvoie SK-030 (600 000 F),
  le modèle appelle alors `lister_creneaux_libres`, puis écarte lui-même le bien en rédigeant.
- L'email envoyé au client reste correct (aucun bien, aucun créneau), mais :
  le filtrage du budget a été fait par le raisonnement du modèle et non par l'outil,
  et un appel d'outil inutile a été consommé.
- Cause racine commune avec E05 : le modèle retire parfois un critère du client dans l'appel
  d'outil. La correction d'E05 visait le quartier seulement (le symptôme), pas la cause générale.
- Piste de correction : extraire les critères (quartier, type, pièces, budget) dans le code avec
  une sortie structurée, puis appeler le catalogue de façon déterministe.

## Bilan

| Passage | Réussite | Appels d'outils | Tokens | Durée moyenne |
|---|---|---|---|---|
| Avant | 14/15 | 20 | 101 519 | 14,8 s |
| Après | 14/15 | 20 | 103 082 | 8,7 s |

La correction a réglé E05 mais révélé une régression sur E07 : rejouer le jeu complet après
chaque correction est indispensable avec un modèle de langage, dont le comportement n'est
jamais parfaitement déterministe.
