📘 PROJEKT: FOOTBALL MATCH PREDICTION AI (FINAL VERSION)
🏆 OPIS PROJEKTU
Celem projektu jest zaprojektowanie i implementacja systemu opartego na uczeniu maszynowym (Machine Learning), służącego do predykcji wyników meczów piłkarskich w pięciu czołowych ligach europejskich. System łączy historyczną analizę statystyczną, dynamiczne algorytmy rankingowe oraz modele klasyfikacyjne, aby oszacować prawdopodobieństwo wystąpienia konkretnych rozstrzygnięć sportowych.
Projekt realizowany jest w metodyce przyrostowej. Stage 3 stanowi finalną wersję systemu, wzbogaconą o zaawansowaną inżynierię cech, rygorystyczną walidację statystyczną oraz moduł biznesowy (Value Betting).

⚙️ STAGE 1: DATA ACQUISITION & PREPROCESSING
(Bez zmian - fundamenty systemu)
•	Integracja API: Pobieranie harmonogramów z football-data.org.
•	Strukturyzacja: ETL danych do formatu Pandas/CSV.
•	Zakres: Top 5 Lig Europy (PL, PD, BL1, SA, FL1).

🧠 STAGE 2: MACHINE LEARNING BASE
(Bez zmian - budowa silnika)
•	Modele: LightGBM (Klasyfikacja) + Random Forest (Regresja Goli).
•	ELO: Implementacja dynamicznego rankingu siły drużyn.
•	Streamlit: Podstawowy dashboard analityczny.

🚀 STAGE 3: ADVANCED ANALYTICS & VALIDATION (WERSJA FINALNA)
Trzeci, ostatni etap projektu skupił się na maksymalizacji skuteczności modelu, wdrożeniu cech opisujących "momentum" drużyn oraz profesjonalnej walidacji wyników pod kątem naukowym i biznesowym.
🆕 Kluczowe Innowacje w Stage 3:
1. Zaawansowana Inżynieria Cech (Advanced Feature Engineering)
  Model przestał polegać wyłącznie na rankingu ELO. Wprowadzono dynamiczne okna czasowe (Rolling Windows), które analizują formę z ostatnich 5 spotkań:
•	Rolling Form: Suma punktów zdobytych w ostatnich 5 meczach (wykrywanie "Hot Streaks" i kryzysów).
•	Attack & Defense Strength: Średnia liczba goli strzelonych i straconych (odróżnienie dominacji od szczęśliwych wygranych).
•	Aktualizacja Danych: Dołączono sezon 2025/2026, zapewniając modelowi wiedzę o najświeższej dyspozycji drużyn.
2. Metodologia Naukowa i Walidacja
  Wprowadzono rygorystyczne metryki oceny jakości modelu, odpowiadające standardom akademickim:
•	Baseline Comparison: Porównanie wyników modelu ze strategią naiwną ("Zero Rule" - stawianie zawsze na gospodarza).
  o	📉 Baseline: ~43.0%
  o	📈 AI Model: ~48.8% (Przewaga +5.8 p.p. nad rynkiem).
•	MCC (Matthews Correlation Coefficient): Wynik > 0.21 potwierdza, że model posiada realną zdolność predykcyjną, a nie zgaduje losowo.
•	Test Shapiro-Wilka: Analiza statystyczna rozkładu błędów (residuals) dla modułu regresji goli.
3. Moduł Oceny Ryzyka ("Pewniaki")
  Zaimplementowano system filtrowania predykcji oparty na progu pewności (Confidence Threshold).
•	Dla meczów o wysokiej pewności (>60%), skuteczność modelu wzrasta do ~64.3%.
•	Pozwala to na selekcję tylko najbardziej prawdopodobnych zdarzeń.
4. Inteligentne Mapowanie (Smart Mapping)
  Rozwiązano problem "Data Mismatch" pomiędzy nazwami drużyn w API a historycznymi plikami CSV. Zastosowano algorytm Fuzzy Matching oraz dedykowane słowniki, co pozwala na poprawne obliczanie ELO dla beniaminków i drużyn o zmiennych nazwach.
5. Dashboard Analityczny 2.0 (Hybrydowy)
Aplikacja w Streamlit została przebudowana i podzielona na dwa moduły:
•	🔮 Moduł Predykcyjny:
  o	Automatyczne wykrywanie Value Bets (sytuacji, gdzie AI ocenia szanse wyżej niż bukmacher).
  o	Oznaczenia "PEWNIAK" dla typów o wysokim prawdopodobieństwie.
•	📜 Moduł Analityczny:
  o	Interaktywne wykresy liniowe formy ELO w czasie.
  o	Szczegółowa historia ostatnich 10 meczów dla wybranej drużyny z kolorowaniem wyników (Z/R/P).

📊 WYNIKI KOŃCOWE (PERFORMANCE)
Metryka	Wartość	Komentarz
Accuracy (Ogólne)	48.80%	Przewaga nad strategią naiwną o blisko 6%.
Accuracy (High Conf.)	64.33%	Skuteczność dla typów o pewności > 60%.
MCC	0.2115	Wyraźna korelacja dodatnia (model działa).
MAE (Gole)	~0.98	Średni błąd przewidywania liczby bramek < 1.

🛠️ STACK TECHNOLOGICZNY (AKTUALIZACJA)
•	Core: Python 3.10+
•	Data Processing: Pandas, NumPy, Scipy (testy statystyczne).
•	Machine Learning:
  o	LightGBM (Klasyfikacja z class_weight='balanced' i tuningiem hiperparametrów).
  o	Random Forest (Regresja).
  o	Scikit-learn (Metryki, Preprocessing, Pipeline).
  •	Visualization: Streamlit, Plotly Express (interaktywne wykresy), Matplotlib/Seaborn (statyczne raporty).
  •	Integration: REST API (football-data.org).

📥 INSTRUKCJA URUCHOMIENIA
  System składa się z trzech niezależnych modułów, które należy uruchamiać sekwencyjnie:
  1.	Trening i ETL:

  python train_pro.py
  Pobiera dane (w tym sezon 25/26), liczy ELO/Formę, trenuje modele i generuje raporty skuteczności.
  2.	Generowanie Prognoz:

  python predict_top5.py
  Pobiera mecze na najbliższe dni z API, mapuje nazwy drużyn i generuje typy przy użyciu wytrenowanych modeli.  
  3.	Uruchomienie Dashboardu:

  streamlit run app.py
  Otwiera interfejs graficzny w przeglądarce.

