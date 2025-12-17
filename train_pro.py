import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMClassifier
from elo import compute_elo

# Mapowanie lig
LEAGUE_FILES = {
    "Premier League": ["E0"],
    "La Liga": ["SP1"],
    "Bundesliga": ["D1"],
    "Serie A": ["I1"],
    "Ligue 1": ["F1"]
}

BASE_URL = "https://www.football-data.co.uk/mmz4281"


def download_historical_data():
    # 👇 DODANO "2425" (obecny sezon) żeby mieć najświeższe dane!
    seasons = ["2425", "2324", "2223", "2122", "2021", "1920"]
    all_data = []

    print(f"📥 Pobieranie darmowych danych historycznych (football-data.co.uk)...")

    for league_name, codes in LEAGUE_FILES.items():
        for code in codes:
            for season in seasons:
                url = f"{BASE_URL}/{season}/{code}.csv"
                try:
                    df = pd.read_csv(url, encoding="unicode_escape")
                    df["league_name"] = league_name
                    df["season_code"] = season
                    all_data.append(df)
                except Exception:
                    # Ignorujemy błędy (np. brak pliku na początku sezonu)
                    continue

    if not all_data:
        print("❌ Błąd pobierania danych.")
        return pd.DataFrame()

    full_df = pd.concat(all_data, ignore_index=True)

    rename_map = {
        "Date": "date", "HomeTeam": "home", "AwayTeam": "away",
        "FTHG": "goals_home", "FTAG": "goals_away",
        "B365H": "odds_home", "B365D": "odds_draw", "B365A": "odds_away"
    }

    full_df = full_df.rename(columns=rename_map)
    full_df["date"] = pd.to_datetime(full_df["date"], dayfirst=True, errors='coerce')
    full_df = full_df.dropna(subset=["date", "goals_home", "goals_away", "odds_home"])

    print(f"✅ POBRANO: {len(full_df)} meczów (w tym najnowsze z sezonu 24/25)!")
    return full_df


def build_features(df):
    df = df.sort_values("date").reset_index(drop=True)
    df = compute_elo(df)
    return df


def main():
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    df = download_historical_data()

    print("⚙️ Obliczanie rankingu ELO...")
    df = build_features(df)

    df.to_csv("data/matches_history_big.csv", index=False)
    print(f"💾 Zapisano historię do data/matches_history_big.csv")

    feature_cols = ["elo_home", "elo_away", "odds_home", "odds_draw", "odds_away"]
    df = df.dropna(subset=feature_cols)

    X = df[feature_cols]
    y = df.apply(
        lambda x: "H" if x["goals_home"] > x["goals_away"] else ("A" if x["goals_away"] > x["goals_home"] else "D"),
        axis=1)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42)

    print("🚀 Trenowanie modelu...")
    clf = LGBMClassifier(n_estimators=1000, learning_rate=0.05, verbose=-1)
    clf.fit(X_train, y_train)

    print(classification_report(y_test, clf.predict(X_test), target_names=le.classes_))

    reg_home = RandomForestRegressor(n_estimators=100, n_jobs=-1)
    reg_away = RandomForestRegressor(n_estimators=100, n_jobs=-1)
    reg_home.fit(X, df["goals_home"])
    reg_away.fit(X, df["goals_away"])

    joblib.dump(clf, "models/clf_pro.pkl")
    joblib.dump(reg_home, "models/reg_home_pro.pkl")
    joblib.dump(reg_away, "models/reg_away_pro.pkl")
    joblib.dump(le, "models/label_encoder.pkl")
    joblib.dump(feature_cols, "models/feature_cols.pkl")

    print("✅ Model gotowy.")


if __name__ == "__main__":
    main()