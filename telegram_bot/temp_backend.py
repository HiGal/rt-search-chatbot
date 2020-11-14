from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Optional
from enum import Enum

import random

from telegram_bot.bot import BAD_ANSWER, NEW_ANSWER, CALL_OPERATOR


class AnswerType(str, Enum):
    final = "final"
    clarification = "clarification"
    operator = "operator"


class Answer(BaseModel):
    id: str
    type: AnswerType
    answer: str
    options: Optional[list] = None


class MyRequest(BaseModel):
    question: str


app = FastAPI()


@app.post("/bot/v1/question/{chat_id}", response_model=Answer)
async def root(item: MyRequest):

    if item.question == "final":
        return {
            "id": "temp",
            "type": AnswerType.final,
            "answer": "поп поп поп поп поп поп поп поп поп поп поп поп",
            "options": None
        }
    elif item.question == "operator":
        return {
            "id": "temp",
            "type": AnswerType.operator,
            "answer": "поп поп поп поп поп поп поп поп поп поп поп поп",
            "options": None
        }
    elif item.question == "clarification":
        return {
            "id": "temp",
            "type": AnswerType.clarification,
            "answer": "Может поп поп поп поп поп поп поп поп поп поп поп поп?",
            "options": ["поп1", "поп2", "поп3"]
        }
    else:
        return random.choice([
            {
                "id": "temp",
                "type": AnswerType.clarification,
                "answer": item.question,
                "options": ["поп1", "поп2", "поп3"]
            },
            {
                "id": "temp",
                "type": AnswerType.operator,
                "answer": "поп поп поп поп поп поп поп поп поп поп поп поп",
                "options": None
            },
            {
                "id": "temp",
                "type": AnswerType.final,
                "answer": "поп поп поп поп поп поп поп поп поп поп поп поп",
                "options": None
            }
        ])


@app.get("/bot/v1/question/{chat_id}/incorrect", response_model=Answer)
async def root():
    a = {
        "id": "temp",
        "type": AnswerType.final,
        "answer": "response from incorrect"
    }
    return a


@app.get("/bot/v1/question/{chat_id}/cancel", response_model=Answer)
async def root():
    a = {
        "id": "temp",
        "type": AnswerType.final,
        "answer": "response from cancel"
    }
    return a


@app.get("/bot/v1/question/{chat_id}/operator", response_model=Answer)
async def root():
    a = {
        "id": "temp",
        "type": AnswerType.final,
        "answer": "response from cancel"
    }
    return a


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
