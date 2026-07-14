#!/usr/bin/env python3
"""Создаёт структуру Docs/ и стартовый state.yaml для p3-flow.

Использование:
  python3 init_repo.py --methodology p3-express --project-name "Мой проект" [--root .]

Без внешних зависимостей (yaml пишется как текст).
"""
import argparse
import datetime
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

STRUCTURE = {
    "p3-express": {
        "dirs": [
            "Docs/.p3flow",
            "Docs/01-project-description",
            "Docs/02-deliverables-map/diagrams",
            "Docs/03-follow-up-register",
            "Docs/04-health-register",
            "Docs/cycles",
            "Docs/diagrams",
        ],
        "templates": {
            "p3-express/project-description.md": "Docs/01-project-description/project-description.md",
            "p3-express/deliverables-map.md": "Docs/02-deliverables-map/deliverables-map.md",
            "p3-express/follow-up-register.md": "Docs/03-follow-up-register/follow-up-register.md",
            "p3-express/health-register.md": "Docs/04-health-register/health-register.md",
        },
        "first_activity": "A01",
        "documents": {
            "project-description": "Docs/01-project-description/project-description.md",
            "deliverables-map": "Docs/02-deliverables-map/deliverables-map.md",
            "follow-up-register": "Docs/03-follow-up-register/follow-up-register.md",
            "health-register": "Docs/04-health-register/health-register.md",
        },
    },
    "micro-p3-express": {
        "dirs": [
            "Docs/.p3flow",
            "Docs/01-common-understanding/diagrams",
            "Docs/02-follow-up-register",
            "Docs/cycles",
            "Docs/diagrams",
        ],
        "templates": {
            "micro-p3-express/common-understanding.md": "Docs/01-common-understanding/common-understanding.md",
            "micro-p3-express/follow-up-register.md": "Docs/02-follow-up-register/follow-up-register.md",
        },
        "first_activity": "A1",
        "documents": {
            "common-understanding": "Docs/01-common-understanding/common-understanding.md",
            "follow-up-register": "Docs/02-follow-up-register/follow-up-register.md",
        },
    },
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--methodology", required=True, choices=sorted(STRUCTURE))
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--root", default=".", help="корень репозитория проекта")
    args = ap.parse_args()

    cfg = STRUCTURE[args.methodology]
    root = Path(args.root).resolve()
    state_path = root / "Docs/.p3flow/state.yaml"
    if state_path.exists():
        print(f"ОШИБКА: {state_path} уже существует — проект уже инициализирован.", file=sys.stderr)
        return 1

    for d in cfg["dirs"]:
        (root / d).mkdir(parents=True, exist_ok=True)

    for src, dst in cfg["templates"].items():
        dst_path = root / dst
        if dst_path.exists():
            print(f"пропущен (уже есть): {dst}")
            continue
        text = (SKILL_DIR / "templates" / src).read_text(encoding="utf-8")
        dst_path.write_text(text.replace("{{PROJECT_NAME}}", args.project_name), encoding="utf-8")
        print(f"создан: {dst}")

    today = datetime.date.today().isoformat()
    doc_lines = "\n".join(
        f"  {name}: {{status: not_started, path: {path}}}"
        for name, path in cfg["documents"].items()
    )
    state_path.write_text(
        f"""methodology: {args.methodology}
project_name: "{args.project_name}"
started_at: {today}
current_group: A
current_activity: {cfg['first_activity']}
completed_activities: []
documents:
{doc_lines}
cycle_history: []
""",
        encoding="utf-8",
    )
    print(f"создан: {state_path.relative_to(root)}")
    print("Готово. Структура Docs/ инициализирована.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
