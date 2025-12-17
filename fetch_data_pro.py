import os
import time
import requests
import pandas as pd
from tqdm import tqdm
from config import BASE_URL, HEADERS, LEAGUES, SEASON, FREE_PLAN_MODE, MATCHES_LIMIT

# 🚧 OGRANICZNIK PRĘDKOŚCI
# Twój limit to 10 zapytań na minutę.
# Oznacza to 1 zapytanie co 6 sekund. Dajemy 7s dla bezpieczeństwa.
RATE_LIMIT_DELAY = 7


def wait_for_api():
    """Czeka, aby nie przekroczyć limitu 10 req/min."""
    time.sleep(RATE_LIMIT_DELAY)


def api_request(endpoint: str, params: dict | None = None):
    url = f"{BASE_URL}/{endpoint}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)

        # ZAWSZE czekamy po zapytaniu
        wait_for_api()

        data = r.json()

        if "errors" in data and data["errors"]:
            errs = data["errors"]
            # Specyficzna obsługa błędu Rate Limit
            if isinstance(errs, dict) and 'rateLimit' in errs:
                print(f"\n⏳ PRZEKROCZONO LIMIT (Rate Limit). Czekam 60s...")
                time.sleep(60)
                # Spróbuj raz jeszcze (rekurencja)
                return api_request(endpoint, params)

            if errs:
                print(f"\n⚠️ BŁĄD API ({endpoint}): {errs}")
                return []

        if r.status_code != 200:
            print(f"\n⚠️ HTTP ERROR {endpoint}: {r.status_code} {r.text}")
            return []

        return data.get("response", [])
    except Exception as e:
        print(f"\n⚠️ Request failed: {e}")
        return []


def get_fixtures(league_id: int, season: int) -> pd.DataFrame:
    print(f"   🔎 Pobieram listę meczów dla ligi {league_id}...")
    params = {"league": league_id, "season": season}
    data = api_request("fixtures", params)
    rows = []

    if not data:
        return pd.DataFrame()

    for m in data:
        fixture = m["fixture"]
        teams = m["teams"]
        goals = m["goals"]
        status_short = fixture["status"]["short"]

        if status_short != "FT":
            continue

        rows.append({
            "matchId": fixture["id"],
            "date": fixture["date"],
            "league_id": league_id,
            "home": teams["home"]["name"],
            "away": teams["away"]["name"],
            "goals_home": goals["home"],
            "goals_away": goals["away"],
            "referee": fixture.get("referee")
        })

    return pd.DataFrame(rows)


def get_stats(match_id: int) -> dict:
    data = api_request("fixtures/statistics", {"fixture": match_id})
    stats = {}
    if not data: return stats

    for i, entry in enumerate(data):
        side = "home" if i == 0 else "away"
        for s in entry["statistics"]:
            if s["value"] is None: continue
            name = s["type"].lower().replace(" ", "_")
            value = s["value"]
            if isinstance(value, str) and "%" in value:
                value = value.replace("%", "")
            try:
                value = float(value)
                stats[f"stat_{name}_{side}"] = value
            except ValueError:
                continue
    return stats


def get_odds(match_id: int) -> dict:
    data = api_request("odds", {"fixture": match_id})
    res = {"odds_home": 0.0, "odds_draw": 0.0, "odds_away": 0.0}
    if not data: return res

    bookmakers = data[0].get("bookmakers", [])
    if not bookmakers: return res

    bets = bookmakers[0].get("bets", [])
    for bet in bets:
        if bet["name"] == "Match Winner":
            for v in bet["values"]:
                if v["value"] == "Home": res["odds_home"] = float(v["odd"])
                if v["value"] == "Draw": res["odds_draw"] = float(v["odd"])
                if v["value"] == "Away": res["odds_away"] = float(v["odd"])
            break
    return res


def build_dataset():
    os.makedirs("data", exist_ok=True)
    all_rows = []

    print(f"🚀 START. Sezon: {SEASON}. Tryb Powolny (bezpieczny dla limitu 10/min).")

    for league_id, league_name in LEAGUES.items():
        print(f"\n📌 Liga: {league_name} ({league_id})")

        df = get_fixtures(league_id, SEASON)

        if df.empty:
            print("   ⚠️ Brak meczów lub błąd API.")
            continue

        df = df.sort_values("date")

        if FREE_PLAN_MODE:
            # Zmniejszmy jeszcze bardziej limit na start, żebyś szybciej zobaczył efekt
            limit = 5  # Pobieramy tylko 5 meczów na ligę testowo
            print(f"   ✂️ Pobieram OSTATNIE {limit} meczów (oszczędzanie limitu)...")
            df = df.tail(limit)
        else:
            print(f"   ➤ meczów do pobrania: {len(df)}")

        # Pętla po meczach
        for _, row in tqdm(df.iterrows(), total=len(df)):
            match_id = row["matchId"]

            # Każde z tych wywołań w środku ma teraz time.sleep(7)
            stats = get_stats(match_id)
            odds = get_odds(match_id)

            full_row = {**row.to_dict(), **stats, **odds}
            all_rows.append(full_row)

    if not all_rows:
        print("\n❌ Nie udało się pobrać żadnych danych.")
        return

    final_df = pd.DataFrame(all_rows)
    out_path = os.path.join("data", "matches_raw.csv")
    final_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 SUKCES! Zapisano: {out_path} (rekordów: {len(final_df)})")


if __name__ == "__main__":
    build_dataset()