import requests
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime, timedelta

# ================================
#   KONFIGURACJA
# ================================
API_KEY = "d7d427428ea141edbf4f88b2ed2e751c"  # Twój klucz API
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}
# Kody lig do pobrania: PL (Anglia), PD (Hiszpania), BL1 (Niemcy), SA (Włochy), FL1 (Francja)
LEAGUE_CODES = ["PL", "PD", "BL1", "SA", "FL1"]

# Sztywne mapowanie dla trudnych przypadków (API -> CSV)
HARD_MAPPINGS = {
    # --- ANGLIA (Premier League) ---
    "Manchester United FC": "Man United",
    "Manchester City FC": "Man City",
    "Tottenham Hotspur FC": "Tottenham",
    "Newcastle United FC": "Newcastle",
    "Wolverhampton Wanderers FC": "Wolves",
    "Nottingham Forest FC": "Nott'm Forest",
    "Brighton & Hove Albion FC": "Brighton",
    "West Ham United FC": "West Ham",
    "Sheffield United FC": "Sheffield United",
    "Leicester City FC": "Leicester",
    "Leeds United FC": "Leeds",
    "Luton Town FC": "Luton",
    "Ipswich Town FC": "Ipswich",
    "Southampton FC": "Southampton",

    # --- NIEMCY (Bundesliga) ---
    "Bayer 04 Leverkusen": "Leverkusen",
    "Borussia Mönchengladbach": "M'gladbach",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "1. FSV Mainz 05": "Mainz",
    "VfL Bochum 1848": "Bochum",
    "FC Augsburg": "Augsburg",
    "VfL Wolfsburg": "Wolfsburg",
    "1. FC Union Berlin": "Union Berlin",
    "SC Freiburg": "Freiburg",
    "VfB Stuttgart": "Stuttgart",
    "1. FC Köln": "FC Koln",
    "SV Werder Bremen": "Werder Bremen",
    "1. FC Heidenheim 1846": "Heidenheim",
    "SV Darmstadt 98": "Darmstadt",
    "FC St. Pauli 1910": "St Pauli",
    "Holstein Kiel": "Holstein Kiel",
    "Fortuna Düsseldorf": "Fortuna Dusseldorf",

    # --- WŁOCHY (Serie A) ---
    "FC Internazionale Milano": "Inter",
    "AC Milan": "Milan",
    "AS Roma": "Roma",
    "SS Lazio": "Lazio",
    "Hellas Verona FC": "Verona",
    "US Salernitana 1919": "Salernitana",
    "US Cremonese": "Cremonese",
    "AC Monza": "Monza",
    "US Sassuolo Calcio": "Sassuolo",
    "Udinese Calcio": "Udinese",
    "Torino FC": "Torino",
    "Bologna FC 1909": "Bologna",
    "Cagliari Calcio": "Cagliari",
    "Empoli FC": "Empoli",
    "ACF Fiorentina": "Fiorentina",
    "Frosinone Calcio": "Frosinone",
    "Genoa CFC": "Genoa",
    "US Lecce": "Lecce",
    "Parma Calcio 1913": "Parma",
    "Como 1907": "Como",
    "Venezia FC": "Venezia",

    # --- HISZPANIA (La Liga) ---
    "Athletic Club": "Ath Bilbao",
    "Atlético de Madrid": "Ath Madrid",
    "Club Atlético de Madrid": "Ath Madrid",
    "Real Betis Balompié": "Betis",
    "Rayo Vallecano de Madrid": "Rayo Vallecano",
    "RCD Espanyol de Barcelona": "Espanyol",
    "RC Celta de Vigo": "Celta",
    "Cadiz CF": "Cadiz",
    "UD Almería": "Almeria",
    "Valencia CF": "Valencia",
    "Real Sociedad de Fútbol": "Sociedad",
    "Sevilla FC": "Sevilla",
    "Real Valladolid CF": "Valladolid",
    "Girona FC": "Girona",
    "Deportivo Alavés": "Alaves",
    "Granada CF": "Granada",
    "CA Osasuna": "Osasuna",
    "Getafe CF": "Getafe",
    "RCD Mallorca": "Mallorca",
    "CD Leganés": "Leganes",
    "UD Las Palmas": "Las Palmas",

    # --- FRANCJA (Ligue 1) ---
    "Paris Saint-Germain FC": "Paris SG",
    "Olympique de Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon",
    "Stade Rennais FC 1901": "Rennes",
    "AS Saint-Étienne": "St Etienne",
    "Clermont Foot 63": "Clermont",
    "Le Havre AC": "Le Havre",
    "FC Metz": "Metz",
    "FC Lorient": "Lorient",
    "AS Monaco FC": "Monaco",
    "OGC Nice": "Nice",
    "RC Lens": "Lens",
    "Stade de Reims": "Reims",
    "Stade Brestois 29": "Brest",
    "LOSC Lille": "Lille",
    "Toulouse FC": "Toulouse",
    "Montpellier HSC": "Montpellier",
    "FC Nantes": "Nantes",
    "AJ Auxerre": "Auxerre",
    "Angers SCO": "Angers",
}


# ================================
#   FUNKCJE POMOCNICZE
# ================================
def load_elo_data():
    """Wczytuje historię i tworzy mapę ELO dla nazw z CSV"""
    print("📂 Wczytywanie bazy ELO...")
    if not os.path.exists("data/matches_history_big.csv"):
        print("❌ Brak pliku data/matches_history_big.csv! Uruchom najpierw train_pro.py")
        exit()

    df = pd.read_csv("data/matches_history_big.csv", low_memory=False)
    # Sortujemy od najnowszych, żeby wziąć ostatnie znane ELO
    df = df.sort_values("date", ascending=False)

    elo_map = {}
    known_teams = set()

    # Zbieramy unikalne drużyny i ich ostatnie ELO
    for _, row in df.iterrows():
        # Home
        if row['home'] not in elo_map:
            elo_map[row['home']] = row['elo_home']
            known_teams.add(row['home'])
        # Away
        if row['away'] not in elo_map:
            elo_map[row['away']] = row['elo_away']
            known_teams.add(row['away'])

    print(f"✅ Załadowano ELO dla {len(elo_map)} drużyn.")
    return elo_map, list(known_teams)


def smart_map_team(api_name, csv_teams_list):
    """Inteligentne dopasowanie nazwy z API do nazwy z CSV"""

    # 1. Sprawdź sztywne mapowanie
    if api_name in HARD_MAPPINGS:
        return HARD_MAPPINGS[api_name]

    # 2. Sprawdź czy nazwa z API jest już w CSV (idealne dopasowanie)
    if api_name in csv_teams_list:
        return api_name

    # 3. Dopasowanie "rozmyte" (Fuzzy)
    # Sprawdzamy, czy krótka nazwa z CSV zawiera się w długiej nazwie z API
    # np. "Werder Bremen" in "SV Werder Bremen" -> True
    api_clean = api_name.replace(".", "").lower()  # np. "fc st pauli 1910"

    best_match = None

    for csv_team in csv_teams_list:
        csv_clean = csv_team.replace(".", "").lower()  # np. "st pauli"

        # Jeśli nazwa z CSV jest w nazwie API (np. 'Hoffenheim' w 'TSG 1899 Hoffenheim')
        if csv_clean in api_clean:
            # Wybieramy najdłuższe dopasowanie (żeby 'Man City' nie pasowało do 'Man United')
            if best_match is None or len(csv_team) > len(best_match):
                best_match = csv_team

    if best_match:
        return best_match

    # Jeśli nic nie znaleziono, zwracamy oryginał (dostanie 1500)
    return api_name


# ================================
#   GŁÓWNA PĘTLA
# ================================
def predict_future():
    # 1. Ładowanie modeli
    try:
        clf = joblib.load("models/clf_pro.pkl")
        reg_h = joblib.load("models/reg_home_pro.pkl")
        reg_a = joblib.load("models/reg_away_pro.pkl")
        le = joblib.load("models/label_encoder.pkl")
        feats = joblib.load("models/feature_cols.pkl")
    except:
        print("❌ Brak modeli. Uruchom train_pro.py")
        return

    # 2. Ładowanie ELO
    elo_map, csv_teams = load_elo_data()

    # 3. Pobieranie meczów
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")

    print(f"🌍 Pobieranie meczów z API ({today} do {next_week})...")

    all_matches = []
    for league in LEAGUE_CODES:
        url = f"{BASE_URL}/competitions/{league}/matches?dateFrom={today}&dateTo={next_week}&status=SCHEDULED"
        try:
            r = requests.get(url, headers=HEADERS)
            data = r.json()
            matches = data.get('matches', [])
            for m in matches:
                m['league_code'] = league
                all_matches.append(m)
        except Exception as e:
            print(f"⚠️ Błąd pobierania ligi {league}: {e}")

    if not all_matches:
        print("❌ Brak nadchodzących meczów (lub błąd API).")
        return

    print(f"\n📊 ZNALEZIONO {len(all_matches)} MECZÓW. ANALIZA...")
    print(
        f"{'DATA':<12} | {'GOSPODARZ (API -> CSV)':<35} vs {'GOŚĆ':<35} | {'ELO H':<5} {'ELO A':<5} | {'TYP':<5} {'PEWNOŚĆ':<8} | {'WYNIK'}")
    print("-" * 130)

    for m in all_matches:
        # Pobieramy nazwy z API
        api_home = m['homeTeam']['name']
        api_away = m['awayTeam']['name']

        # Mapujemy na nazwy z CSV (żeby znaleźć ELO)
        home = smart_map_team(api_home, csv_teams)
        away = smart_map_team(api_away, csv_teams)

        # Pobieramy ELO
        elo_h = elo_map.get(home, 1500.0)
        elo_a = elo_map.get(away, 1500.0)

        # Obliczamy szanse
        dr = elo_a - elo_h
        p_home = 1 / (1 + 10 ** (dr / 400))

        # Symulujemy kursy
        fake_odds_h = round(1 / p_home, 2)
        fake_odds_a = round(1 / (1 - p_home), 2)
        fake_odds_d = 3.60

        # Przygotowanie danych do modelu
        row = pd.DataFrame([{
            "elo_home": elo_h, "elo_away": elo_a,
            "odds_home": fake_odds_h, "odds_draw": fake_odds_d, "odds_away": fake_odds_a
        }])

        # Predykcja
        # Upewnij się, że kolejność kolumn jest taka sama jak w treningu
        row = row[feats]

        probs = clf.predict_proba(row)[0]
        pred_idx = np.argmax(probs)
        tip = le.inverse_transform([pred_idx])[0]
        conf = probs[pred_idx]

        gh = reg_h.predict(row)[0]
        ga = reg_a.predict(row)[0]

        date_str = m['utcDate'][:10]

        # Wyświetlanie
        # Jeśli ELO nadal wynosi 1500 dla obu, oznaczamy to gwiazdką (*) jako niepewne
        alert = "⚠️" if (elo_h == 1500 and elo_a == 1500) else ""

        print(
            f"{date_str:<12} | {home:<35} vs {away:<35} | {elo_h:.0f}   {elo_a:.0f}   | {tip:<5} {conf:.1%}   | {gh:.1f}-{ga:.1f} {alert}")


if __name__ == "__main__":
    predict_future()