from pydantic import BaseModel
from typing import Optional
from enum import Enum

class AnswerType(str, Enum):
    final = "final"
    clarification = "clarification"
    operator = "operator"

class Answer(BaseModel):
    id: str
    type: AnswerType
    answer: str
    options: Optional[list] = None