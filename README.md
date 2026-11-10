# F1 Manager

Простая консольная игра-менеджер Формулы 1 на Python 3 (без внешних библиотек).

## Запуск

**В браузере (Google Colab):**
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ahrisanov-lab/f1-manager/blob/main/f1_manager.ipynb)

Нажмите на значок, затем Runtime -> Run all. Ввод команд идёт в поле под ячейкой.

**В GitHub Codespaces:** [открыть](https://codespaces.new/ahrisanov-lab/f1-manager), затем в терминале `python f1_manager.py`.

**Локально:**

```
git clone https://github.com/ahrisanov-lab/f1-manager.git
cd f1-manager
python f1_manager.py
```

## Что есть в игре

- 10 команд, 20 пилотов (вымышленные имена), 8 трасс.
- Сила машины, надёжность, мастерство пилотов, пит-команда.
- Квалификация и гонка по кругам, очки, два зачёта.
- Сходы: аварии, поломки, проколы.
- Пит-стопы: софт, медиум, хард, интер, дождевые; износ шин; правило двух составов в сухую.
- Погода: прогноз, лёгкий дождь, ливень, смена условий по ходу гонки.
- Улучшения между этапами за бюджет.
