import json

import numpy as np
from fastapi import APIRouter, HTTPException
import requests
from model import answer
from model import context as ctx
from utils import db_controller
from sklearn.metrics.pairwise import cosine_distances
import redis

router = APIRouter()

REDIS_HOST = "localhost"
REDIS_PORT = 6379


def query_analyzer(query_vector, doc_vecs):
    # score = np.sum(query_vector * doc_vecs, axis=1) / np.linalg.norm(doc_vecs, axis=1)
    score = cosine_distances(query_vector, doc_vecs)[0]
    topk_idx = np.argsort(score)[:10]
    return topk_idx, score[topk_idx]


@router.post("/bot/v1/question/{chat_id}", response_model=answer.Answer)
def question(body: dict, chat_id: str):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    text = str(body['question'])
    if r.exists(chat_id):
        print("We know you")  # TODO: we know you
        context = json.loads(r.get(chat_id).decode())
        if context["state"] == ctx.State.clarification:
            if context['type'] is None:
                if text in context['possible_types']:
                    context['type'] = text
                    context['possible_types'] = None
                    context['candidates'] = [candidate for candidate in context['candidates'] if
                                             candidate['type'] == text]
                    reqs = set({question["request"] for question in context["candidates"]})
                    print(list(reqs))
                    if len(reqs) > 1:
                        context["possible_requests"] = list(reqs)
                        response_body = {
                            "id": chat_id,
                            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
                            "answer": "Что Вас интересует?",
                            "options": list(reqs)
                        }
                        r.set(chat_id, json.dumps(context))
                        return response_body
                    clars = set({question["suggestion"] for question in context["candidates"]})
                    print(list(clars))
                    if len(clars) > 1:
                        context["possible_suggestions"] = list(clars)
                        response_body = {
                            "id": chat_id,
                            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
                            "answer": "Что Вас интересует?",
                            "options": list(clars)
                        }
                        r.set(chat_id, json.dumps(context))
                        return response_body
                    context["suggestion"] = list(clars)[0]
                    context["state"] = ctx.State.answered
                    context["attempt"] = 1
                    ans = context["candidates"][0]
                    context["candidates"] = context["candidates"][1:]
                    r.set(chat_id, json.dumps(context))
                    response_body = {
                        "id": chat_id,
                        "type": answer.AnswerType.final,
                        "answer": ans["answer"]
                    }
                    return response_body
                else:
                    raise HTTPException(status_code=400, detail="Not a type")
            elif context['request'] is None:
                if text in context['possible_requests']:
                    context['request'] = text
                    context['possible_requests'] = None
                    context['candidates'] = [candidate for candidate in context['candidates'] if
                                             candidate['request'] == text]
                    clars = set({question["suggestion"] for question in context["candidates"]})
                    print(list(clars))
                    if len(clars) > 1:
                        context["possible_suggestions"] = list(clars)
                        response_body = {
                            "id": chat_id,
                            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
                            "answer": "Что Вас интересует?",
                            "options": list(clars)
                        }
                        r.set(chat_id, json.dumps(context))
                        return response_body
                    context["suggestion"] = list(clars)[0]
                    context["state"] = ctx.State.answered
                    context["attempt"] = 1
                    ans = context["candidates"][0]
                    context["candidates"] = context["candidates"][1:]
                    r.set(chat_id, json.dumps(context))
                    response_body = {
                        "id": chat_id,
                        "type": answer.AnswerType.final,
                        "answer": ans['answer']
                    }
                    return response_body
                else:
                    raise HTTPException(status_code=400, detail="Not a request")
            else:
                if text in context['possible_suggestions']:
                    context['suggestion'] = text
                    context['possible_suggestions'] = None
                    context['candidates'] = [candidate for candidate in context['candidates'] if
                                             candidate['suggestion'] == text]
                    context["state"] = ctx.State.answered
                    context["attempt"] = 1
                    ans = context["candidates"][0]
                    context["candidates"] = context["candidates"][1:]
                    r.set(chat_id, json.dumps(context))
                    response_body = {
                        "id": chat_id,
                        "type": answer.AnswerType.final,
                        "answer": ans["answer"]
                    }
                    return response_body
                else:
                    raise HTTPException(status_code=400, detail="Not a suggestion")

    context = ctx.Context(
        state=ctx.State.clarification,
        original_question=text,
        attempt=0,
        candidates=list()
    )

    bert_body = {
        "id": chat_id,
        "texts": [text],
        "is_tokenized": False
    }
    query_vector = requests.post("http://127.0.0.1:8125/encode", json=bert_body).json()['result']
    # TODO: достать контекст
    # TODO: достать вектора документов из БД
    db_controller.cursor.execute("SELECT * FROM vectors ORDER BY index ASC")
    data = db_controller.cursor.fetchall()
    doc_vecs = np.array([row for _, row in data])
    topk_idx, scores = query_analyzer(query_vector, doc_vecs)

    for i in topk_idx:
        context.candidates.append(db_controller.get_question(i))

    if (scores[1] - scores[0]) > 0.01:
        response_body = {
            "id": chat_id,
            "type": answer.AnswerType.final,  # TODO: добавить логику запросов
            "answer": context.candidates.pop(0).answer,
            "options": None
        }
        context.attempt = 1
        context.state = ctx.State.answered
        r.set(chat_id, context.json())
        return response_body

    # r.set(chat_id, context.json())
    types = set({question.type for question in context.candidates})
    print(list(types))
    if len(types) > 1:
        context.possible_types = types
        response_body = {
            "id": chat_id,
            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
            "answer": "Что вас интересует?",
            "options": list(types)
        }
        r.set(chat_id, context.json())
        return response_body
    context.type = list(types)[0]
    # r.set(chat_id, context.json())
    ##################
    reqs = set({question.request for question in context.candidates})
    print(list(reqs))
    if len(reqs) > 1:
        context.possible_requests = reqs
        response_body = {
            "id": chat_id,
            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
            "answer": "Что Вас интересует?",
            "options": list(reqs)
        }
        r.set(chat_id, context.json())
        return response_body
    context.request = list(reqs)[0]
    # r.set(chat_id, context.json())
    #########################
    clars = set({question.suggestion for question in context.candidates})
    print(list(clars))
    if len(clars) > 1:
        context.possible_suggestions = clars
        response_body = {
            "id": chat_id,
            "type": answer.AnswerType.clarification,  # TODO: добавить логику запросов
            "answer": "Что Вас интересует?",
            "options": list(clars)
        }
        r.set(chat_id, context.json())
        return response_body
    context.suggestion = list(clars)[0]
    context.state = ctx.State.answered
    context.attempt = 1
    ans = context.candidates[0]
    context.candidates = context.candidates[1:]
    r.set(chat_id, context.json())
    response_body = {
        "id": chat_id,
        "type": answer.AnswerType.final,  # TODO: добавить логику запросов
        "answer": ans.answer,  # TODO: retrieve document by its id and put text here instead its index
        # TODO: логика с уточяющими вопросами
    }
    return response_body


# def clarification(context: ctx.Context):
#
#         #pass  # TODO: уточнить
#
#     print("Много типов")
#     return context


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
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    if not r.exists(chat_id):
        raise HTTPException(status_code=404, detail="Chat context not found")
    context = json.loads(r.get(chat_id).decode())
    if context['state'] != ctx.State.clarification:
        raise HTTPException(status_code=400, detail="You are not in the clarification state")
    res = {
        "id": chat_id,
        "type": answer.AnswerType.operator,
        "answer": "Передаем запрос оператору"
    }
    r.delete(chat_id)
    return res
