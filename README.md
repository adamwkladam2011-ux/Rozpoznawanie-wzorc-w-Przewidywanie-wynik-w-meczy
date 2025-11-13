Stage 1: Football Match Results Dataset
🏆 Football Match Prediction AI – Stage 1: Data Collection

Cel projektu:
Celem całego projektu jest stworzenie systemu sztucznej inteligencji (AI), który przewiduje wyniki meczów piłkarskich w topowych ligach europejskich.
Projekt podzielono na trzy etapy (Stage 1 → Stage 3), które rozwijają się krok po kroku — od czystych wyników po pełny model predykcyjny.

⚙️ Stage 1: Pobieranie wyników meczów

W tym etapie przygotowano skrypt w Pythonie (przystosowany do działania w Google Colab), który automatycznie pobiera dane o meczach z pięciu najlepszych lig europejskich z serwisu Football-Data.org
.

Zakres danych:

📅 Sezony: 2024 oraz 2025

🏟️ Ligi:

Premier League (Anglia)

Ligue 1 (Francja)

Bundesliga (Niemcy)

La Liga (Hiszpania)

Serie A (Włochy)

📊 Dane w pliku CSV:

data – data i godzina meczu (UTC)

liga, kod_ligi

gospodarz, goście

wynik – gole gospodarzy i gości

kolejka, status, sezon
