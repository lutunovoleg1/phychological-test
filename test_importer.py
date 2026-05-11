import models


class TestImportError(ValueError):
    pass


def validate_test_data(data):
    required_fields = ["code", "title", "description", "scales", "questions", "interpretations"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise TestImportError(f"Не хватает полей теста: {', '.join(missing_fields)}")

    scale_codes = {scale["code"] for scale in data["scales"]}
    if not scale_codes:
        raise TestImportError("У теста должна быть хотя бы одна шкала")

    for question_index, question in enumerate(data["questions"], start=1):
        if "text" not in question or "answers" not in question:
            raise TestImportError(f"Вопрос {question_index}: нужны поля text и answers")

        answer_codes = set()
        for answer in question["answers"]:
            answer_code = answer.get("code")
            if not answer_code:
                raise TestImportError(f"Вопрос {question_index}: у ответа нет code")
            if answer_code in answer_codes:
                raise TestImportError(f"Вопрос {question_index}: код ответа {answer_code} повторяется")
            answer_codes.add(answer_code)

            for scale_code in answer.get("scores", {}):
                if scale_code not in scale_codes:
                    raise TestImportError(
                        f"Вопрос {question_index}, ответ {answer_code}: неизвестная шкала {scale_code}"
                    )


def create_test_from_data(db, data):
    validate_test_data(data)

    test = models.Test(
        code=data["code"],
        title=data["title"],
        description=data["description"],
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    scales_by_code = {}
    for position, scale_data in enumerate(data["scales"], start=1):
        scale = models.Scale(
            test_id=test.id,
            code=scale_data["code"],
            title=scale_data["title"],
            position=position,
        )
        db.add(scale)
        db.commit()
        db.refresh(scale)
        scales_by_code[scale.code] = scale

    for question_position, question_data in enumerate(data["questions"], start=1):
        question = models.Question(
            test_id=test.id,
            text=question_data["text"],
            position=question_position,
        )
        db.add(question)
        db.commit()
        db.refresh(question)

        for answer_position, answer_data in enumerate(question_data["answers"], start=1):
            db.add(
                models.AnswerOption(
                    question_id=question.id,
                    code=answer_data["code"],
                    text=answer_data["text"],
                    position=answer_position,
                )
            )

            for scale_code, points in answer_data.get("scores", {}).items():
                db.add(
                    models.ScoringRule(
                        question_id=question.id,
                        answer_code=answer_data["code"],
                        scale_id=scales_by_code[scale_code].id,
                        points=points,
                    )
                )

    for position, rule_data in enumerate(data["interpretations"], start=1):
        db.add(
            models.InterpretationRule(
                test_id=test.id,
                scale_code=rule_data.get("scale", "total"),
                min_score=rule_data["min"],
                max_score=rule_data["max"],
                text=rule_data["text"],
                position=position,
            )
        )

    db.commit()
    return test
