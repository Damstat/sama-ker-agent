"""Client MCP minimal : vérifie qu'un serveur Sama Kër répond et montre comment l'appeler.

Usage :
    python -m mcp_server.exemple_client                               # lance le serveur en stdio
    python -m mcp_server.exemple_client --url http://127.0.0.1:8000/mcp  # serveur déjà lancé en HTTP
"""
import argparse
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

RACINE = Path(__file__).resolve().parents[1]


async def demo(session: ClientSession) -> None:
    await session.initialize()

    outils = await session.list_tools()
    print("Outils :", [o.name for o in outils.tools])

    ressources = await session.list_resources()
    print("Ressources :", [str(r.uri) for r in ressources.resources])

    r = await session.call_tool("rechercher_biens",
                                {"quartier": "Mermoz", "pieces_min": 3, "loyer_max": 400000})
    print("\nrechercher_biens(quartier='Mermoz', pieces_min=3, loyer_max=400000) ->")
    print(r.content[0].text)

    r = await session.call_tool("detail_bien", {"id_bien": "SK-999"})
    print("\ndetail_bien('SK-999') ->")
    print(r.content[0].text)

    infos = await session.read_resource("agence://infos")
    print("\nagence://infos ->")
    print(infos.contents[0].text[:300], "...")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="URL du serveur HTTP, ex. http://127.0.0.1:8000/mcp")
    args = parser.parse_args()

    if args.url:
        async with streamablehttp_client(args.url) as (lecture, ecriture, _):
            async with ClientSession(lecture, ecriture) as session:
                await demo(session)
    else:
        params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
                                       cwd=str(RACINE))
        async with stdio_client(params) as (lecture, ecriture):
            async with ClientSession(lecture, ecriture) as session:
                await demo(session)


if __name__ == "__main__":
    asyncio.run(main())
