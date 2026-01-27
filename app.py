import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ================================
#   KONFIGURACJA STRONY
# ================================
st.set_page_config(
    page_title="Piłkarzyki AI PRO ⚽",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================
#   STYL (Twój ulubiony - zachowany)
# ================================
st.markdown("""
<style>
    .winner { color: #2ecc71; font-weight: 900; font-size: 24px; }
    .loser { color: #95a5a6; font-weight: 400; font-size: 20px; text-decoration: none; }
    .score-box { 
        background-color: #1e272e; 
        border-radius: 10px; 
        padding: 5px 15px; 
        font-family: 'Courier New', monospace; 
        font-weight: bold; 
        font-size: 28px; 
        border: 1px solid #4bcffa;
        color: #4bcffa;
    }
    .value-badge {
        background-color: #f1c40f;
        color: #000;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
        margin-left: 10px;
    }
    .league-header { font-size: 30px; font-weight: bold; margin-bottom: 20px; }
    .vs-text { color: #57606f; font-weight: bold; font-size: 16px; margin-top: 10px;}
    div.stContainer { border: 1px solid #2f3640; border-radius: 15px; padding: 15px; margin-bottom: 15px; background-color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# Mapa flag i nazw lig
LEAGUE_INFO = {
    "PL": {"name": "Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "PD": {"name": "La Liga", "flag": "🇪🇸"},
    "BL1": {"name": "Bundesliga", "flag": "🇩🇪"},
    "SA": {"name": "Serie A", "flag": "🇮🇹"},
    "FL1": {"name": "Ligue 1", "flag": "🇫🇷"}
}

DATA_PREDS = "data/upcoming_predictions_final.csv"
DATA_HIST = "data/matches_history_big.csv"


# ================================
#   FUNKCJE POMOCNICZE
# ================================
@st.cache_data
def load_data():
    """Wczytuje predykcje i historię"""
    preds = pd.read_csv(DATA_PREDS) if os.path.exists(DATA_PREDS) else None
    hist = pd.read_csv(DATA_HIST) if os.path.exists(DATA_HIST) else None

    if hist is not None:
        hist['date'] = pd.to_datetime(hist['date'])
    return preds, hist


def calculate_value(row):
    """Sprawdza czy jest Value Bet"""
    # 1. Pobierz kurs na typ AI
    odd = 0.0
    if row['tip'] == 'H':
        odd = row['odds_home']
    elif row['tip'] == 'A':
        odd = row['odds_away']
    else:
        odd = row['odds_draw']

    # 2. Oblicz prawdopodobieństwo bukmachera (1/kurs)
    implied_prob = 1 / odd if odd > 0 else 0.99

    # 3. Value = Prawdopodobieństwo AI > Prawdopodobieństwo Bukmachera
    is_value = row['confidence'] > implied_prob
    value_margin = (row['confidence'] - implied_prob) * 100  # Ile % przewagi

    return is_value, value_margin, odd


def get_team_stats(df, team_name):
    """Filtruje mecze dla konkretnej drużyny"""
    matches = df[(df['home'] == team_name) | (df['away'] == team_name)].copy()
    matches = matches.sort_values('date', ascending=False)
    return matches


# ================================
#   ŁADOWANIE DANYCH
# ================================
df_preds, df_hist = load_data()

st.title("⚽ Piłkarzyki AI - Centrum Dowodzenia")

# ZAKŁADKI GŁÓWNE
tab1, tab2 = st.tabs(["🔮 PREDYKCJE (Value Bets)", "📜 ANALIZA DRUŻYN (Wykresy)"])

# =========================================================
#   ZAKŁADKA 1: PREDYKCJE (Styl "Old School" + Value)
# =========================================================
with tab1:
    if df_preds is None:
        st.error("❌ Brak predykcji! Uruchom `python sportmonks_ai/predict_top5.py`")
    else:
        # Filtry w kolumnach na górze
        c1, c2, c3 = st.columns(3)
        min_conf = c1.slider("Minimalna pewność AI", 30, 95, 45) / 100.0
        show_only_value = c2.checkbox("Pokaż tylko Value Bets 💰", value=False)

        # Filtrowanie
        df_view = df_preds[df_preds["confidence"] >= min_conf].copy()

        # Obliczanie Value dla każdego meczu
        df_view['is_value'], df_view['val_margin'], df_view['bet_odd'] = zip(*df_view.apply(calculate_value, axis=1))

        if show_only_value:
            df_view = df_view[df_view['is_value'] == True]

        # Wyświetlanie ligami
        available_leagues = sorted(df_view["league"].unique())

        # Podzakładki dla Lig
        league_tabs = st.tabs([f"{LEAGUE_INFO.get(l, {'flag': '🏆'})['flag']} {l}" for l in available_leagues])

        for i, league_code in enumerate(available_leagues):
            with league_tabs[i]:
                league_matches = df_view[df_view["league"] == league_code]

                if league_matches.empty:
                    st.info("Brak meczów spełniających kryteria w tej lidze.")

                for _, row in league_matches.iterrows():
                    tip = row['tip']
                    conf = row['confidence']
                    is_val = row['is_value']

                    # Logika klas CSS (Twój styl)
                    if tip == 'H':
                        class_h, class_a, win_text = "winner", "loser", f"Wygrywa {row['home']}"
                    elif tip == 'A':
                        class_h, class_a, win_text = "loser", "winner", f"Wygrywa {row['away']}"
                    else:
                        class_h, class_a, win_text = "winner", "winner", "Przewidywany REMIS"

                    # Karta meczu
                    with st.container():
                        c1, c2, c3 = st.columns([4, 3, 4])

                        # GOSPODARZ
                        with c1:
                            st.markdown(f"<div style='text-align: right;'>", unsafe_allow_html=True)
                            st.markdown(f"<span class='{class_h}'>{row['home']}</span>", unsafe_allow_html=True)
                            st.caption(f"ELO: {row['elo_home']:.0f} | Atak: {row.get('h_att', 0):.1f}")
                            if tip == 'H':
                                st.markdown(f"🔥 <b style='color:#2ecc71'>{conf:.0%}</b>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                        # WYNIK / VALUE
                        with c2:
                            st.markdown(f"<div style='text-align: center;'>", unsafe_allow_html=True)
                            st.caption(f"{row['date']}")

                            # Wynik w ramce
                            st.markdown(f"<span class='score-box'>{row['pred_score']}</span>", unsafe_allow_html=True)

                            # Value Badge
                            if is_val:
                                st.markdown(f"<br><span class='value-badge'>💰 VALUE @ {row['bet_odd']:.2f}</span>",
                                            unsafe_allow_html=True)
                                st.caption(f"Przewaga: +{row['val_margin']:.1f}%")
                            else:
                                st.markdown(f"<div class='vs-text'>{win_text}</div>", unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

                        # GOŚĆ
                        with c3:
                            st.markdown(f"<div style='text-align: left;'>", unsafe_allow_html=True)
                            st.markdown(f"<span class='{class_a}'>{row['away']}</span>", unsafe_allow_html=True)
                            st.caption(f"ELO: {row['elo_away']:.0f} | Atak: {row.get('a_att', 0):.1f}")
                            if tip == 'A':
                                st.markdown(f"🔥 <b style='color:#2ecc71'>{conf:.0%}</b>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                        # Expander z kursami
                        with st.expander("📊 Szczegóły kursów"):
                            kc1, kc2, kc3 = st.columns(3)
                            kc1.metric("Kurs 1", f"{row['odds_home']:.2f}", delta="Typ AI" if tip == 'H' else None)
                            kc2.metric("Kurs X", f"{row['odds_draw']:.2f}", delta="Typ AI" if tip == 'D' else None)
                            kc3.metric("Kurs 2", f"{row['odds_away']:.2f}", delta="Typ AI" if tip == 'A' else None)

# =========================================================
#   ZAKŁADKA 2: ANALIZA DRUŻYN (Wykresy i Historia)
# =========================================================
with tab2:
    if df_hist is None:
        st.error("❌ Brak historii! Uruchom `python sportmonks_ai/train_pro.py`")
    else:
        # Wybór drużyny
        all_teams = sorted(list(set(df_hist['home'].unique()) | set(df_hist['away'].unique())))
        selected_team = st.selectbox("🔍 Wyszukaj drużynę:", all_teams, index=0)

        # Pobranie danych
        team_matches = get_team_stats(df_hist, selected_team)

        # 1. WYKRES ELO
        st.subheader(f"📈 Dynamika formy: {selected_team}")
        chart_data = team_matches.copy().sort_values('date')
        chart_data['Team ELO'] = chart_data.apply(
            lambda x: x['elo_home'] if x['home'] == selected_team else x['elo_away'], axis=1
        )

        fig = px.line(chart_data, x='date', y='Team ELO', markers=True)
        fig.update_traces(line_color='#4bcffa', line_width=3)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

        # 2. TABELA MECZÓW
        st.subheader("🗓️ Ostatnie mecze")

        display_data = []
        for _, m in team_matches.head(10).iterrows():
            if m['home'] == selected_team:
                opp, score = m['away'], f"{int(m['goals_home'])} - {int(m['goals_away'])}"
                res = "Zwycięstwo" if m['goals_home'] > m['goals_away'] else (
                    "Porażka" if m['goals_home'] < m['goals_away'] else "Remis")
            else:
                opp, score = m['home'], f"{int(m['goals_away'])} - {int(m['goals_home'])}"  # Wynik odwrócony dla gości
                res = "Zwycięstwo" if m['goals_away'] > m['goals_home'] else (
                    "Porażka" if m['goals_away'] < m['goals_home'] else "Remis")

            display_data.append({
                "Data": m['date'].strftime('%Y-%m-%d'),
                "Rywal": opp,
                "Wynik": score,
                "Rezultat": res
            })

        st.dataframe(
            pd.DataFrame(display_data).style.map(
                lambda v: 'color: #2ecc71' if v == 'Zwycięstwo' else (
                    'color: #e74c3c' if v == 'Porażka' else 'color: gray'),
                subset=['Rezultat']
            ),
            use_container_width=True,
            hide_index=True
        )