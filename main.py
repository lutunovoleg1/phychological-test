import json
from datetime import datetime

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_scores(db: Session, session: models.TestSession) -> dict[str, int]:
    scores = {scale.code: 0 for scale in session.test.scales}

    for user_answer in session.answers:
        rules = (
            db.query(models.ScoringRule)
            .filter(
                models.ScoringRule.question_id == user_answer.question_id,
                models.ScoringRule.answer_code == user_answer.answer_code,
            )
            .all()
        )
        for rule in rules:
            scores[rule.scale.code] = scores.get(rule.scale.code, 0) + rule.points

    return scores


def select_interpretation(test: models.Test, scores: dict[str, int]) -> str:
    total_score = sum(scores.values())

    for rule in test.interpretation_rules:
        value = total_score if rule.scale_code == "total" else scores.get(rule.scale_code, 0)
        if rule.min_score <= value <= rule.max_score:
            return rule.text

    return "Тест пройден успешно."


def finish_session(db: Session, session: models.TestSession) -> models.UserResult:
    existing_result = (
        db.query(models.UserResult)
        .filter(models.UserResult.session_id == session.id)
        .first()
    )
    if existing_result:
        return existing_result

    scores = calculate_scores(db, session)
    total_score = sum(scores.values())
    result_text = select_interpretation(session.test, scores)

    session.status = "completed"
    session.completed_at = datetime.utcnow()

    result = models.UserResult(
        username=session.username,
        test_id=session.test_id,
        session_id=session.id,
        score=total_score,
        scores_json=json.dumps(scores, ensure_ascii=False),
        result_text=result_text,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    tests = db.query(models.Test).all()
    history = (
        db.query(models.UserResult)
        .order_by(models.UserResult.created_at.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"tests": tests, "history": history},
    )


@app.get("/test/{test_id}", response_class=HTMLResponse)
async def run_test(
    request: Request,
    test_id: int,
    username: str | None = None,
    session_id: int | None = None,
    db: Session = Depends(get_db),
):
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        return HTMLResponse(content="Тест не найден", status_code=404)

    if not username and not session_id:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"test_id": test_id},
        )

    if session_id:
        session = (
            db.query(models.TestSession)
            .filter(
                models.TestSession.id == session_id,
                models.TestSession.test_id == test_id,
            )
            .first()
        )
        if not session:
            return HTMLResponse(content="Сессия теста не найдена", status_code=404)
    else:
        session = models.TestSession(username=username, test_id=test_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        return RedirectResponse(
            url=f"/test/{test_id}?session_id={session.id}",
            status_code=303,
        )

    questions = test.questions
    answered_count = len(session.answers)

    if answered_count >= len(questions):
        result = finish_session(db, session)
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "test": test,
                "username": session.username,
                "scores": result.scores,
                "score": result.score,
                "result_text": result.result_text,
            },
        )

    current_question = questions[answered_count]

    return templates.TemplateResponse(
        request=request,
        name="test.html",
        context={
            "test": test,
            "question": current_question,
            "question_number": answered_count + 1,
            "questions_count": len(questions),
            "session_id": session.id,
            "can_go_back": answered_count > 0,
        },
    )


@app.post("/test/{test_id}/answer")
async def submit_answer(
    test_id: int,
    session_id: int = Form(...),
    answer_code: str = Form(...),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.TestSession)
        .filter(
            models.TestSession.id == session_id,
            models.TestSession.test_id == test_id,
            models.TestSession.status == "in_progress",
        )
        .first()
    )
    if not session:
        return HTMLResponse(content="Активная сессия теста не найдена", status_code=404)

    questions = session.test.questions
    answered_count = len(session.answers)
    if answered_count >= len(questions):
        return RedirectResponse(url=f"/test/{test_id}?session_id={session.id}", status_code=303)

    question = questions[answered_count]
    allowed_codes = {answer.code for answer in question.answer_options}
    if answer_code not in allowed_codes:
        return HTMLResponse(content="Недопустимый код ответа", status_code=400)

    db.add(
        models.UserAnswer(
            session_id=session.id,
            question_id=question.id,
            answer_code=answer_code,
        )
    )
    db.commit()

    return RedirectResponse(url=f"/test/{test_id}?session_id={session.id}", status_code=303)


@app.post("/test/{test_id}/back")
async def go_back(
    test_id: int,
    session_id: int = Form(...),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.TestSession)
        .filter(
            models.TestSession.id == session_id,
            models.TestSession.test_id == test_id,
            models.TestSession.status == "in_progress",
        )
        .first()
    )
    if not session:
        return HTMLResponse(content="Активная сессия теста не найдена", status_code=404)

    last_answer = session.answers[-1] if session.answers else None
    if last_answer:
        db.delete(last_answer)
        db.commit()

    return RedirectResponse(url=f"/test/{test_id}?session_id={session.id}", status_code=303)
