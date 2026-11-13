# Sama Kër Immobilier — Agent de traitement des demandes de visite

Agent IA qui traite les demandes de visite de l'agence fictive **Sama Kër Immobilier** (Dakar) :
lecture des emails Gmail, recherche dans le catalogue de biens, proposition de créneaux
libres dans Google Calendar, rédaction de la réponse et inscription de la visite.
**Aucun email n'est envoyé et aucune visite n'est créée sans la validation d'un conseiller.**

Projet réalisé dans le cadre du programme Data & IA — Orange Digital Center.

## Équipe

| Membre | Rôle principal |
|---|---|
| Adama Sarr | Boucle de l'agent, pipeline complet, validation humaine |
| Sine Ndoye Seck | Catalogue SQLite, serveur MCP, script d'évaluation |
| Yaye Aminata Ndiaye | Accès Google (OAuth), Google Calendar, Gmail |

## Architecture

```
            Email client
                 │
                 ▼
┌──────────────────────────────────┐
│ Agent (LangGraph + Gemini)       │──► Serveur MCP catalogue (SQLite)
│ boucle, état, étapes limitées    │──► Google Calendar (créneaux, visites)
└──────────────────────────────────┘──► Gmail (lecture, brouillons, envoi)
        │                    │
        ▼                    ▼
  Traces / journal   Validation par un conseiller
```

| Brique | Choix |
|---|---|
| Modèle | Gemini Flash (palier gratuit Google AI Studio) |
| Framework d'agent | LangGraph |
| Catalogue | SQLite (30 biens fictifs) exposé par un serveur MCP (FastMCP) |
| Agenda / Messagerie | API Google Calendar / API Gmail, sur un compte de test |
| Validation humaine | Gradio ou ligne de commande |

## Organisation du dépôt

```
sama-ker-agent/
├── agent/          # code de l'agent (boucle, outils Calendar et Gmail, validation)
├── mcp_server/     # serveur MCP du catalogue
├── data/           # script de création de la base SQLite
├── eval/           # 15 emails de test, résultats attendus, script d'évaluation
├── traces/         # traces de traitements complets
├── .env.example    # modèle de configuration (sans secrets)
├── requirements.txt
└── README.md
```

## Installation

### Prérequis

- Python 3.11 ou plus récent
- Git
- Accès au compte Google de test de l'équipe (demander à Adama ou Yaye)

### 1. Cloner le dépôt

```powershell
git clone https://github.com/Damstat/sama-ker-agent.git
cd sama-ker-agent
```

### 2. Créer l'environnement virtuel

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Sous Windows, si l'activation est bloquée :
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
>
> Sous macOS / Linux : `source .venv/bin/activate`

### 3. Configurer les secrets

```powershell
copy .env.example .env
```

Remplir le fichier `.env` avec les vraies valeurs, transmises en privé par l'équipe :

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Clé API Gemini (Google AI Studio, compte de test) |
| `MODEL_NAME` | Nom du modèle, ex. `gemini-2.5-flash` |
| `CALENDAR_ID_CONSEILLER_1..3` | ID des trois agendas des conseillers |
| `GOOGLE_CREDENTIALS_FILE` | Chemin du fichier OAuth `credentials.json` |
| `DB_PATH` | Chemin de la base SQLite du catalogue |
| `MCP_SERVER_URL` | Adresse du serveur MCP en mode HTTP |

Placer aussi le fichier `credentials.json` (identifiant OAuth Google) à la racine du projet.

### 4. Configuration des accès Google
