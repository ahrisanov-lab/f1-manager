import random

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

# name: (power, reliability, [(driver, skill), ...])
TEAMS = {
    "Red Falcon":   (92, 88, [("M. Verstov", 95), ("S. Perrez", 84)]),
    "Scuderia Rosa":(89, 82, [("C. Leclair", 91), ("L. Sainto", 87)]),
    "Silver Arrow": (88, 90, [("L. Hamilt", 93), ("G. Russel", 88)]),
    "Papaya Racing":(90, 85, [("L. Norrison", 92), ("O. Piastro", 86)]),
    "Green Motors": (82, 84, [("F. Alonzo", 90), ("L. Stroll", 78)]),
    "Alpine Blue":  (78, 80, [("P. Gaslin", 82), ("E. Ocone", 80)]),
    "Williams Old": (75, 83, [("A. Albon", 83), ("C. Sainz", 87)]),
    "Haas Stripe":  (72, 78, [("N. Hulkan", 82), ("K. Magnus", 79)]),
    "RB Juniors":   (76, 81, [("Y. Tsunodo", 80), ("D. Ricciardi", 81)]),
    "Sauber Green": (68, 76, [("V. Botas", 81), ("G. Zhou", 74)]),
}

# name, обгоны(0-1), риск аварий, вес машины, круги, базовое время круга, потеря в боксах, шанс дождя
TRACKS = [
    ("Бахрейн",      0.35, 0.30, 0.60, 57,  96, 22, 0.02),
    ("Монако",       0.95, 0.80, 0.30, 78,  74, 19, 0.20),
    ("Монца",        0.30, 0.35, 0.80, 53,  82, 20, 0.15),
    ("Сильверстоун", 0.45, 0.40, 0.65, 52,  90, 20, 0.35),
    ("Спа",          0.35, 0.45, 0.70, 44, 107, 18, 0.45),
    ("Сузука",       0.70, 0.55, 0.50, 53,  93, 22, 0.30),
    ("Баку",         0.40, 0.75, 0.55, 51, 104, 20, 0.10),
    ("Интерлагос",   0.40, 0.50, 0.55, 71,  72, 19, 0.40),
]

# название, износ (сек/круг), ресурс (круги)
TYRES = {
    "S": ("Софт", 0.07, 18),
    "M": ("Медиум", 0.04, 30),
    "H": ("Хард", 0.025, 42),
    "I": ("Интер", 0.05, 35),
    "W": ("Дождевые", 0.04, 40),
}
# штраф к времени круга: (сухо, лёгкий дождь, ливень)
PEN = {
    "S": (-0.6, 5.0, 12.0),
    "M": (0.0, 4.5, 11.0),
    "H": (0.5, 4.0, 10.5),
    "I": (4.0, 0.0, 3.5),
    "W": (7.0, 2.5, 0.0),
}
RAIN_BASE = (0, 6, 13)           # на сколько дождь замедляет всех
WET_NAMES = ("сухо", "лёгкий дождь", "ливень")
MODES = {"1": ("Осторожно", 0.15, 0.6, 0.8),
         "2": ("Нормально", 0.0, 1.0, 1.0),
         "3": ("Агрессивно", -0.15, 1.6, 1.25)}


class Driver:
    def __init__(self, name, skill, team):
        self.name, self.skill, self.team = name, skill, team
        self.points = self.wins = self.dnfs = 0


class Team:
    def __init__(self, name, power, rel, drivers):
        self.name, self.power, self.rel = name, power, rel
        self.pit = max(60, min(95, rel + random.randint(-6, 6)))
        self.drivers = [Driver(n, s, self) for n, s in drivers]
        self.points = 0
        self.budget = 10


class Car:
    def __init__(self, d, grid_pos):
        self.d = d
        self.tyre = "M"
        self.age = 0
        self.used = set()          # использованные сухие составы
        self.wet_used = False
        self.stops = 0
        self.cum = grid_pos * 0.25  # время от старта (с)
        self.alive = True
        self.last = 0.0
        self.limit = 30
        self.dnf = None
        self.planned = []
        self.manual = False
        self.lp = -99               # круг последнего запроса игроку
        self.penalty = 0

    def set_tyre(self, t):
        self.tyre, self.age = t, 0
        self.limit = TYRES[t][2] * random.uniform(0.75, 1.0)
        if t in "SMH":
            self.used.add(t)
        else:
            self.wet_used = True


def suited(t, w):
    return (w == 0 and t in "SMH") or (w == 1 and t == "I") or (w == 2 and t == "W")


def pick_dry(c, laps_left):
    cands = [t for t in "SMH" if TYRES[t][2] * 0.95 >= laps_left] or ["M", "H"]
    unused = [t for t in cands if t not in c.used]
    if len(c.used) < 2 and unused:
        cands = unused
    return random.choice(cands)


def pick_for_weather(c, w, laps_left):
    return pick_dry(c, laps_left) if w == 0 else ("I" if w == 1 else "W")


def make_weather(laps, chance):
    wet = [0] * laps
    if random.random() < chance:
        start = 0 if random.random() < 0.25 else random.randint(int(laps * 0.1), int(laps * 0.7))
        length = random.randint(int(laps * 0.15), int(laps * 0.5))
        peak = random.choice([1, 2])
        end = min(laps, start + length)
        for l in range(start, end):
            pos = (l - start) / max(1, length)
            wet[l] = peak if 0.25 < pos < 0.75 else 1
    return wet


def forecast(wet, chance, laps):
    actual = 1 if any(wet) else 0
    p = min(max(0.55 * actual + 0.45 * chance + random.uniform(-0.15, 0.15), 0), 1)
    txt = f"вероятность дождя ~{round(p * 100 / 5) * 5}%"
    if p > 0.5 and any(wet):
        first = wet.index(next(x for x in wet if x)) + 1
        guess = max(1, first + random.randint(-8, 8))
        txt += f", начало примерно около круга {guess}"
    return txt


def qualifying(drivers, w0):
    res = []
    for d in drivers:
        skill_share = 0.45 + 0.10 * w0
        t = d.team.power * (1 - skill_share) + d.skill * skill_share + random.gauss(0, 3 + 3 * w0)
        res.append((t, d))
    res.sort(key=lambda x: -x[0])
    return [d for _, d in res]


def ask_tyre(c, lap, laps, w, reason, pos):
    t = TYRES[c.tyre]
    print(f"\n[Круг {lap + 1}/{laps}] {c.d.name}: P{pos}, шины {t[0]} ({c.age} кр., ресурс ~{t[2]}), "
          f"трасса: {WET_NAMES[w]}. {reason}")
    ans = input("  s/m/h = слики, i = интер, w = дождевые, a = авто, Enter = остаться: ").strip().lower()
    if ans in ("s", "m", "h", "i", "w"):
        return ans.upper()
    if ans == "a":
        return pick_for_weather(c, w, laps - lap)
    return None


def ai_pit(c, w, laps_left):
    if laps_left <= 2:
        return None
    if not suited(c.tyre, w):
        return pick_for_weather(c, w, laps_left) if random.random() < 0.3 else None
    if c.age >= c.limit and laps_left > 4:
        return pick_for_weather(c, w, laps_left)
    return None


def do_pit(c, new, pit_loss):
    t = pit_loss + max(1.9, random.gauss(2.4, 0.35))
    note = ""
    if random.random() < (100 - c.d.team.pit) / 100 * 0.15:
        extra = random.uniform(3, 8)
        t += extra
        note = f" — медленный стоп (+{extra:.1f}с)"
    elif random.random() < 0.01:
        t += 15
        note = " — ЧП в боксах (+15с)"
    c.cum += t
    c.stops += 1
    c.set_tyre(new)
    return note


def race(grid, track, wet, modes, player, manual, start_tyre, stops):
    name, overtake, crash_risk, pw, laps, base, pit_loss, _ = track
    cars = [Car(d, i) for i, d in enumerate(grid)]
    for c in cars:
        if c.d.team is player and manual:
            c.manual = True
            c.set_tyre(start_tyre)
            c.planned = [int(laps * (i + 1) / (stops + 1)) for i in range(stops)]
        elif wet[0] == 0:
            c.set_tyre(random.choices(["S", "M", "H"], [0.35, 0.45, 0.2])[0])
        else:
            c.set_tyre("I" if wet[0] == 1 else "W")
    dnf = []
    for lap in range(laps):
        w = wet[lap]
        if lap > 0 and w != wet[lap - 1]:
            print(f">>> Круг {lap + 1}: {WET_NAMES[w].upper()}!")
        order = sorted([c for c in cars if c.alive], key=lambda c: c.cum)
        starts = {id(c): c.cum for c in order}
        for idx, c in enumerate(order):
            laps_left = laps - lap
            is_p = c.d.team is player
            new = None
            if c.manual:
                reasons = []
                if lap > 0 and laps_left > 2:
                    if not suited(c.tyre, w) and lap - c.lp >= 2:
                        reasons.append("Шины не подходят к погоде!")
                    if lap in c.planned:
                        reasons.append("Плановый пит-стоп.")
                    if c.age >= TYRES[c.tyre][2] and lap - c.lp >= 3:
                        reasons.append("Шины на пределе!")
                if reasons:
                    c.lp = lap
                    new = ask_tyre(c, lap, laps, w, " ".join(reasons), idx + 1)
            else:
                new = ai_pit(c, w, laps_left)
            if new:
                note = do_pit(c, new, pit_loss)
                if is_p:
                    print(f"  Круг {lap + 1}: {c.d.name} в боксах -> {TYRES[new][0]}{note}")

            mode = modes.get(c.d.team.name, MODES["2"])
            ppw = pw * (1 - 0.25 * w)
            perf = c.d.team.power * ppw + c.d.skill * (1 - ppw)
            lt = base + (100 - perf) * 0.12 + RAIN_BASE[w] + PEN[c.tyre][w]
            wear = TYRES[c.tyre][1] * mode[3]
            if c.tyre in "IW" and w == 0:
                wear *= 4
            lt += wear * c.age
            life = TYRES[c.tyre][2]
            if c.age > life:
                lt += 0.3 * (c.age - life)
            lt += (laps - lap) * 0.03 + mode[1]
            lt += random.gauss(0, 0.25 + 0.35 * w * (100 - c.d.skill) / 50)
            if idx > 0:
                ahead = order[idx - 1]
                if ahead.alive and starts[id(c)] - starts[id(ahead)] < 1.0 \
                        and lt < ahead.last + 0.1 and random.random() < overtake * 0.9:
                    lt = ahead.last + random.uniform(0.05, 0.3)
            c.last = lt
            c.cum += lt
            c.age += 1

            factor = 1 + 0.8 * w
            if not suited(c.tyre, w):
                factor *= 3 if w > 0 else 1.5
            p_crash = (((100 - c.d.skill) / 100) * crash_risk * 0.25 * mode[2] + 0.01) / laps * factor
            p_mech = ((100 - c.d.team.rel) / 100) * 0.35 / laps
            p_burst = 0.04 if c.age > life + 6 else 0
            r = random.random()
            reason = None
            if r < p_crash:
                reason = "авария"
            elif r < p_crash + p_mech:
                reason = random.choice(["двигатель", "коробка", "гидравлика", "тормоза", "перегрев"])
            elif r < p_crash + p_mech + p_burst:
                reason = "пробитая шина"
            if reason:
                c.alive = False
                c.dnf = (reason, lap + 1)
                dnf.append(c)
                if is_p:
                    print(f"  !!! Круг {lap + 1}: {c.d.name} сходит — {reason}")

    rainy = any(wet)
    for c in cars:
        if c.alive and not rainy and len(c.used) < 2:
            c.penalty = 20
            if c.d.team is player:
                print(f"  Штраф +20с: {c.d.name} не использовал два разных сухих состава")
    finishers = sorted([c for c in cars if c.alive], key=lambda c: c.cum + c.penalty)
    for i, c in enumerate(finishers):
        if i < len(POINTS):
            c.d.points += POINTS[i]
            c.d.team.points += POINTS[i]
    if finishers:
        finishers[0].d.wins += 1
    for c in dnf:
        c.d.dnfs += 1
    return finishers, dnf


def show_race(track, grid, finishers, dnf, player, wet):
    print(f"\n=== Гран-при: {track[0]} ({track[4]} кругов) ===")
    rain_laps = sum(1 for x in wet if x)
    print(f"Дождь шёл {rain_laps} из {track[4]} кругов" if rain_laps else "Гонка прошла всухую")
    print("Старт:", ", ".join(f"{i + 1}.{d.name}" for i, d in enumerate(grid[:5])), "...")
    print("\nФиниш:")
    best = finishers[0].cum + finishers[0].penalty if finishers else 0
    for i, c in enumerate(finishers, 1):
        pts = POINTS[i - 1] if i <= len(POINTS) else 0
        gap = "" if i == 1 else f"+{c.cum + c.penalty - best:.1f}с"
        mark = " <== ВАШ" if c.d.team is player else ""
        print(f"{i:>2}. {c.d.name:<14} {c.d.team.name:<14} {gap:>9} пит:{c.stops} +{pts}{mark}")
    if dnf:
        print("\nСходы:")
        for c in dnf:
            mark = " <== ВАШ" if c.d.team is player else ""
            print(f"  {c.d.name:<14} {c.d.team.name:<14} {c.dnf[0]}, круг {c.dnf[1]}{mark}")


def standings(teams, drivers, top=10):
    print("\n--- Пилоты ---")
    for i, d in enumerate(sorted(drivers, key=lambda x: (-x.points, -x.wins))[:top], 1):
        print(f"{i:>2}. {d.name:<14} {d.team.name:<14} {d.points:>4} очк. | победы {d.wins} | сходы {d.dnfs}")
    print("--- Команды ---")
    for i, t in enumerate(sorted(teams, key=lambda x: -x.points), 1):
        print(f"{i:>2}. {t.name:<14} {t.points:>4} очк. | сила {t.power} | надёжн. {t.rel} | пит {t.pit}")


def upgrade_menu(team):
    while team.budget > 0:
        print(f"\nБюджет: {team.budget} | Сила: {team.power} | Надёжность: {team.rel} | Пит-команда: {team.pit}")
        c = input("1 - мощность (+2, цена 3), 2 - надёжность (+2, цена 2), "
                  "3 - пит-команда (+3, цена 2), Enter - дальше: ").strip()
        if c == "1" and team.budget >= 3:
            team.budget -= 3; team.power = min(100, team.power + 2)
        elif c == "2" and team.budget >= 2:
            team.budget -= 2; team.rel = min(100, team.rel + 2)
        elif c == "3" and team.budget >= 2:
            team.budget -= 2; team.pit = min(98, team.pit + 3)
        elif c == "":
            break
        else:
            print("Не хватает бюджета или неверный ввод.")


def main():
    teams = [Team(n, *v) for n, v in TEAMS.items()]
    drivers = [d for t in teams for d in t.drivers]
    print("=== F1 MANAGER ===")
    for i, t in enumerate(teams, 1):
        print(f"{i:>2}. {t.name:<14} сила {t.power}, надёжн. {t.rel}, пит {t.pit}, пилоты: "
              + ", ".join(f"{d.name}({d.skill})" for d in t.drivers))
    while True:
        try:
            player = teams[int(input("\nВыберите команду (номер): ")) - 1]
            break
        except (ValueError, IndexError):
            pass
    player.budget = 12

    for n, track in enumerate(TRACKS, 1):
        laps = track[4]
        wet = make_weather(laps, track[7])
        print(f"\n########## Этап {n}/{len(TRACKS)}: {track[0]} ({laps} кр.) ##########")
        print(f"Обгоны: {track[1]:.0%} сложности, риск аварий {track[2]:.0%}, важность машины {track[3]:.0%}")
        print("Прогноз:", forecast(wet, track[7], laps))
        upgrade_menu(player)

        print("\nРежим гонки: 1 - Осторожно, 2 - Нормально, 3 - Агрессивно")
        m = input("Выбор [2]: ").strip() or "2"
        modes = {player.name: MODES.get(m, MODES["2"])}

        manual = input("Управлять пит-стопами вручную? (y/n) [n]: ").strip().lower() == "y"
        start_tyre, stops = "M", 1
        if manual:
            print("Стартовые шины: s=Софт (быстрые, 18 кр.), m=Медиум (30), h=Хард (42), i=Интер, w=Дождевые")
            s = input("Старт на [m]: ").strip().lower() or "m"
            start_tyre = s.upper() if s in ("s", "m", "h", "i", "w") else "M"
            try:
                stops = max(0, min(4, int(input("Плановых пит-стопов (0-4) [2]: ") or 2)))
            except ValueError:
                stops = 2
            print("В сухую нужно использовать минимум 2 разных состава, иначе штраф +20с.")

        grid = qualifying(drivers, wet[0])
        print(f"\nКвалификация: {WET_NAMES[wet[0]]}. Поул: {grid[0].name} ({grid[0].team.name})")
        finishers, dnf = race(grid, track, wet, modes, player, manual, start_tyre, stops)
        show_race(track, grid, finishers, dnf, player, wet)

        gained = sum(POINTS[i] for i, c in enumerate(finishers)
                     if i < len(POINTS) and c.d.team is player)
        player.budget += 2 + gained // 6
        standings(teams, drivers, top=6)
        input("\nEnter - дальше...")

    print("\n######## ИТОГИ СЕЗОНА ########")
    standings(teams, drivers)
    champ = max(teams, key=lambda t: t.points)
    print(f"\nКубок конструкторов: {champ.name}" + (" — ВЫ ЧЕМПИОНЫ!" if champ is player else ""))


if __name__ == "__main__":
    main()
