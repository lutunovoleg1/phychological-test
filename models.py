from datetime import datetime
import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String)

    questions = relationship("Question", back_populates="test", order_by="Question.position")
    scales = relationship("Scale", back_populates="test", order_by="Scale.position")
    interpretation_rules = relationship(
        "InterpretationRule",
        back_populates="test",
        order_by="InterpretationRule.position",
    )


class Scale(Base):
    __tablename__ = "scales"
    __table_args__ = (UniqueConstraint("test_id", "code", name="uq_scale_test_code"),)

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    code = Column(String, index=True)
    title = Column(String)
    position = Column(Integer, default=0)

    test = relationship("Test", back_populates="scales")
    scoring_rules = relationship("ScoringRule", back_populates="scale")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    text = Column(String)
    position = Column(Integer, default=0)

    test = relationship("Test", back_populates="questions")
    answer_options = relationship(
        "AnswerOption",
        back_populates="question",
        order_by="AnswerOption.position",
    )
    scoring_rules = relationship("ScoringRule", back_populates="question")


class AnswerOption(Base):
    __tablename__ = "answer_options"
    __table_args__ = (UniqueConstraint("question_id", "code", name="uq_answer_question_code"),)

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    code = Column(String, index=True)
    text = Column(String)
    position = Column(Integer, default=0)

    question = relationship("Question", back_populates="answer_options")


class ScoringRule(Base):
    __tablename__ = "scoring_rules"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "answer_code",
            "scale_id",
            name="uq_scoring_question_answer_scale",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_code = Column(String, index=True)
    scale_id = Column(Integer, ForeignKey("scales.id"))
    points = Column(Integer, default=0)

    question = relationship("Question", back_populates="scoring_rules")
    scale = relationship("Scale", back_populates="scoring_rules")


class InterpretationRule(Base):
    __tablename__ = "interpretation_rules"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    scale_code = Column(String, default="total")
    min_score = Column(Integer)
    max_score = Column(Integer)
    text = Column(String)
    position = Column(Integer, default=0)

    test = relationship("Test", back_populates="interpretation_rules")


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    test_id = Column(Integer, ForeignKey("tests.id"))
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    test = relationship("Test")
    answers = relationship(
        "UserAnswer",
        back_populates="session",
        order_by="UserAnswer.created_at",
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"
    __table_args__ = (UniqueConstraint("session_id", "question_id", name="uq_answer_session_question"),)

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TestSession", back_populates="answers")
    question = relationship("Question")


class UserResult(Base):
    __tablename__ = "user_results"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    test_id = Column(Integer, ForeignKey("tests.id"))
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=True)
    score = Column(Integer)
    scores_json = Column(String, default="{}")
    result_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test")
    session = relationship("TestSession")

    @property
    def scores(self):
        return json.loads(self.scores_json or "{}")
