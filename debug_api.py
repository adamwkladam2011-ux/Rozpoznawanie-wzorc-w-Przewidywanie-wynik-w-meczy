import requests
from config import BASE_URL, HEADERS


def check_season():
    # Sprawdźmy Premier League (39) na sezon 2025
    league_id = 39
    season = 2025

    print(f"🕵️‍♂️ Sprawdzam dostępność meczów dla ligi {league_id}, sezon {season}...")

    url = f"{BASE_URL}/fixtures?league={league_id}&season={season}"
    try:
        r = requests.get(url, headers=HEADERS)
        data = r.json()

        if "errors" in data and data["errors"]:
            print(f"❌ Błąd API: {data['errors']}")
            return

        fixtures = data.get("response", [])
        print(f"✅ Znaleziono łącznie {len(fixtures)} meczów w tym sezonie.")

        # Policz statusy
        ns = sum(1 for f in fixtures if f['fixture']['status']['short'] == 'NS')
        ft = sum(1 for f in fixtures if f['fixture']['status']['short'] == 'FT')

        print(f"   - Zakończone (FT): {ft}")
        print(f"   - Zaplanowane (NS): {ns}")

        if ns > 0:
            print("\n🔍 Przykładowy nadchodzący mecz:")
            next_match = next(f for f in fixtures if f['fixture']['status']['short'] == 'NS')
            print(f"   {next_match['teams']['home']['name']} vs {next_match['teams']['away']['name']}")
            print(f"   Data: {next_match['fixture']['date']}")
        else:
            print("\n⚠️ Brak nadchodzących meczów. Sprawdź, czy sezon się nie skończył lub zmień rok w config.py.")

    except Exception as e:
        print(f"❌ Błąd połączenia: {e}")


if __name__ == "__main__":
    check_season()