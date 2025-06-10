# DMN to BPMN Generator

Generator modeli BPMN na podstawie modeli DMN zgodnie z algorytmem opisanym w artykule "Proposal of a Method for Creating a BPMN Model based on the Data Extracted from a DMN Model".

## Wymagania

- Python 3.6+
- Biblioteki wymienione w `requirements.txt`

## Instalacja

1. Sklonuj repozytorium:
```
git clone https://github.com/username/MiAPB.git
cd MiAPB
```

2. Zainstaluj wymagane biblioteki:
```
pip install -r requirements.txt
```

## Użycie

### Generowanie modelu BPMN z modelu DMN

```
python dmn_to_bpmn_generator.py "event_logs/d1.dmn" -o "output/generated_bpmn.bpmn"
```

Gdzie:
- `event_logs/d1.dmn` to ścieżka do pliku DMN (względna lub absolutna)
- `-o output/generated_bpmn.bpmn` to opcjonalna ścieżka wyjściowa dla wygenerowanego pliku BPMN

Jeśli nie podasz parametru `-o`, plik BPMN zostanie zapisany w tej samej lokalizacji co plik DMN, ale z rozszerzeniem `.bpmn`.

### Wizualizacja grafu przejść

```
python config.py
```

Ten skrypt wczytuje plik XES, generuje mapę przejść i wizualizuje ją jako graf.

## Struktura projektu

- `dmn_to_bpmn_generator.py` - główny skrypt do generowania modeli BPMN z modeli DMN
- `config.py` - skrypt konfiguracyjny do wizualizacji grafu przejść
- `event_logs/` - katalog zawierający pliki XES i DMN
- `models/` - katalog zawierający definicje modeli DMN i BPMN
- `processing/` - katalog zawierający moduły przetwarzania
  - `extractor.py` - moduł do ekstrakcji modeli DMN z plików XML
  - `mapper.py` - moduł do mapowania ścieżek na grafy przejść
  - `dmn_to_bpmn.py` - moduł implementujący algorytm mapowania DMN na BPMN
- `visualization/` - katalog zawierający moduły wizualizacji
  - `bpmn_renderer.py` - moduł do wizualizacji modeli BPMN
- `output/` - katalog na pliki wyjściowe

## Algorytm

Algorytm mapowania DMN na BPMN składa się z następujących kroków:

1. Ekstrakcja modelu DMN z pliku XML
2. Przetworzenie modelu DMN (usunięcie redundantnych wymagań informacyjnych)
3. Identyfikacja elementów początkowych (decyzje i dane wejściowe)
4. Mapowanie danych wejściowych na zdarzenia początkowe lub zadania użytkownika
5. Mapowanie decyzji na zadania reguł biznesowych
6. Dodanie bramek logicznych (AND, XOR) dla równoległych i wykluczających się przepływów
7. Łączenie elementów sekwencyjnie zgodnie z zależnościami w modelu DMN
8. Tworzenie zdarzenia końcowego
9. Generowanie wizualizacji modelu BPMN