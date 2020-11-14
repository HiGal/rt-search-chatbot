import numpy as np
from fastapi import APIRouter
import requests
from model import answer

router = APIRouter()

def query_analyzer(query_vector, doc_vecs):
    score = np.sum(query_vector * doc_vecs, axis=1) / np.linalg.norm(doc_vecs, axis=1)
    topk_idx = np.argsort(score)[::-1][:10]
    return topk_idx

@router.post("/bot/v1/question/{chat_id}", response_model=answer.Answer)
async def question(body: dict, chat_id: str):
    bert_body = {
        "id": chat_id,
        "texts": [[body['question']]],
        "is_tokenized": True
    }
    query_vector = requests.post("http://127.0.0.1:8125/encode", json=bert_body).json()['result']
    # TODO: достать контекст
    # TODO: достать вектора документов из БД
    doc_vecs = np.random.randn(50, 768)
    topk_idx = query_analyzer(query_vector, doc_vecs)
    response_body = {
        "id": chat_id,
        "type": answer.AnswerType.final, # TODO: добавить логику запросов
        "answer": str(topk_idx[0]), # TODO: retrieve document by its id and put text here instead its index
        # TODO: логика с уточяющими вопросами
    }
    return response_body

@router.get("/bot/v1/question/{chat_id}/incorrect", response_model=answer.Answer)
def incorrect_answer():
    # TODO: Достать контекст
    # TODO: Проверить что в нужном стейте
    # TODO: Вернуть след вопрос
    pass

@router.get("/bot/v1/question/{chat_id}/cancel")
def cancel_question():
    # TODO: Проверить что контекст есть
    # TODO: Удалить из контекста запись
    pass

@router.get("/bot/v1/question/{chat_id}/operator")
def operator():
    # TODO: Проверить что контекст есть
    # TODO: Сформировать ответ с AnswerType.operator
    # TODO: Удалить из контекста запись
    pass