import random
from sqlalchemy.orm import Session
from app.recommendation.engine import recommend

# Веса распределения бюджета по категориям для каждого сценария использования
_WEIGHTS: dict[str, dict[str, float]] = {
    "gaming": {
        "monitor":    0.30,
        "keyboard":   0.22,
        "mouse":      0.22,
        "headphones": 0.16,
        "mousepad":   0.10,
    },
    "work": {
        "monitor":    0.38,
        "keyboard":   0.28,
        "mouse":      0.18,
        "headphones": 0.11,
        "mousepad":   0.05,
    },
    "both": {
        "monitor":    0.32,
        "keyboard":   0.24,
        "mouse":      0.20,
        "headphones": 0.14,
        "mousepad":   0.10,
    },
}

# Минимальный бюджет на категорию (ниже этого не имеет смысла искать)
_MIN_BUDGET: dict[str, float] = {
    "monitor":    5000.0,
    "keyboard":   1000.0,
    "mouse":       700.0,
    "headphones":  800.0,
    "mousepad":    300.0,
}

# Базовые ответы для каждого сценария (чтобы рекомендации были осмысленными)
_BASE_ANSWERS: dict[str, dict[str, str]] = {
    "gaming": {
        "use_case": "gaming",
        "wireless": "any",
        "form_factor": "any",
        "switches": "any",
        "construction_type": "any",
        "connection": "any",
        "size": "any",
        "hardness": "any",
        "rgb": "any",
        "priority": "balance",
    },
    "work": {
        "use_case": "work",
        "wireless": "any",
        "form_factor": "any",
        "switches": "any",
        "construction_type": "any",
        "connection": "any",
        "size": "any",
        "hardness": "any",
        "rgb": "no",
        "priority": "balance",
    },
    "both": {
        "use_case": "both",
        "wireless": "any",
        "form_factor": "any",
        "switches": "any",
        "construction_type": "any",
        "connection": "any",
        "size": "any",
        "hardness": "any",
        "rgb": "any",
        "priority": "balance",
    },
}

CATEGORIES = ["monitor", "keyboard", "mouse", "headphones", "mousepad"]


def recommend_setup(
    total_budget: float,
    use_case: str,
    priority: str,
    db: Session,
) -> dict:
    """
    Распределяет бюджет по категориям и возвращает оптимальный комплект.

    Алгоритм:
    1. Считаем бюджет на каждую категорию по весам.
    2. Для каждой категории запускаем recommend(), берём топ-1.
    3. Если категория не даёт результатов — исключаем её и перераспределяем
       её бюджет пропорционально оставшимся.
    4. Возвращаем итоговый набор с реальными ценами и остатком бюджета.
    """
    weights = dict(_WEIGHTS.get(use_case, _WEIGHTS["both"]))
    base_answers = dict(_BASE_ANSWERS.get(use_case, _BASE_ANSWERS["both"]))
    base_answers["priority"] = priority

    # Шаг 1: первичное распределение
    allocations = {cat: total_budget * w for cat, w in weights.items()}

    result: dict[str, dict] = {}
    failed: list[str] = []

    # Шаг 2: пытаемся найти товар в каждой категории
    for cat in CATEGORIES:
        budget = allocations[cat]
        if budget < _MIN_BUDGET.get(cat, 0):
            failed.append(cat)
            continue

        answers = {**base_answers, "budget": budget}
        items = recommend(cat, answers, db)

        if items:
            result[cat] = random.choice(items[:3])
        else:
            failed.append(cat)

    # Шаг 3: перераспределяем бюджет от провалившихся категорий
    if failed:
        freed = sum(allocations[cat] for cat in failed)
        remaining_cats = [c for c in CATEGORIES if c not in failed and c not in result]

        if remaining_cats and freed > 0:
            extra_per_cat = freed / len(remaining_cats)
            for cat in remaining_cats:
                allocations[cat] += extra_per_cat
                answers = {**base_answers, "budget": allocations[cat]}
                items = recommend(cat, answers, db)
                if items:
                    result[cat] = random.choice(items[:3])

    # Шаг 4: считаем итоговую стоимость
    total_price = 0.0
    for cat, item in result.items():
        best = item.get("best_price") or 0
        total_price += best

    return {
        "use_case": use_case,
        "total_budget": total_budget,
        "total_price": round(total_price, 2),
        "remaining": round(total_budget - total_price, 2),
        "allocations": {cat: round(v, 2) for cat, v in allocations.items()},
        "items": result,
    }
