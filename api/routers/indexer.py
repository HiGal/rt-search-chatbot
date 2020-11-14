from fastapi import APIRouter
import requests
import pandas as pd
from utils import db_controller

router = APIRouter()


@router.get("/bot/v1/index/all")
async def index_all():
    db_controller.prep()
    db_controller.init()
    db_controller.cursor.execute('SELECT index, "Вопрос" FROM knowledge_base')
    questions = db_controller.cursor.fetchall()
    for question in questions:
        # print(row['Вопрос'])
        bert_body = {
            "id": question[0],
            "texts": [question[1]],
            "is_tokenized": False,
        }
        vector = requests.post("http://indexer:8125/encode", json=bert_body).json()['result']
        db_controller.cursor.execute("INSERT INTO vectors VALUES(%s, %s)", (question[0], vector[0]))
    db_controller.connection.commit()


@router.post("/bot/v1/index/new")
async def index_one(body: dict):
    db_controller.cursor.execute("SELECT index FROM knowledge_base ORDER BY index DESC LIMIT 1")
    max_index = int(db_controller.cursor.fetchone()[0])
    db_controller.cursor.execute("INSERT INTO knowledge_base VALUES(%s, %s, %s, %s, %s, %s)", (max_index + 1,
                                                                                               body['request'],
                                                                                               body['clarification'],
                                                                                               body['category'],
                                                                                               body['question'],
                                                                                               body['answer']))
    db_controller.connection.commit()
    id = 1
    is_tokenized = False
    bert_body = {
        "id": id,
        "texts": [body["question"]],
        "is_tokenized": is_tokenized
    }
    r = requests.post("http://indexer:8125/encode", json=bert_body)
    if r.status_code == 200:
        vector = r.json()['result']
        db_controller.cursor.execute("INSERT INTO vectors VALUES(%s, %s)", (max_index + 1, [0]))
        return {"vector": vector}
    return r.raise_for_status()
