import os
import json
import random
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("APISPORTS_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "Accept": "application/json"}

# Los jugadores siempre están cargados en la temporada 2023
PLAYER_SEASON = 2023  

# --- CLUBES FAMOSOS ---
CLUBES_FAMOSOS = [
    "Real Madrid",
    "Barcelona",
    "Atletico Madrid",
    "Manchester City",
    "Manchester United",
    "Liverpool",
    "Arsenal",
    "Chelsea",
    "Tottenham",
    "Bayern Munich",
    "Borussia Dortmund",
    "PSG",
    "Juventus",
    "Inter",
    "AC Milan",
    "Roma",
    "Napoli"
]


def api_get(path, params=None):
    if not API_KEY:
        raise RuntimeError("Falta la variable de entorno APISPORTS_KEY")

    r = requests.get(
        f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30
    )
    r.raise_for_status()
    return r.json()


# ----------------------------- OBTENER ID DEL CLUB -----------------------------
def get_team_id_by_name(name: str):
    js = api_get("/teams", {"name": name})
    resp = js.get("response", []) or []

    if not resp:
        return None

    exact = [
        it for it in resp 
        if (it.get("team") or {}).get("name", "").lower() == name.lower()
    ]

    t = (exact[0].get("team") if exact else resp[0].get("team")) or {}
    return t.get("id")
# -------------------------------------------------------------------------------


# -------------------------- JUGADORES DEL CLUB --------------------------------
def get_players_from_team(team_id: int, season: int):
    jugadores = []
    page = 1

    while True:
        js = api_get("/players", {
            "team": team_id,
            "season": season,
            "page": page
        })

        resp = js.get("response", []) or []

        for it in resp:
            p = it.get("player") or {}
            stats = it.get("statistics")[0] if it.get("statistics") else {}
            pos = stats.get("games", {}).get("position")

            jugadores.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "age": p.get("age"),
                "nationality": p.get("nationality"),
                "position": pos,
                "team_id": team_id
            })

        paging = js.get("paging") or {}
        if paging.get("current") >= paging.get("total"):
            break

        page += 1

    return jugadores
# -------------------------------------------------------------------------------


def get_random_player():
    """
    Devuelve un jugador aleatorio de un club famoso.

    Se usa tanto en el servidor Flask (para Vercel) como al ejecutar el
    script directamente.
    """

    # Elegimos un club famoso al azar
    club_random = random.choice(CLUBES_FAMOSOS)

    # Obtenemos su ID real desde API
    club_id = get_team_id_by_name(club_random)

    if not club_id:
        raise RuntimeError(f"No se pudo obtener el ID del club: {club_random}")

    # Buscar jugadores de ese club
    players = get_players_from_team(club_id, PLAYER_SEASON)

    if not players:
        raise RuntimeError(f"No se encontraron jugadores para {club_random}")

    # Elegir jugador conocido al azar
    jugador = random.choice(players)
    jugador["team_name"] = club_random

    return jugador


def main():
    jugador = get_random_player()
    print(json.dumps(jugador, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
