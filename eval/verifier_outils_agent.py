"""Vérifie que le modèle ne reçoit que des outils de lecture (aucune écriture dans l'agenda)."""
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.agent import charger_outils_lecture, config_mcp


async def main():
    async with MultiServerMCPClient(config_mcp()).session("catalogue") as session:
        outils = await charger_outils_lecture(session)
        print("Outils donnés au modèle :", sorted(o.name for o in outils))


asyncio.run(main())
