# Propozycja metody tworzenia modelu BPMN na podstawie danych wyodrębnionych z modelu DMN

Projekt został wykonany w ramach przedmiotu "Modelowanie i Analiza Procesów Biznesowych" na studiach II stopnia kierunku Automatyka i Robotyka na Akademii Górniczo-Hutniczej w Krakowie.

## Przegląd

Projekt implementuje algorytm automatycznego generowania modeli BPMN (Business Process Model and Notation) na podstawie modeli DMN (Decision Model and Notation). Algorytm analizuje strukturę modelu DMN, w tym decyzje, dane wejściowe, modele wiedzy biznesowej oraz ich relacje, a następnie tworzy odpowiedni diagram procesu BPMN.

## Wymagania

- Python 3.6+
- Biblioteki wymienione w pliku `requirements.txt`

## Instalacja

1. Sklonuj repozytorium:
```
git clone https://github.com/yourusername/MiAPB.git
cd MiAPB
```

2. Zainstaluj wymagane biblioteki:
```
pip install -r requirements.txt
```

## Użycie

### Generowanie modelu BPMN z modelu DMN

```python
from processing.generator import generate_bpmn_from_dmn

# Generowanie BPMN z pliku DMN
dmn_path = "event_logs/d1.dmn"
output_path = "output"
bpmn_file = generate_bpmn_from_dmn(dmn_path, output_path)
```

## Struktura projektu

- `models/` - katalog zawierający definicje modeli
  - `dmn_model.py` - definicja klasy modelu DMN z obsługą decyzji, danych wejściowych i wymagań
- `processing/` - katalog zawierający moduły przetwarzania
  - `extractor.py` - moduł do ekstrakcji modeli DMN z plików XML
  - `mapper.py` - moduł implementujący algorytm mapowania DMN na BPMN
  - `generator.py` - moduł wysokiego poziomu do generowania BPMN z modeli DMN
- `event_logs/` - katalog zawierający przykładowe pliki DMN i dzienniki zdarzeń
- `output/` - katalog na wygenerowane pliki BPMN

## Algorytm

Algorytm mapowania DMN na BPMN składa się z następujących kroków:

1. Ekstrakcja modelu DMN z pliku XML
2. Analiza grafu decyzyjnego w celu określenia poziomów decyzji i zależności
3. Identyfikacja elementów początkowych (decyzje i dane wejściowe)
4. Mapowanie danych wejściowych na odpowiednie elementy BPMN (zdarzenia początkowe, zadania użytkownika itp.)
5. Mapowanie decyzji na zadania reguł biznesowych
6. Dodawanie bramek logicznych (AND, XOR) dla przepływów równoległych i wykluczających się
7. Łączenie elementów sekwencyjnie zgodnie z zależnościami w modelu DMN
8. Tworzenie elementów pośrednich dla danych wejściowych niebędących elementami początkowymi
9. Pozycjonowanie elementów na podstawie ich poziomu w przepływie decyzyjnym
10. Generowanie końcowego modelu BPMN

## Funkcje

Obecna implementacja zawiera:

- Dynamiczne pozycjonowanie elementów na podstawie ich poziomu w przepływie decyzyjnym
- Inteligentne mapowanie danych wejściowych na odpowiednie elementy BPMN w zależności od kontekstu
- Automatyczne dodawanie bramek dla decyzji z wieloma wejściami lub wyjściami
- Obsługę modeli wiedzy biznesowej i źródeł wiedzy
- Obsługę redundantnych wymagań informacyjnych