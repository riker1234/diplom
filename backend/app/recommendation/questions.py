_PRIORITY_QUESTION = {
    "id": "priority",
    "text": "Что важнее при выборе?",
    "type": "choice",
    "options": [
        {"value": "budget", "label": "Цена — главное, хочу сэкономить"},
        {"value": "balance", "label": "Баланс цены и качества"},
        {"value": "flagship", "label": "Только лучшее в своём классе"},
    ],
}

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
        _PRIORITY_QUESTION,
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
                {"value": "full", "label": "Полноразмерная — с цифровым блоком (100%)"},
                {"value": "tkl", "label": "TKL — без цифрового блока, все F-клавиши (80%)"},
                {"value": "compact", "label": "Компактная — без F-ряда или части клавиш (60–75%)"},
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
                {"value": "magnetic", "label": "Магнитные (Hall Effect)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        _PRIORITY_QUESTION,
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
        _PRIORITY_QUESTION,
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 20000",
        },
    ],
    "headphones": [
        {
            "id": "use_case",
            "text": "Для чего нужны наушники?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Для игр"},
                {"value": "music", "label": "Для музыки"},
                {"value": "calls", "label": "Для звонков и работы"},
                {"value": "any", "label": "Универсальные"},
            ],
        },
        {
            "id": "construction_type",
            "text": "Тип конструкции?",
            "type": "choice",
            "options": [
                {"value": "fullsize", "label": "Полноразмерные / накладные (over-ear)"},
                {"value": "earbuds", "label": "Вкладыши / внутриканальные (in-ear)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "connection",
            "text": "Тип подключения?",
            "type": "choice",
            "options": [
                {"value": "wired", "label": "Проводные"},
                {"value": "wireless", "label": "Беспроводные (Bluetooth)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        _PRIORITY_QUESTION,
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 5000",
        },
    ],
    "microphone": [
        {
            "id": "use_case",
            "text": "Для чего нужен микрофон?",
            "type": "choice",
            "options": [
                {"value": "streaming", "label": "Стриминг и подкасты"},
                {"value": "calls", "label": "Звонки и конференции"},
                {"value": "recording", "label": "Запись голоса и музыки"},
                {"value": "any", "label": "Универсальный"},
            ],
        },
        {
            "id": "connection",
            "text": "Тип подключения?",
            "type": "choice",
            "options": [
                {"value": "usb", "label": "USB (plug & play)"},
                {"value": "xlr", "label": "XLR (профессиональный)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        _PRIORITY_QUESTION,
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 8000",
        },
    ],
    "mousepad": [
        {
            "id": "size",
            "text": "Нужный размер коврика?",
            "type": "choice",
            "options": [
                {"value": "small", "label": "Маленький (до 350 мм)"},
                {"value": "large", "label": "Большой (350 мм и больше)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "hardness",
            "text": "Жёсткость поверхности?",
            "type": "choice",
            "options": [
                {"value": "soft", "label": "Мягкий (ткань)"},
                {"value": "hard", "label": "Жёсткий (пластик/стекло)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "rgb",
            "text": "Нужна RGB-подсветка?",
            "type": "choice",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no", "label": "Нет"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        _PRIORITY_QUESTION,
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 2000",
        },
    ],
}

SUPPORTED_CATEGORIES: set[str] = set(QUESTIONS.keys())


def get_questions(category: str) -> list[dict] | None:
    return QUESTIONS.get(category)
