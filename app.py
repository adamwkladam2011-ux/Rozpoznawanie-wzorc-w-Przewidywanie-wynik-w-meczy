import streamlit as st
import pandas as pd
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

# Custom CSS dla lepszego wyglądu
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

DATA_FILE = "data/upcoming_predictions_final.csv"


def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    df = pd.read_csv(DATA_FILE)
    return df


df = load_data()

# ================================
#   PANEL BOCZNY
# ================================
st.sidebar.title("🎛️ Filtry")
if df is not None:
    min_conf = st.sidebar.slider("Minimalna pewność (%)", 30, 95, 45) / 100.0
    show_risky = st.sidebar.checkbox("Pokaż ryzykowne mecze", value=True)
else:
    min_conf = 0.0

st.sidebar.markdown("---")
st.sidebar.info("💡 **Legenda:**\n\n🟢 **Zielony**: Przewidywany zwycięzca\n🔴 **Czerwony**: ELO sugeruje dużą przewagę")

# ================================
#   GŁÓWNY WIDOK
# ================================
st.title("⚽ Piłkarzyki AI - Dashboard")

if df is None:
    st.error("❌ Brak danych! Uruchom najpierw: `python sportmonks_ai/predict_top5.py`")
    if st.button("🔄 Wygeneruj dane teraz"):
        os.system("python sportmonks_ai/predict_top5.py")
        st.rerun()
else:
    # Filtrowanie
    df_filtered = df[df["confidence"] >= min_conf].copy()
    if not show_risky:
        df_filtered = df_filtered[df_filtered["confidence"] > 0.6]

    # KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Mecze w analizie", len(df_filtered))

    pewniaki = df_filtered[df_filtered["confidence"] > 0.7]
    k2.metric("Super Pewniaki (>70%)", len(pewniaki))

    avg_conf = df_filtered["confidence"].mean()
    k3.metric("Średnia pewność", f"{avg_conf:.1%}")

    top_pick = df_filtered.sort_values("confidence", ascending=False).iloc[0] if not df_filtered.empty else None
    if top_pick is not None:
        winner = top_pick['home'] if top_pick['tip'] == 'H' else top_pick['away']
        k4.metric("Typ Dnia", winner, f"{top_pick['confidence']:.1%}")

    st.markdown("---")

    # ZAKŁADKI DLA LIG
    available_leagues = sorted(df_filtered["league"].unique())
    tabs = st.tabs([f"{LEAGUE_INFO.get(l, {'flag': '🏆'})['flag']} {LEAGUE_INFO.get(l, {'name': l})['name']}" for l in
                    available_leagues])

    for i, league_code in enumerate(available_leagues):
        with tabs[i]:
            league_matches = df_filtered[df_filtered["league"] == league_code]

            for _, row in league_matches.iterrows():
                # Logika kolorów - KTO WYGRYWA?
                tip = row['tip']
                conf = row['confidence']

                # Klasy CSS dla drużyn
                if tip == 'H':
                    class_h = "winner"
                    class_a = "loser"
                    bar_color = "green"  # Pasek w lewo/prawo
                    win_text = f"Wygrywa {row['home']}"
                elif tip == 'A':
                    class_h = "loser"
                    class_a = "winner"
                    bar_color = "red"
                    win_text = f"Wygrywa {row['away']}"
                else:  # Remis
                    class_h = "winner"  # Obie lekko zaznaczone
                    class_a = "winner"
                    bar_color = "orange"
                    win_text = "Przewidywany REMIS"

                # Karta meczu
                with st.container():
                    c1, c2, c3 = st.columns([4, 3, 4])

                    # --- GOSPODARZ (LEWA) ---
                    with c1:
                        st.markdown(f"<div style='text-align: right;'>", unsafe_allow_html=True)
                        st.markdown(f"<span class='{class_h}'>{row['home']}</span>", unsafe_allow_html=True)
                        st.markdown(
                            f"<br><span style='color: gray; font-size: 14px;'>ELO: {row['elo_home']:.0f}</span>",
                            unsafe_allow_html=True)
                        if tip == 'H':
                            st.markdown(f"🔥 <b style='color:#2ecc71'>{conf:.0%}</b>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # --- WYNIK (ŚRODEK) ---
                    with c2:
                        st.markdown(f"<div style='text-align: center;'>", unsafe_allow_html=True)
                        st.caption(f"{row['date']}")
                        st.markdown(f"<span class='score-box'>{row['pred_score']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='vs-text'>{win_text}</div>", unsafe_allow_html=True)

                        # Pasek pewności
                        if tip == 'H':
                            st.progress(int(conf * 100), text="Pewność AI (Home)")
                        elif tip == 'A':
                            # Streamlit progress idzie od lewej, więc dla Away ciężko wizualnie odwrócić,
                            # ale damy czerwony pasek
                            st.progress(int(conf * 100), text="Pewność AI (Away)")
                        else:
                            st.progress(int(conf * 100), text="Szansa na Remis")

                        st.markdown("</div>", unsafe_allow_html=True)

                    # --- GOŚĆ (PRAWA) ---
                    with c3:
                        st.markdown(f"<div style='text-align: left;'>", unsafe_allow_html=True)
                        st.markdown(f"<span class='{class_a}'>{row['away']}</span>", unsafe_allow_html=True)
                        st.markdown(
                            f"<br><span style='color: gray; font-size: 14px;'>ELO: {row['elo_away']:.0f}</span>",
                            unsafe_allow_html=True)
                        if tip == 'A':
                            st.markdown(f"🔥 <b style='color:#2ecc71'>{conf:.0%}</b>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Rozwijane szczegóły kursów
                    with st.expander("💰 Zobacz kursy i analizę"):
                        kc1, kc2, kc3 = st.columns(3)
                        kc1.metric("Kurs 1", f"{row['odds_home']:.2f}",
                                   delta="Faworyt" if row['odds_home'] < 2.0 else None)
                        kc2.metric("Kurs X", f"{row['odds_draw']:.2f}")
                        kc3.metric("Kurs 2", f"{row['odds_away']:.2f}",
                                   delta="Faworyt" if row['odds_away'] < 2.0 else None)