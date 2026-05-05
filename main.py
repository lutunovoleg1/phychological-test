import json
from urllib.parse import unquote
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine

# Автоматическое создание таблиц при запуске
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключение статических файлов (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение шаблонов HTML
templates = Jinja2Templates(directory="templates")

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Загружаем тесты и последние 10 результатов для истории
    tests = db.query(models.Test).all()
    history = db.query(models.UserResult).order_by(models.UserResult.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"tests": tests, "history": history}
    )

@app.get("/test/{test_id}", response_class=HTMLResponse)
async def run_test(
    request: Request, 
    test_id: int, 
    username: str = None, 
    q_index: int = 0, 
    scores_json: str = "{}", 
    db: Session = Depends(get_db)
):
    # ЛОГ: Начало обработки запроса
    print(f"\n[DEBUG] Запрос: Test ID={test_id}, User={username}, Q_Index={q_index}")

    # 1. Если имя пользователя не введено, показываем форму входа
    if not username:
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"test_id": test_id}
        )

    # Загружаем тест и вопросы из БД
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        print("[ERROR] Тест не найден!")
        return HTMLResponse(content="Тест не найден", status_code=404)
        
    questions = test.questions
    scores = json.loads(unquote(scores_json))

    # 2. ПРОВЕРКА ФИНАЛА: Если индекс вопроса равен или больше общего кол-ва вопросов
    if q_index >= len(questions):
        print(f"[DEBUG] Финал достигнут для {username}. Расчет результатов...")
        
        # Считаем общую сумму баллов по всем шкалам
        total_score = sum(scores.values())
        
        # Определяем текст интерпретации на основе правил из БД
        result_text = "Тест пройден успешно."
        for rule in test.interpretations:
            if rule['min'] <= total_score <= rule['max']:
                result_text = rule['text']
                break
        
        # СОХРАНЕНИЕ В БАЗУ ДАННЫХ
        try:
            new_record = models.UserResult(
                username=username,
                test_id=test_id,
                score=total_score,
                result_text=result_text
            )
            db.add(new_record)
            db.commit()
            print(f"[SUCCESS] Результат сохранен в БД: {total_score} баллов")
        except Exception as e:
            db.rollback()
            print(f"[CRITICAL ERROR] Ошибка при сохранении в БД: {e}")

        return templates.TemplateResponse(
            request=request, 
            name="result.html", 
            context={
                "test": test,
                "username": username,
                "scores": scores,
                "score": total_score,
                "result_text": result_text
            }
        )

    # 3. ОТОБРАЖЕНИЕ ТЕКУЩЕГО ВОПРОСА
    current_question = questions[q_index]
    print(f"[DEBUG] Отображение вопроса {q_index + 1}: {current_question.text}")
    
    return templates.TemplateResponse(
        request=request, 
        name="test.html", 
        context={
            "test": test,
            "question": current_question,
            "q_index": q_index,
            "scores_json": scores_json,
            "username": username,
            "can_go_back": q_index > 0
        }
    )
