# ids_ligas_equipos_y_random_name.py
import os, json, random, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("APISPORTS_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS  = {"x-apisports-key": API_KEY, "Accept": "application/json"}

SEASON = 2024  # 2024/25

TOP5_LEAGUE_NAMES = [
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
]

EQUIPOS_POOL = [
    "Manchester City", "Arsenal", "Liverpool", "Chelsea", "Manchester United", "Tottenham",
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Valencia",
    "Inter", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio",
    "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
    "Paris Saint Germain", "Monaco", "Marseille", "Lyon", "Lille"
]

def get(path, params=None):
    if not API_KEY:
        raise SystemExit("Falta APISPORTS_KEY en .env")
    r = requests.get(f"{BASE_URL}{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def get_league_id_by_name(league_name: str):
    """Devuelve el ID de la liga (prioriza una temporada 'current' si existe)."""
    js = get("/leagues", {"name": league_name})
    best = None
    for item in js.get("response", []) or []:
        lg = item.get("league") or {}
        seasons = item.get("seasons") or []
        is_current = any(s.get("current") for s in seasons)
        if lg.get("id") is None:
            continue
        cand = {"id": lg["id"], "current": is_current}
        if best is None or (cand["current"] and not (best["current"])):
            best = cand
    return best["id"] if best else None

def get_all_teams_in_league(league_id: int, season: int):
    """Devuelve todos los equipos de una liga en una temporada (con paginación)."""
    teams = []
    page = 1
    while True:
        js = get("/teams", {"league": league_id, "season": season, "page": page})
        resp = js.get("response", []) or []
        for it in resp:
            t = it.get("team") or {}
            v = it.get("venue") or {}
            teams.append({
                "id": t.get("id"),
                "name": t.get("name"),
                "code": t.get("code"),
                "country": it.get("country",{}).get("name") or None,
                "venue": v.get("name"),
            })
        paging = js.get("paging") or {}
        if paging.get("current", page) >= paging.get("total", page):
            break
        page += 1
    return teams

def get_team_id_by_name(team_name: str):
    """
    OBLIGATORIO: usar /teams?name=<team_name> para obtener el ID del equipo por nombre.
    Devuelve {id, name} o None si no hay coincidencias.
    """
    js = get("/teams", {"name": team_name})
    resp = js.get("response", []) or []
    if not resp:
        return None
    # Preferimos coincidencia exacta por nombre (case-insensitive)
    exact = [it for it in resp if (it.get("team") or {}).get("name","").lower() == team_name.lower()]
    t = (exact[0].get("team") if exact else resp[0].get("team")) or {}
    return {"id": t.get("id"), "name": t.get("name")}

def validate_team_in_top5(team_id: int, league_ids: dict, season: int):
    """
    Verifica que el team_id pertenezca a alguna de las 5 grandes ligas en la season dada.
    Lo hacemos consultando /teams?league=<lid>&season=<season>&search=<team_id>
    y comparando IDs dentro de la respuesta.
    """
    for lname, lid in league_ids.items():
        if not lid:
            continue
        js = get("/teams", {"league": lid, "season": season, "search": team_id})
        for it in js.get("response", []) or []:
            t = (it.get("team") or {})
            if t.get("id") == team_id:
                # Devuelve liga donde lo encontró
                return {"league_id": lid, "league_name": lname}
    return None

def main():
    result = {"season": SEASON, "leagues": [], "random_team": None}

    # 1) IDs de las 5 ligas + sus equipos
    league_ids = {}
    for lname in TOP5_LEAGUE_NAMES:
        lid = get_league_id_by_name(lname)
        league_ids[lname] = lid
        teams = get_all_teams_in_league(lid, SEASON) if lid else []
        result["leagues"].append({
            "name": lname,
            "id": lid,
            "teams": teams,
            "count": len(teams),
        })

    # 2) Equipo random del pool -> resolver ID usando /teams?name=<...>
    if EQUIPOS_POOL:
        candidato = random.choice(EQUIPOS_POOL)
        t_basic = get_team_id_by_name(candidato)  # ← usa ?name
        liga_ok = None
        if t_basic and t_basic["id"]:
            liga_ok = validate_team_in_top5(t_basic["id"], league_ids, SEASON)

        result["random_team"] = {
            "requested_name": candidato,
            "resolved": {
                "id": (t_basic or {}).get("id"),
                "name": (t_basic or {}).get("name"),
                "league": liga_ok  # None si no pertenece a top-5 en esa season
            }
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
