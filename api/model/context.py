from pydantic import BaseModel
from typing import Optional
from enum import Enum

class State(str, Enum):
    clarification = "clarification"

class Question(BaseModel):
    question: str
    answer: str
    type: str
    request: str
    suggestion: str
    distanse: float

class Context(BaseModel):
    state: State
    original_question: str
    attempt: int
    candidates: list # here questions
    type: Optional[str] = None
    request: Optional[str] = None
    suggestion: Optional[str] = None


