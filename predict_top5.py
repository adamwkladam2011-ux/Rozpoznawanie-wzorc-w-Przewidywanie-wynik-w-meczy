import requests
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime, timedelta

# KONFIGURACJA
API_KEY = "d7d427428ea141edbf4f88b2ed2e751c"
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}
LEAGUE_CODES = ["PL", "PD", "BL1", "SA", "FL1"]

# Mapowanie (skrócone - wklej pełne jeśli masz)
HARD_MAPPINGS = {
    "Manchester United FC": "Man United", "Manchester City FC": "Man City", "Tottenham Hotspur FC": "Tottenham",
    "Bayer 04 Leverkusen": "Leverkusen", "FC Bayern München": "Bayern Munich", "FC Barcelona": "Barcelona",
    "Real Madrid CF": "Real Madrid", "Paris Saint-Germain FC": "Paris SG", "Juventus FC": "Juventus",
    "FC Internazionale Milano": "Inter", "AC Milan": "Milan", "Arsenal FC": "Arsenal", "Liverpool FC": "Liverpool"
}


def load_team_stats():
    """Wczytuje ELO, Formę ORAZ Średnie Goli"""
    print("📂 Analiza formy i siły ataku...")
    if not os.path.exists("data/matches_history_big.csv"):
        print("❌ Brak historii! Uruchom train_pro.py")
        exit()

    df = pd.read_csv("data/matches_history_big.csv", low_memory=False)
    df = df.sort_values("date")

    # team -> {'elo': 1500, 'pts': [], 'gs': [], 'gc': []}
    stats_map = {}

    for _, row in df.iterrows():
        h, a = row['home'], row['away']
        gh, ga = row['goals_home'], row['goals_away']

        # Inicjalizacja
        if h not in stats_map: stats_map[h] = {'elo': 1500, 'pts': [], 'gs': [], 'gc': []}
        if a not in stats_map: stats_map[a] = {'elo': 1500, 'pts': [], 'gs': [], 'gc': []}

        # ELO (ostatnie znane)
        stats_map[h]['elo'] = row['elo_home']
        stats_map[a]['elo'] = row['elo_away']

        # Punkty i Gole
        if gh > ga:
            hp, ap = 3, 0
        elif gh < ga:
            hp, ap = 0, 3
        else:
            hp, ap = 1, 1

        stats_map[h]['pts'].append(hp);
        stats_map[h]['gs'].append(gh);
        stats_map[h]['gc'].append(ga)
        stats_map[a]['pts'].append(ap);
        stats_map[a]['gs'].append(ga);
        stats_map[a]['gc'].append(
            gh)  # Dla gościa strzelone to ga! (w sensie row['goals_away']) - Czekaj, logiczny błąd?
        # Poprawka logiki goli dla gościa:
        # row['goals_away'] to gole GOŚCIA. Więc dla 'a' append(ga).
        # row['goals_home'] to gole GOSPODARZA. Więc dla 'a' append(gh) jako stracone.
        # W pętli wyżej w train_pro zrobiłem:
        # team_stats[a]['gs'].append(ga); team_stats[a]['gc'].append(gh) <- TO JEST POPRAWNE.

    # Agregacja ostatnich 5
    final_stats = {}
    for team, data in stats_map.items():
        last_5_pts = data['pts'][-5:] if data['pts'] else [1] * 5
        last_5_gs = data['gs'][-5:] if data['gs'] else [1.5] * 5
        last_5_gc = data['gc'][-5:] if data['gc'] else [1.5] * 5

        final_stats[team] = {
            'elo': data['elo'],
            'form': sum(last_5_pts),
            'att': sum(last_5_gs) / len(last_5_gs),  # Średnia strzelonych
            'def': sum(last_5_gc) / len(last_5_gc)  # Średnia straconych
        }

    print(f"✅ Załadowano pełne statystyki dla {len(final_stats)} drużyn.")
    return final_stats, list(final_stats.keys())


def smart_map_team(api_name, csv_teams_list):
    if api_name in HARD_MAPPINGS: return HARD_MAPPINGS[api_name]
    if api_name in csv_teams_list: return api_name
    api_clean = api_name.replace(".", "").lower()
    best_match = None
    for csv_team in csv_teams_list:
        csv_clean = csv_team.replace(".", "").lower()
        if csv_clean in api_clean:
            if best_match is None or len(csv_team) > len(best_match):
                best_match = csv_team
    return best_match if best_match else api_name


def predict_future():
    try:
        clf = joblib.load("models/clf_pro.pkl")
        reg_h = joblib.load("models/reg_home_pro.pkl")
        reg_a = joblib.load("models/reg_away_pro.pkl")
        le = joblib.load("models/label_encoder.pkl")
        feats = joblib.load("models/feature_cols.pkl")
    except:
        print("❌ Brak modeli. Uruchom train_pro.py")
        return

    team_stats, csv_teams = load_team_stats()

    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    print(f"🌍 Pobieranie meczów ({today} do {next_week})...")

    all_matches = []
    for league in LEAGUE_CODES:
        url = f"{BASE_URL}/competitions/{league}/matches?dateFrom={today}&dateTo={next_week}&status=SCHEDULED"
        try:
            r = requests.get(url, headers=HEADERS)
            data = r.json()
            matches = data.get('matches', [])
            for m in matches: m['league_code'] = league; all_matches.append(m)
        except Exception:
            pass

    if not all_matches: return

    predictions_list = []
    print(f"\n📊 PROGNOZY (ELO + FORMA + ATAK/OBRONA)...")
    print(f"{'MECZ':<35} | {'ELO':<9} | {'ATAK (śr)':<9} | {'TYP':<5} {'PEWNOŚĆ'}")
    print("-" * 90)

    for m in all_matches:
        home = smart_map_team(m['homeTeam']['name'], csv_teams)
        away = smart_map_team(m['awayTeam']['name'], csv_teams)

        # Domyślne dane dla beniaminków bez historii
        def_stats = {'elo': 1500, 'form': 5, 'att': 1.2, 'def': 1.5}
        h_data = team_stats.get(home, def_stats)
        a_data = team_stats.get(away, def_stats)

        # Obliczenie kursów ELO
        p_home = 1 / (1 + 10 ** ((a_data['elo'] - h_data['elo']) / 400))
        fake_odds_h = round(1 / p_home, 2)
        fake_odds_a = round(1 / (1 - p_home), 2)
        fake_odds_d = 3.60

        row = pd.DataFrame([{
            "elo_home": h_data['elo'], "elo_away": a_data['elo'],
            "odds_home": fake_odds_h, "odds_draw": fake_odds_d, "odds_away": fake_odds_a,
            "h_form": h_data['form'], "a_form": a_data['form'],
            "h_att": h_data['att'], "a_att": a_data['att'],
            "h_def": h_data['def'], "a_def": a_data['def']
        }])
        row = row[feats]

        probs = clf.predict_proba(row)[0]
        tip = le.inverse_transform([np.argmax(probs)])[0]
        conf = max(probs)
        gh = reg_h.predict(row)[0]
        ga = reg_a.predict(row)[0]

        # Wyświetlanie siły ataku dla porównania
        att_str = f"{h_data['att']:.1f}:{a_data['att']:.1f}"

        print(f"{home} vs {away:<15} | {h_data['elo']:.0f}:{a_data['elo']:.0f} | {att_str:<9} | {tip:<5} {conf:.1%}")

        predictions_list.append({
            "date": m['utcDate'][:10], "league": m['league_code'],
            "home": home, "away": away,
            "elo_home": h_data['elo'], "elo_away": a_data['elo'],
            "odds_home": fake_odds_h, "odds_draw": fake_odds_d, "odds_away": fake_odds_a,
            "tip": tip, "confidence": conf, "pred_score": f"{gh:.1f} - {ga:.1f}"
        })

    if predictions_list:
        pd.DataFrame(predictions_list).to_csv("data/upcoming_predictions_final.csv", index=False)
        print("\n✅ Gotowe.")


if __name__ == "__main__":
    predict_future()