import pandas as pd
import numpy as np
import os
import joblib

# Tryb bezokienkowy dla matplotlib
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, matthews_corrcoef, mean_absolute_error, r2_score, \
    accuracy_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyClassifier
from lightgbm import LGBMClassifier
from scipy import stats
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
    # 👇 POPRAWKA: Dodano sezon 2526 (obecny!)
    seasons = ["2526", "2425", "2324", "2223", "2122", "2021", "1920"]
    all_data = []

    print(f"📥 Pobieranie danych historycznych (w tym sezon 25/26)...")

    for league_name, codes in LEAGUE_FILES.items():
        for code in codes:
            for season in seasons:
                url = f"{BASE_URL}/{season}/{code}.csv"
                try:
                    df = pd.read_csv(url, encoding="unicode_escape")
                    # Czyszczenie nazw kolumn (czasem są spacje)
                    df.columns = [c.strip() for c in df.columns]
                    df["league_name"] = league_name
                    df["season_code"] = season
                    all_data.append(df)
                except Exception:
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

    print(f"✅ POBRANO: {len(full_df)} meczów (teraz uwzględnia najnowsze)!")
    return full_df


def compute_rolling_stats(df):
    """
    Oblicza formę punktową ORAZ siłę ataku/obrony (średnia goli z 5 meczów).
    """
    print("🔄 Obliczanie formy i statystyk bramkowych (ostatnie 5 meczów)...")

    team_stats = {}  # team -> {'pts': [], 'gs': [], 'gc': []}

    # Listy na nowe cechy
    cols = {
        'h_form': [], 'a_form': [],
        'h_att': [], 'a_att': [],
        'h_def': [], 'a_def': []
    }

    df = df.sort_values("date").reset_index(drop=True)

    for idx, row in df.iterrows():
        h, a = row['home'], row['away']
        gh, ga = row['goals_home'], row['goals_away']

        # 1. Statystyki PRZED meczem
        for team, prefix in [(h, 'h_'), (a, 'a_')]:
            stats = team_stats.get(team, {'pts': [], 'gs': [], 'gc': []})

            # Jeśli brak historii (np. początek sezonu 19/20), dajemy średnie
            last_5_pts = stats['pts'][-5:] if stats['pts'] else [1] * 5
            last_5_gs = stats['gs'][-5:] if stats['gs'] else [1.5] * 5
            last_5_gc = stats['gc'][-5:] if stats['gc'] else [1.5] * 5

            cols[f'{prefix}form'].append(sum(last_5_pts))
            cols[f'{prefix}att'].append(sum(last_5_gs) / len(last_5_gs))
            cols[f'{prefix}def'].append(sum(last_5_gc) / len(last_5_gc))

        # 2. Punkty za TEN mecz
        if gh > ga:
            hp, ap = 3, 0
        elif gh < ga:
            hp, ap = 0, 3
        else:
            hp, ap = 1, 1

        # 3. Aktualizacja historii
        if h not in team_stats: team_stats[h] = {'pts': [], 'gs': [], 'gc': []}
        if a not in team_stats: team_stats[a] = {'pts': [], 'gs': [], 'gc': []}

        team_stats[h]['pts'].append(hp);
        team_stats[h]['gs'].append(gh);
        team_stats[h]['gc'].append(ga)
        team_stats[a]['pts'].append(ap);
        team_stats[a]['gs'].append(ga);
        team_stats[a]['gc'].append(gh)

    for k, v in cols.items():
        df[k] = v

    return df


def main():
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 1. Dane + ELO
    df = download_historical_data()
    print("⚙️ Obliczanie ELO...")
    df = df.sort_values("date").reset_index(drop=True)
    df = compute_elo(df)

    # 2. Statystyki Bramkowe + Forma
    df = compute_rolling_stats(df)

    # Zapis historii
    df.to_csv("data/matches_history_big.csv", index=False)

    # 3. Trening
    feature_cols = [
        "elo_home", "elo_away", "odds_home", "odds_draw", "odds_away",
        "h_form", "a_form", "h_att", "a_att", "h_def", "a_def"
    ]
    df = df.dropna(subset=feature_cols)

    X = df[feature_cols]
    y_class = df.apply(
        lambda x: "H" if x["goals_home"] > x["goals_away"] else ("A" if x["goals_away"] > x["goals_home"] else "D"),
        axis=1)
    y_goals_h = df["goals_home"]
    y_goals_a = df["goals_away"]

    le = LabelEncoder()
    y_enc = le.fit_transform(y_class)

    # Stratyfikowany podział
    X_train, X_test, y_train, y_test, yh_train, yh_test, ya_train, ya_test = train_test_split(
        X, y_enc, y_goals_h, y_goals_a, test_size=0.2, random_state=42, stratify=y_enc
    )

    print(f"\n🚀 ROZPOCZYNAM TRENING (Liczba cech: {len(feature_cols)})...")

    # Baseline
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(X_train, y_train)
    baseline_acc = dummy.score(X_test, y_test)
    print(f"📉 BASELINE: {baseline_acc:.2%}")

    # MODEL
    clf = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.01,
        num_leaves=31,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)

    print(f"📈 TWÓJ MODEL (z Formą i Sezonem 25/26): {acc:.2%}")
    print(f"💎 MCC: {mcc:.4f}")

    # Analiza Pewniaków
    y_probs = clf.predict_proba(X_test)
    max_probs = np.max(y_probs, axis=1)
    threshold = 0.60
    high_conf_idx = np.where(max_probs > threshold)[0]

    if len(high_conf_idx) > 0:
        y_test_hc = y_test.iloc[high_conf_idx] if hasattr(y_test, 'iloc') else y_test[high_conf_idx]
        y_pred_hc = y_pred[high_conf_idx]
        acc_hc = accuracy_score(y_test_hc, y_pred_hc)
        print(
            f"\n🔥 SKUTECZNOŚĆ DLA 'PEWNIAKÓW' (Pewność > {threshold * 100}%): {acc_hc:.2%} ({len(high_conf_idx)} meczów)")

    # Regresja
    reg_h = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=42)
    reg_a = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=42)
    reg_h.fit(X, y_goals_h)
    reg_a.fit(X, y_goals_a)

    # Testy regresji
    preds_h = reg_home.predict(X_test) if 'reg_home' in locals() else reg_h.predict(X_test)
    residuals_h = yh_test - preds_h
    shapiro_stat, shapiro_p = stats.shapiro(residuals_h[:1000])  # Próbka dla Shapiro
    print(f"\n🧪 Test Shapiro-Wilka (regresja): p-value = {shapiro_p:.6f}")

    joblib.dump(clf, "models/clf_pro.pkl")
    joblib.dump(reg_h, "models/reg_home_pro.pkl")
    joblib.dump(reg_a, "models/reg_away_pro.pkl")
    joblib.dump(le, "models/label_encoder.pkl")
    joblib.dump(feature_cols, "models/feature_cols.pkl")

    print("\n✅ Gotowe! Model nauczył się na danych aż do 2026 roku.")


if __name__ == "__main__":
    main()