import os
import json
import random
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("APISPORTS_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "Accept": "application/json"}

# 🔁 Temporadas a probar SOLO para el club random
PLAYER_SEASONS = [2023]

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

# IDs estáticos por si el endpoint de búsqueda falla
CLUB_IDS_CACHE = {
    "real madrid": 541,
    "barcelona": 529,
    "atletico madrid": 530,
    "manchester city": 50,
    "manchester united": 33,
    "liverpool": 40,
    "arsenal": 42,
    "chelsea": 49,
    "tottenham": 47,
    "bayern munich": 157,
    "borussia dortmund": 165,
    "psg": 85,
    "juventus": 109,
    "inter": 108,
    "ac milan": 489,
    "roma": 497,
    "napoli": 492,
}


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
    # Primero intento con la caché
    cached_id = CLUB_IDS_CACHE.get(name.lower())
    if cached_id:
        return cached_id

    js = api_get("/teams", {"name": name})
    resp = js.get("response", []) or []

    if not resp:
        # Reintentar con la caché si el API no devuelve resultados
        return CLUB_IDS_CACHE.get(name.lower())

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
        try:
            js = api_get("/players", {
                "team": team_id,
                "season": season,
                "page": page
            })
        except Exception as e:
            print(f"[WARN] Error llamando /players para team={team_id}, season={season}, page={page}: {e}")
            break

        # Si la API responde con errores explícitos, corto
        if js.get("errors"):
            print(f"[WARN] API devolvió errores para team={team_id}, season={season}, page={page}: {js.get('errors')}")
            break

        resp = js.get("response", []) or []
        if not resp:
            # Sin más jugadores en esta página
            break

        for it in resp:
            p = it.get("player") or {}
            stats_list = it.get("statistics") or []
            stats = stats_list[0] if stats_list else {}
            pos = (stats.get("games") or {}).get("position")

            jugadores.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "age": p.get("age"),
                "nationality": p.get("nationality"),
                "position": pos,
                "team_id": team_id,
            })

        paging = js.get("paging") or {}
        current = paging.get("current") or page
        total = paging.get("total") or current

        if current >= total:
            break

        page += 1

    return jugadores
# -------------------------------------------------------------------------------


def get_random_player():
    """
    Devuelve un jugador aleatorio de UN club famoso elegido al azar.

    - Elige un club random de la lista.
    - Para ese club, prueba varias seasons (PLAYER_SEASONS).
    - Si alguna season tiene jugadores, devuelve uno random.
    - Si ninguna season tiene jugadores, lanza error SOLO de ese club.
    """

    # 1) Elegimos UN club famoso al azar
    club_random = random.choice(CLUBES_FAMOSOS)
    print(f"[INFO] Club elegido al azar: {club_random}")

    # 2) Obtenemos su ID
    club_id = get_team_id_by_name(club_random)
    if not club_id:
        raise RuntimeError(f"No se pudo obtener el ID del club: {club_random}")

    # 3) Probamos varias seasons SOLO para este club
    ultimo_mensaje = ""
    for season in PLAYER_SEASONS:
        print(f"[INFO] Buscando jugadores de {club_random} en season={season}...")
        players = get_players_from_team(club_id, season)

        if players:
            print(f"[OK] Encontrados {len(players)} jugadores para {club_random} en season={season}")
            jugador = random.choice(players)
            jugador["team_name"] = club_random
            jugador["season"] = season
            return jugador

        msg = f"No se encontraron jugadores para {club_random} (season {season})"
        print("[WARN]", msg)
        ultimo_mensaje = msg

    # 4) Si llegamos acá, ninguna season devolvió jugadores para ese club
    raise RuntimeError(
        f"No se encontraron jugadores para el club random {club_random} "
        f"en ninguna de las seasons {PLAYER_SEASONS}. Último intento: {ultimo_mensaje}"
    )


def main():
    jugador = get_random_player()
    print(json.dumps(jugador, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
