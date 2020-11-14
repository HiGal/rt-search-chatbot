import numpy as np
from fastapi import APIRouter,  HTTPException
import requests
from model import answer
from model import context as ctx
from utils import db_controller
from sklearn.metrics.pairwise import cosine_distances
import redis


router = APIRouter()

def query_analyzer(query_vector, doc_vecs):
    # score = np.sum(query_vector * doc_vecs, axis=1) / np.linalg.norm(doc_vecs, axis=1)
    score = cosine_distances(query_vector, doc_vecs)[0]
    topk_idx = np.argsort(score)[:3]
    print(topk_idx)
    return topk_idx

@router.post("/bot/v1/question/{chat_id}", response_model=answer.Answer)
async def question(body: dict, chat_id: str):
    text = str(body['question'])
    bert_body = {
        "id": chat_id,
        "texts": [text],
        "is_tokenized": False
    }
    query_vector = requests.post("http://indexer:8125/encode", json=bert_body).json()['result']
    # TODO: достать контекст
    # TODO: достать вектора документов из БД
    db_controller.cursor.execute("SELECT * FROM vectors ORDER BY index ASC")
    data = db_controller.cursor.fetchall()
    doc_vecs = np.array([row for _, row in data])
    topk_idx = query_analyzer(query_vector, doc_vecs)

    db_controller.cursor.execute(f'SELECT "Ответ" FROM knowledge_base WHERE index = {topk_idx[0]}')
    answer_text = db_controller.cursor.fetchall()
    response_body = {
        "id": chat_id,
        "type": answer.AnswerType.final, # TODO: добавить логику запросов
        "answer": str(answer_text[0]), # TODO: retrieve document by its id and put text here instead its index
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

@router.get("/bot/v1/question/{chat_id}/operator", response_model=answer.Answer)
def operator(chat_id: str):
    r = redis.Redis(host='hostname', port=port, password='password')
    if (not r.contains(chat_id)):
        raise HTTPException(status_code=404, detail="Chat context not found")
    context = r.get(chat_id)
    if (context.state != ctx.State.clarification):
        raise HTTPException(status_code=400, detail="You are not in the clarification state")        
    # TODO: Сформировать ответ с AnswerType.operator
    # TODO: записать context в неизвестные
    r.remove(chat_id)