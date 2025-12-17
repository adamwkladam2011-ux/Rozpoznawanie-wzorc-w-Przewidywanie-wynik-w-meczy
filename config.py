# config.py

# 🔑 Klucz do API-Sports Football
API_KEY = "2da3f454f02054513d765fa93c9f82b3"
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

# Top 5 lig (ID z API-Sports)
LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
}

# 📅 Sezon bieżący (do pobierania nadchodzących meczów)
SEASON = 2025

# 🚧 Opóźnienie (w sekundach) między zapytaniami API
# Darmowe konto ma limit 10 zapytań/minutę -> co najmniej 6-7 sekund przerwy
RATE_LIMIT_DELAY = 7