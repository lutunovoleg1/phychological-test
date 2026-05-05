from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
import json




class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    # Новая колонка для хранения логики результатов
    interpretations_json = Column(String, default="[]") 
    questions = relationship("Question", back_populates="test")

    @property
    def interpretations(self):
        return json.loads(self.interpretations_json)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    text = Column(String)
    test = relationship("Test", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(String)
    score = Column(Integer)
    scale = Column(String, default="total") # Название шкалы: "extraversion", "logic" и т.д.
    question = relationship("Question", back_populates="answers")

class UserResult(Base):
    __tablename__ = "user_results"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    test_id = Column(Integer, ForeignKey("tests.id"))
    score = Column(Integer)
    result_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Добавьте это, чтобы главная страница могла подтянуть название теста
    test = relationship("Test") 
