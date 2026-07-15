#!/usr/bin/env python3
"""Читает/обновляет Docs/.p3flow/state.yaml — прогресс по активностям p3-flow.

Использование:
  python3 progress_tracker.py status                    # показать состояние
  python3 progress_tracker.py complete A03              # отметить активность выполненной
  python3 progress_tracker.py set current_activity C1   # установить произвольное поле
  python3 progress_tracker.py doc project-description in_progress   # статус документа
  python3 progress_tracker.py cycle week-2026-07-14     # зафиксировать завершённый цикл

Опция --root задаёт корень репозитория (по умолчанию — текущий каталог).
Без внешних зависимостей: state.yaml разбирается упрощённо (плоские ключи,
inline-списки, documents как вложенный блок с inline-словарями).
"""
import argparse
import re
import sys
from pathlib import Path

# порядок активностей по методологиям
ORDERS = {
    "p3-express": (
        [f"A{i:02d}" for i in range(1, 11)]
        + [f"B{i:02d}" for i in range(1, 6)]
        + [f"C{i:02d}" for i in range(1, 5)]
        + [f"D{i:02d}" for i in range(1, 3)]
        + [f"E{i:02d}" for i in range(1, 4)]
        + [f"F{i:02d}" for i in range(1, 7)]
        + [f"G{i:02d}" for i in range(1, 4)]
    ),
    "micro-p3-express": (
        [f"A{i}" for i in range(1, 8)]
        + [f"C{i}" for i in range(1, 5)]
        + [f"D{i}" for i in range(1, 3)]
        + [f"E{i}" for i in range(1, 5)]
        + [f"F{i}" for i in range(1, 8)]
        + [f"G{i}" for i in range(1, 4)]
    ),
}
# после инициации начинается цикл: у P3 — месячный (B01), у micro — недельный (C1)
CYCLE_START = {"p3-express": "B01", "micro-p3-express": "C1"}
INITIATION_LAST = {"p3-express": "A10", "micro-p3-express": "A7"}
# конец цикла возвращает к его началу (закрытие проекта F — только явным set)
CYCLE_LOOP = {"p3-express": {"E03": "B01"}, "micro-p3-express": {"E4": "C1"}}


def state_file(root: str) -> Path:
    p = Path(root) / "Docs/.p3flow/state.yaml"
    if not p.exists():
        print(f"ОШИБКА: {p} не найден. Сначала выполните init_repo.py.", file=sys.stderr)
        sys.exit(1)
    return p


def parse(text: str) -> dict:
    data: dict = {"documents": {}}
    in_docs = False
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("documents:"):
            in_docs = True
            continue
        if in_docs and line.startswith("  ") and ":" in line:
            name, rest = line.strip().split(":", 1)
            m = re.search(r"status:\s*([\w-]+).*path:\s*([^,}]+)", rest)
            if m:
                data["documents"][name] = {"status": m.group(1), "path": m.group(2).strip()}
            continue
        in_docs = False
        if ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            val = val.strip().strip('"')
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                data[key] = [x.strip() for x in inner.split(",")] if inner else []
            else:
                data[key] = val
    return data


def dump(data: dict) -> str:
    lines = []
    for key in ("methodology", "project_name", "started_at", "current_group", "current_activity"):
        val = data.get(key, "")
        if key == "project_name":
            val = f'"{val}"'
        lines.append(f"{key}: {val}")
    lines.append(f"completed_activities: [{', '.join(data.get('completed_activities', []))}]")
    lines.append("documents:")
    for name, d in data["documents"].items():
        lines.append(f"  {name}: {{status: {d['status']}, path: {d['path']}}}")
    ch = data.get("cycle_history", [])
    lines.append(f"cycle_history: [{', '.join(ch) if isinstance(ch, list) else ch}]")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_complete = sub.add_parser("complete")
    p_complete.add_argument("activity")
    p_set = sub.add_parser("set")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_doc = sub.add_parser("doc")
    p_doc.add_argument("name")
    p_doc.add_argument("status", choices=["not_started", "in_progress", "done"])
    p_cycle = sub.add_parser("cycle")
    p_cycle.add_argument("cycle_id", help="например week-2026-07-14 или month-2026-07")
    args = ap.parse_args()

    path = state_file(args.root)
    data = parse(path.read_text(encoding="utf-8"))
    methodology = data.get("methodology", "")
    order = ORDERS.get(methodology, [])

    if args.cmd == "status":
        done = data.get("completed_activities", [])
        print(f"Проект: {data.get('project_name')} · методология: {methodology}")
        print(f"Текущая активность: {data.get('current_activity')} (группа {data.get('current_group')})")
        print(f"Выполнено активностей: {len(done)}: {', '.join(done) if done else '—'}")
        for name, d in data["documents"].items():
            print(f"  документ {name}: {d['status']} ({d['path']})")
        return 0

    if args.cmd == "complete":
        act = args.activity.upper()
        if order and act not in order:
            print(f"ОШИБКА: активность {act} не существует в {methodology}.", file=sys.stderr)
            return 1
        done = data.get("completed_activities", [])
        if act not in done:
            done.append(act)
        data["completed_activities"] = done
        # следующая активность: конец инициации → старт цикла; конец цикла → его начало
        loop = CYCLE_LOOP.get(methodology, {})
        if act == INITIATION_LAST.get(methodology):
            nxt = CYCLE_START.get(methodology, "")
        elif act in loop:
            nxt = loop[act]
        else:
            idx = order.index(act)
            nxt = order[idx + 1] if idx + 1 < len(order) else act
        data["current_activity"] = nxt
        data["current_group"] = nxt[0] if nxt else data.get("current_group", "")
        path.write_text(dump(data), encoding="utf-8")
        print(f"Активность {act} отмечена. Следующая: {nxt}")
        if act in loop:
            print("Цикл замкнулся. Не забудьте зафиксировать его: progress_tracker.py cycle <id>.")
            print("Для закрытия проекта переведите вручную: progress_tracker.py set current_activity "
                  + ("F01" if methodology == "p3-express" else "F1"))
        return 0

    if args.cmd == "set":
        data[args.key] = args.value
        if args.key == "current_activity":
            data["current_group"] = args.value[0].upper()
        path.write_text(dump(data), encoding="utf-8")
        print(f"{args.key} = {args.value}")
        return 0

    if args.cmd == "doc":
        if args.name not in data["documents"]:
            print(f"ОШИБКА: документ {args.name} не найден. Есть: {', '.join(data['documents'])}", file=sys.stderr)
            return 1
        data["documents"][args.name]["status"] = args.status
        path.write_text(dump(data), encoding="utf-8")
        print(f"документ {args.name}: {args.status}")
        return 0

    if args.cmd == "cycle":
        ch = data.get("cycle_history", [])
        if not isinstance(ch, list):
            ch = [ch] if ch else []
        if args.cycle_id not in ch:
            ch.append(args.cycle_id)
        data["cycle_history"] = ch
        path.write_text(dump(data), encoding="utf-8")
        print(f"Цикл {args.cycle_id} зафиксирован. Всего циклов: {len(ch)}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
