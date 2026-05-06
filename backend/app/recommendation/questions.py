QUESTIONS: dict[str, list[dict]] = {
    "mouse": [
        {
            "id": "use_case",
            "text": "Для чего используете мышь?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Для игр"},
                {"value": "office", "label": "Для работы"},
                {"value": "both", "label": "Для всего"},
            ],
        },
        {
            "id": "wireless",
            "text": "Нужна беспроводная?",
            "type": "choice",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no", "label": "Нет, проводная"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 3000",
        },
    ],
    "keyboard": [
        {
            "id": "use_case",
            "text": "Для чего используете клавиатуру?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Для игр"},
                {"value": "typing", "label": "Для печати"},
                {"value": "both", "label": "Для всего"},
            ],
        },
        {
            "id": "form_factor",
            "text": "Форм-фактор?",
            "type": "choice",
            "options": [
                {"value": "full", "label": "Полноразмерная (Full)"},
                {"value": "tkl", "label": "Без цифрового блока (TKL)"},
                {"value": "compact", "label": "Компактная (60–75%)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "switches",
            "text": "Тип переключателей?",
            "type": "choice",
            "options": [
                {"value": "linear", "label": "Линейные (тихие, плавные)"},
                {"value": "tactile", "label": "Тактильные (с ощущением клика)"},
                {"value": "clicky", "label": "Кликающие (громкие)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 5000",
        },
    ],
    "monitor": [
        {
            "id": "use_case",
            "text": "Основное использование?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Игры"},
                {"value": "work", "label": "Работа и учёба"},
                {"value": "both", "label": "Всё понемногу"},
            ],
        },
        {
            "id": "size",
            "text": "Размер экрана?",
            "type": "choice",
            "options": [
                {"value": "small", "label": "До 24\""},
                {"value": "medium", "label": "24–27\""},
                {"value": "large", "label": "27\" и больше"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 20000",
        },
    ],
}

SUPPORTED_CATEGORIES: set[str] = set(QUESTIONS.keys())


def get_questions(category: str) -> list[dict] | None:
    return QUESTIONS.get(category)
