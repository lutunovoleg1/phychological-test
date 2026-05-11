import os

import models
from database import SessionLocal, engine
from test_importer import create_test_from_data


def reset_database():
    if os.path.exists("app.db"):
        os.remove("app.db")
        print("Старая база app.db удалена.")

    models.Base.metadata.create_all(bind=engine)


TESTS = [
    {
        "code": "introvert_extrovert",
        "title": "Интроверт или Экстраверт?",
        "description": "Узнайте свой тип личности",
        "scales": [
            {"code": "total", "title": "Общий показатель"},
        ],
        "questions": [
            {
                "text": "Как вы отдыхаете?",
                "answers": [
                    {"code": "A", "text": "С книгой", "scores": {"total": 2}},
                    {"code": "B", "text": "В баре", "scores": {"total": 0}},
                    {"code": "C", "text": "С друзьями", "scores": {"total": 1}},
                ],
            },
            {
                "text": "Новые знакомства?",
                "answers": [
                    {"code": "A", "text": "Обожаю", "scores": {"total": 2}},
                    {"code": "B", "text": "Тяжело", "scores": {"total": 0}},
                    {"code": "C", "text": "Нормально", "scores": {"total": 1}},
                ],
            },
            {
                "text": "Ваша продуктивность?",
                "answers": [
                    {"code": "A", "text": "В тишине", "scores": {"total": 2}},
                    {"code": "B", "text": "В шуме", "scores": {"total": 0}},
                    {"code": "C", "text": "В общении", "scores": {"total": 1}},
                ],
            },
        ],
        "interpretations": [
            {"scale": "total", "min": 0, "max": 2, "text": "Вы - ярко выраженный интроверт."},
            {"scale": "total", "min": 3, "max": 4, "text": "Вы - амбиверт."},
            {"scale": "total", "min": 5, "max": 6, "text": "Вы - настоящий экстраверт!"},
        ],
    },
    {
        "code": "creator_analyst",
        "title": "Творец или Аналитик?",
        "description": "Определим ваши сильные стороны",
        "scales": [
            {"code": "creative", "title": "Творческое мышление"},
            {"code": "logic", "title": "Аналитическое мышление"},
        ],
        "questions": [
            {
                "text": "Что вам ближе?",
                "answers": [
                    {"code": "A", "text": "Рисование", "scores": {"creative": 2}},
                    {"code": "B", "text": "Математика", "scores": {"logic": 2}},
                ],
            },
            {
                "text": "Как решаете задачи?",
                "answers": [
                    {"code": "A", "text": "Интуитивно", "scores": {"creative": 2}},
                    {"code": "B", "text": "Алгоритмами", "scores": {"logic": 2}},
                ],
            },
            {
                "text": "Ваш идеал?",
                "answers": [
                    {"code": "A", "text": "Свобода", "scores": {"creative": 1}},
                    {"code": "B", "text": "Порядок", "scores": {"logic": 1}},
                ],
            },
        ],
        "interpretations": [
            {"scale": "creative", "min": 4, "max": 5, "text": "Вам ближе творческий подход."},
            {"scale": "logic", "min": 4, "max": 5, "text": "Вам ближе аналитический подход."},
            {"scale": "total", "min": 0, "max": 100, "text": "Посмотрите на баланс ваших навыков ниже."},
        ],
    },
]


if __name__ == "__main__":
    reset_database()
    db = SessionLocal()
    try:
        for test_data in TESTS:
            create_test_from_data(db, test_data)
    finally:
        db.close()

    print("База успешно пересоздана и наполнена!")
