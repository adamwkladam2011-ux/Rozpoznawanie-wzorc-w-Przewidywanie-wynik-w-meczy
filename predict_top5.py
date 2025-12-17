import requests
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime, timedelta

# ================================
#   KONFIGURACJA
# ================================
# 🔑 WKLEJ TUTAJ SWÓJ KLUCZ Z FOOTBALL-DATA.ORG
API_KEY = "d7d427428ea141edbf4f88b2ed2e751c"

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}
LEAGUE_CODES = ["PL", "PD", "BL1", "SA", "FL1"]

# Rozbudowane mapowanie nazw (API -> CSV)
TEAM_MAPPING = {
    # Anglia
    "Man City": "Man City", "Manchester City FC": "Man City",
    "Man Utd": "Man United", "Manchester United FC": "Man United",
    "Spurs": "Tottenham", "Tottenham Hotspur FC": "Tottenham",
    "Newcastle": "Newcastle", "Newcastle United FC": "Newcastle",
    "Brighton & Hove Albion FC": "Brighton",
    "Wolves": "Wolves", "Wolverhampton Wanderers FC": "Wolves",
    "West Ham United FC": "West Ham",
    "Nottingham Forest FC": "Nott'm Forest",
    "Leicester City FC": "Leicester",
    "Leeds United FC": "Leeds",
    "AFC Bournemouth": "Bournemouth",
    "Sunderland AFC": "Sunderland",
    "Crystal Palace FC": "Crystal Palace",
    "Sheffield United FC": "Sheffield United",
    "Burnley FC": "Burnley",
    "Luton Town FC": "Luton",
    "Brentford FC": "Brentford",
    "Everton FC": "Everton",
    "Aston Villa FC": "Aston Villa",
    "Liverpool FC": "Liverpool",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "Fulham FC": "Fulham",

    # Hiszpania
    "Real Madrid CF": "Real Madrid",
    "FC Barcelona": "Barcelona",
    "Atlético de Madrid": "Ath Madrid",
    "Club Atlético de Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao",
    "Real Betis Balompié": "Betis",
    "Villarreal CF": "Villarreal",
    "Real Sociedad de Fútbol": "Sociedad",
    "Sevilla FC": "Sevilla",
    "Girona FC": "Girona",
    "Valencia CF": "Valencia",
    "Rayo Vallecano de Madrid": "Rayo Vallecano",
    "RCD Mallorca": "Mallorca",
    "RC Celta de Vigo": "Celta",
    "CA Osasuna": "Osasuna",
    "Getafe CF": "Getafe",
    "RCD Espanyol de Barcelona": "Espanyol",

    # Niemcy
    "FC Bayern München": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Bayer 04 Leverkusen": "Leverkusen",
    "RB Leipzig": "RB Leipzig",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "VfL Wolfsburg": "Wolfsburg",
    "Borussia Mönchengladbach": "M'gladbach",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "SC Freiburg": "Freiburg",
    "1. FSV Mainz 05": "Mainz",
    "FC Augsburg": "Augsburg",
    "1. FC Köln": "FC Koln",
    "VfB Stuttgart": "Stuttgart",
    "VfL Bochum 1848": "Bochum",
    "SV Werder Bremen": "Werder Bremen",
    "1. FC Union Berlin": "Union Berlin",
    "1. Heidenheim 1846": "Heidenheim",

    # Włochy
    "Juventus FC": "Juventus",
    "AC Milan": "Milan",
    "FC Internazionale Milano": "Inter",
    "SSC Napoli": "Napoli",
    "AS Roma": "Roma",
    "SS Lazio": "Lazio",
    "Atalanta BC": "Atalanta",
    "ACF Fiorentina": "Fiorentina",
    "Torino FC": "Torino",
    "Udinese Calcio": "Udinese",
    "Bologna FC 1909": "Bologna",
    "US Sassuolo Calcio": "Sassuolo",
    "US Lecce": "Lecce",
    "AC Monza": "Monza",
    "Hellas Verona FC": "Verona",
    "US Salernitana 1919": "Salernitana",
    "Empoli FC": "Empoli",
    "Genoa CFC": "Genoa",
    "Cagliari Calcio": "Cagliari",
    "Frosinone Calcio": "Frosinone",
    "Como 1907": "Como",
    "US Cremonese": "Cremonese",

    # Francja
    "Paris Saint-Germain FC": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "AS Monaco FC": "Monaco",
    "Olympique Lyonnais": "Lyon",
    "LOSC Lille": "Lille",
    "Stade Rennais FC 1901": "Rennes",
    "OGC Nice": "Nice",
    "RC Lens": "Lens"
}

# ================================
#   ŁADOWANIE MODELU
# ================================
print("📂 Ładowanie modelu...")
try:
    clf = joblib.load("models/clf_pro.pkl")
    reg_h = joblib.load("models/reg_home_pro.pkl")
    reg_a = joblib.load("models/reg_away_pro.pkl")
    le = joblib.load("models/label_encoder.pkl")
    feats = joblib.load("models/feature_cols.pkl")
    df_hist = pd.read_csv("data/matches_history_big.csv", low_memory=False)
except FileNotFoundError:
    print("❌ Brak plików modelu. Uruchom najpierw train_pro.py")
    exit()

# ================================
#   BUDOWANIE BAZY ELO
# ================================
print("⚙️  Indeksowanie ELO...")
elo_map = {}
df_sorted = df_hist.sort_values("date", ascending=False)
teams_found = pd.concat([df_sorted["home"], df_sorted["away"]]).unique()

for team in teams_found:
    last_match = df_sorted[(df_sorted["home"] == team) | (df_sorted["away"] == team)].iloc[0]
    elo = last_match["elo_home"] if last_match["home"] == team else last_match["elo_away"]
    elo_map[team] = elo


# ================================
#   POBIERANIE TERMINARZA
# ================================
def get_fixtures():
    all_matches = []
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"🌍 Pobieranie meczów ({today} do {next_week})...")

    for code in LEAGUE_CODES:
        url = f"{BASE_URL}/competitions/{code}/matches?dateFrom={today}&dateTo={next_week}"
        try:
            r = requests.get(url, headers=HEADERS)
            if r.status_code == 429:
                print(f"   ⚠️ Limit zapytań! Czekam chwilę...")
                continue

            data = r.json()
            matches = data.get("matches", [])
            print(f"   📌 {code}: Znaleziono {len(matches)} meczów.")

            for m in matches:
                api_home = m["homeTeam"]["name"]
                api_away = m["awayTeam"]["name"]

                home = TEAM_MAPPING.get(api_home, api_home)
                away = TEAM_MAPPING.get(api_away, api_away)

                if home not in elo_map:
                    home = home.replace(" FC", "").replace("CF ", "").replace("AFC ", "").replace("1. ", "").strip()
                if away not in elo_map:
                    away = away.replace(" FC", "").replace("CF ", "").replace("AFC ", "").replace("1. ", "").strip()

                all_matches.append({
                    "league": code,
                    "date": m["utcDate"][:10],
                    "home": home,
                    "away": away
                })
        except Exception as e:
            print(f"   ❌ Błąd przy lidze {code}: {e}")

    return all_matches


# ================================
#   PREDYKCJA
# ================================
def predict_all():
    matches = get_fixtures()
    predictions_list = []

    if not matches:
        print("\n❌ Brak nadchodzących meczów lub błąd klucza API.")
        return

    print("\n" + "=" * 60)
    print(" 🔮  PREDYKCJE TOP 5 LIG (NAJBLIŻSZE 7 DNI)")
    print("=" * 60)

    for m in matches:
        home = m["home"]
        away = m["away"]

        elo_h = elo_map.get(home, 1500.0)
        elo_a = elo_map.get(away, 1500.0)

        if elo_h == 1500.0 and elo_a == 1500.0:
            continue

        dr = elo_a - elo_h
        p_home = 1 / (1 + 10 ** (dr / 400))

        fake_odds_h = max(1.1, 1 / p_home + (0.2 if elo_h > elo_a else -0.5))
        fake_odds_a = max(1.1, 1 / (1 - p_home) + (-0.5 if elo_h > elo_a else 0.2))
        fake_odds_d = 3.60

        row = {
            "elo_home": elo_h, "elo_away": elo_a,
            "odds_home": fake_odds_h, "odds_draw": fake_odds_d, "odds_away": fake_odds_a
        }

        X = pd.DataFrame([row])[feats]

        probs = clf.predict_proba(X)[0]
        class_order = le.classes_
        prob_dict = {c: p for c, p in zip(class_order, probs)}
        tip = max(prob_dict, key=prob_dict.get)
        conf = prob_dict[tip]
        gh = reg_h.predict(X)[0]
        ga = reg_a.predict(X)[0]

        print(f"\n⚽ [{m['league']}] {home} vs {away}")
        print(f"   📊 ELO: {elo_h:.0f} vs {elo_a:.0f}")
        print(f"   💡 TYP: {tip} ({conf:.1%})  |  Wynik: {gh:.1f} - {ga:.1f}")

        if conf > 0.60:
            print("   🔥 DO BRANIA!")

        # DODAWANIE DO LISTY (TEGO BRAKOWAŁO!)
        predictions_list.append({
            "date": m["date"],
            "league": m["league"],
            "home": home,
            "away": away,
            "elo_home": elo_h,
            "elo_away": elo_a,
            "odds_home": fake_odds_h,
            "odds_draw": fake_odds_d,
            "odds_away": fake_odds_a,
            "tip": tip,
            "confidence": conf,
            "pred_score": f"{gh:.1f} - {ga:.1f}"
        })

    # ZAPIS DO PLIKU (TEGO BRAKOWAŁO!)
    if predictions_list:
        os.makedirs("data", exist_ok=True)
        out_path = "data/upcoming_predictions_final.csv"
        pd.DataFrame(predictions_list).to_csv(out_path, index=False)
        print(f"\n✅ SUKCES! Zapisano wyniki do: {out_path}")
    else:
        print("\n⚠️ Nie wygenerowano żadnych wyników.")


if __name__ == "__main__":
    predict_all()