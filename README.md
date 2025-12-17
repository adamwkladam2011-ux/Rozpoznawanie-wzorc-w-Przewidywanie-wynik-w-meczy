📘 PROJEKT: FOOTBALL MATCH PREDICTION AI

🏆 OPIS PROJEKTU Celem projektu jest zaprojektowanie i implementacja systemu opartego na uczeniu maszynowym (Machine Learning), służącego do predykcji wyników meczów piłkarskich w pięciu czołowych ligach europejskich. System łączy historyczną analizę statystyczną, dynamiczne algorytmy rankingowe oraz modele klasyfikacyjne, aby oszacować prawdopodobieństwo wystąpienia konkretnych rozstrzygnięć sportowych.

Projekt realizowany jest w metodyce przyrostowej, podzielonej na trzy etapy (Stages), od akwizycji danych po wdrożenie interfejsu analitycznego.

⚙️ STAGE 1: DATA ACQUISITION & PREPROCESSING (AKWIZYCJA DANYCH) Pierwszym etapem projektu było zbudowanie fundamentów pod analizę danych poprzez stworzenie zautomatyzowanych potoków (pipelines) pobierających surowe dane.

Kluczowe funkcjonalności: 🔹 Integracja z API: Implementacja skryptów w języku Python łączących się z zewnętrznym API (football-data.org) w celu pobierania bieżących harmonogramów. 🔹 Zakres danych: 📅 Sezony: 2024/2025 (dane bieżące) oraz historia. 🏟️ Ligi: Premier League (Anglia), La Liga (Hiszpania), Bundesliga (Niemcy), Serie A (Włochy), Ligue 1 (Francja). 🔹 Strukturyzacja danych: Konwersja surowych odpowiedzi JSON do formatu tabelarycznego (Pandas DataFrame) i zapis do plików CSV. 🔹 Atrybuty: Data, Kod Ligi, Drużyny (Home/Away), Wynik końcowy, Status meczu.

🧠 STAGE 2: MACHINE LEARNING & FEATURE ENGINEERING (MODELOWANIE) W drugim etapie projekt ewoluował z prostego agregatora wyników w zaawansowany system predykcyjny. Wprowadzono inżynierię cech (Feature Engineering) oraz modele uczenia nadzorowanego.

Nowe moduły i funkcjonalności dodane w Stage 2:

🚀 1. Hybrydowy Model AI System wykorzystuje podejście zespołowe (Ensemble Learning), składające się z dwóch niezależnych modeli: • Klasyfikator (LightGBM): Odpowiada za predykcję klasy wyniku (1X2 – Gospodarz/Remis/Gość). Wybór podyktowany wysoką wydajnością algorytmu przy danych tabelarycznych. • Regresor (Random Forest): Odpowiada za przewidywanie dokładnej liczby goli dla obu drużyn, co pozwala na oszacowanie dokładnego wyniku (Correct Score).

📊 2. Dynamiczny Ranking ELO Zaimplementowano autorski algorytm obliczania siły drużyn metodą ELO. • System analizuje historię spotkań z ostatnich 5 lat. • Ranking jest aktualizowany po każdym meczu, co pozwala modelowi zrozumieć aktualną formę drużyny szybciej niż robią to statyczne tabele ligowe.

🛠️ 3. Inżynieria Cech (Feature Engineering) Model uczony jest na wektorach cech zawierających m.in.: • Różnicę punktów ELO między rywalami. • Symulowane Fair Odds (Uczciwe Kursy) wyliczane na podstawie prawdopodobieństwa wynikającego z ELO. • Historię bezpośrednich spotkań.

📈 4. Rozszerzony Dataset Treningowy Zintegrowano zewnętrzne źródła danych historycznych (football-data.co.uk), zwiększając bazę treningową do ponad 10 000 rekordów meczowych, co znacząco poprawiło generalizację modelu.

📈 5. Implementacja: 🔹 Stworzono interaktywny dashboard przy użyciu biblioteki Streamlit. 🔹 Funkcje analityczne: • Wizualizacja Pewności Modelu (Confidence Score) w postaci paska postępu. • Automatyczne oznaczanie faworytów (kolorowanie dynamiczne). • Filtrowanie predykcji według lig oraz poziomu ryzyka. • Porównanie kursów rynkowych z predykcją AI.

🛠️ STACK TECHNOLOGICZNY

🐍 Język programowania: Python 3.10+ 🐼 Data Science: Pandas, NumPy 🤖 Machine Learning: Scikit-learn, LightGBM, Joblib 🌐 Integracja API: Requests, REST API 📊 Frontend / Wizualizacja: Streamlit 📂 Kontrola Wersji: Git & GitHub

📊 METODOLOGIA MODELU Proces decyzyjny modelu przebiega w następujących krokach:

  1. Pobranie harmonogramu na najbliższe 7 dni.

  2. Mapowanie drużyn w celu powiązania nazw z API z bazą historyczną ELO.

  3. Obliczenie różnicy siły (ELO Delta) dla każdej pary meczowej.

  4. Predykcja probabilistyczna (LightGBM) – wyznaczenie szans procentowych na zwycięstwo.

  5. Predykcja numeryczna (Random Forest) – oszacowanie liczby goli.

  6. Prezentacja wyników w dashboardzie z rekomendacją typu.
