import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Ustawienie backendu graficznego (żeby działało bezproblemowo)
import matplotlib

matplotlib.use('Agg')


def plot_top15_elo_history():
    print("📊 Generowanie wykresu historii ELO...")

    # 1. Wczytanie danych
    csv_path = "data/matches_history_big.csv"
    if not os.path.exists(csv_path):
        print("❌ Brak pliku historii! Uruchom najpierw: python train_pro.py")
        return

    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # 2. Znalezienie aktualnego ELO dla każdej drużyny
    # Przechodzimy przez całą historię, żeby znaleźć "ostatnie znane" ELO
    last_elo = {}
    for _, row in df.iterrows():
        last_elo[row['home']] = row['elo_home']
        last_elo[row['away']] = row['elo_away']

    # 3. Wybór Top 15 drużyn z najwyższym ELO
    # Sortujemy malejąco i bierzemy 15 najlepszych
    top_15 = sorted(last_elo.items(), key=lambda x: x[1], reverse=True)[:15]
    top_15_teams = [t[0] for t in top_15]

    print(f"🏆 Top 15 drużyn w analizie:\n {', '.join(top_15_teams)}")

    # 4. Zbieranie danych do wykresu (Ostatnie 10 meczów dla każdej z Top 15)
    plot_data = []

    for team in top_15_teams:
        # Wyciągamy mecze, w których grała dana drużyna
        team_matches = df[(df['home'] == team) | (df['away'] == team)].copy()

        # Ustalamy, jakie miała ELO w danym meczu
        team_matches['elo'] = team_matches.apply(
            lambda x: x['elo_home'] if x['home'] == team else x['elo_away'], axis=1
        )

        # Bierzemy tylko ostatnie 10 spotkań
        last_10 = team_matches.tail(10).reset_index(drop=True)

        # Dodajemy do listy w formacie przyjaznym dla Seaborn
        for i, row in last_10.iterrows():
            plot_data.append({
                'Drużyna': f"{team} ({last_elo[team]:.0f})",  # W legendzie będzie aktualne ELO
                'Mecz_Wstecz': i - 9,  # Oś X: od -9 do 0 (0 to ostatni mecz)
                'Ranking ELO': row['elo']
            })

    plot_df = pd.DataFrame(plot_data)

    # 5. Rysowanie wykresu
    plt.figure(figsize=(16, 9))
    sns.set_style("whitegrid")

    # Paleta kolorów (wyrazista, żeby odróżnić 15 linii)
    palette = sns.color_palette("bright", 15)

    sns.lineplot(
        data=plot_df,
        x='Mecz_Wstecz',
        y='Ranking ELO',
        hue='Drużyna',
        palette=palette,
        linewidth=2.5,
        marker='o',
        markersize=8
    )

    # Kosmetyka wykresu
    plt.title('Dynamika Formy: Top 15 Drużyn Europy (Ostatnie 10 Meczów)', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Historia meczów (0 = Ostatni mecz)', fontsize=14)
    plt.ylabel('Punkty ELO', fontsize=14)

    # Legenda poza wykresem, żeby nie zasłaniała linii
    plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0, title='Drużyna (Aktualne ELO)', fontsize=11)

    # Dostosowanie osi X, żeby pokazywała liczby całkowite
    plt.xticks(range(-9, 1))

    plt.tight_layout()

    # Zapis
    os.makedirs("models", exist_ok=True)
    out_path = "models/elo_history_top15.png"
    plt.savefig(out_path, dpi=300)
    print(f"\n✅ Zapisano wykres: {out_path}")
    plt.close()


if __name__ == "__main__":
    plot_top15_elo_history()