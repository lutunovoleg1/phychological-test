import os
import json
import models
from database import SessionLocal, engine

# 1. Физическое удаление старой базы
if os.path.exists("app.db"):
    os.remove("app.db")
    print("Старая база app.db удалена.")

# 2. Создание таблиц с нуля
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- ТЕСТ 1: ТЕМПЕРАМЕНТ ---
rules_temp = [
    {"min": 0, "max": 2, "text": "Вы — ярко выраженный интроверт."},
    {"min": 3, "max": 4, "text": "Вы — амбиверт."},
    {"min": 5, "max": 6, "text": "Вы — настоящий экстраверт!"}
]

test1 = models.Test(
    title="Интроверт или Экстраверт?",
    description="Узнайте свой тип личности",
    interpretations_json=json.dumps(rules_temp)
)
db.add(test1)
db.commit()

q_data1 = [
    ("Как вы отдыхаете?", [("С книгой", 2, "total"), ("В баре", 0, "total"), ("С друзьями", 1, "total")]),
    ("Новые знакомства?", [("Обожаю", 2, "total"), ("Тяжело", 0, "total"), ("Нормально", 1, "total")]),
    ("Ваша продуктивность?", [("В тишине", 2, "total"), ("В шуме", 0, "total"), ("В общении", 1, "total")])
]

for text, answers in q_data1:
    q = models.Question(text=text, test_id=test1.id)
    db.add(q)
    db.commit()
    db.refresh(q)
    for a_text, a_score, a_scale in answers:
        db.add(models.Answer(text=a_text, score=a_score, scale=a_scale, question_id=q.id))

# --- ТЕСТ 2: ПРОФОРИЕНТАЦИЯ (две шкалы) ---
rules_career = [
    {"min": 0, "max": 100, "text": "Посмотрите на баланс ваших навыков ниже:"}
]

test2 = models.Test(
    title="Творец или Аналитик?",
    description="Определим ваши сильные стороны",
    interpretations_json=json.dumps(rules_career)
)
db.add(test2)
db.commit()

q_data2 = [
    ("Что вам ближе?", [("Рисование", 2, "creative"), ("Математика", 2, "logic")]),
    ("Как решаете задачи?", [("Интуитивно", 2, "creative"), ("Алгоритмами", 2, "logic")]),
    ("Ваш идеал?", [("Свобода", 1, "creative"), ("Порядок", 1, "logic")])
]

for text, answers in q_data2:
    q = models.Question(text=text, test_id=test2.id)
    db.add(q)
    db.commit()
    db.refresh(q)
    for a_text, a_score, a_scale in answers:
        db.add(models.Answer(text=a_text, score=a_score, scale=a_scale, question_id=q.id))

db.commit()
db.close()
print("База успешно пересоздана и наполнена!")
