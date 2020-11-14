from pydantic import BaseModel
from typing import Optional
from enum import Enum

class State(str, Enum):
    clarification = "clarification"
    answered = "answered"

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
    possible_types: Optional[list] = None
    possible_requests: Optional[list] = None
    possible_suggestions: Optional[list] = None
    request: Optional[str] = None
    suggestion: Optional[str] = None


