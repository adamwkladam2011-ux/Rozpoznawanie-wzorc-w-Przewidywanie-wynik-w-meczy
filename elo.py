import pandas as pd


def compute_elo(df: pd.DataFrame,
                home_col: str = "home",
                away_col: str = "away",
                ghome_col: str = "goals_home",
                gawa_col: str = "goals_away",
                base_elo: float = 1500.0,
                k: float = 25.0) -> pd.DataFrame:
    """
    Prosty ELO na podstawie wyniku meczu.
    Zwraca df z kolumnami elo_home, elo_away (elo PRZED meczem).
    """
    teams_elo: dict[str, float] = {}

    def get_elo(team: str) -> float:
        if team not in teams_elo:
            teams_elo[team] = base_elo
        return teams_elo[team]

    elo_home_list = []
    elo_away_list = []

    for _, row in df.iterrows():
        home = row[home_col]
        away = row[away_col]
        gh = row[ghome_col]
        ga = row[gawa_col]

        Eh = get_elo(home)
        Ea = get_elo(away)

        elo_home_list.append(Eh)
        elo_away_list.append(Ea)

        # wynik meczu
        if gh > ga:
            score_home, score_away = 1.0, 0.0
        elif gh < ga:
            score_home, score_away = 0.0, 1.0
        else:
            score_home = score_away = 0.5

        expected_home = 1.0 / (1.0 + 10.0 ** ((Ea - Eh) / 400.0))
        expected_away = 1.0 - expected_home

        teams_elo[home] = Eh + k * (score_home - expected_home)
        teams_elo[away] = Ea + k * (score_away - expected_away)

    df = df.copy()
    df["elo_home"] = elo_home_list
    df["elo_away"] = elo_away_list

    return df
