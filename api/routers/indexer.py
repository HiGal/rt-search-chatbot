from fastapi import APIRouter
import requests
import pandas as pd

router = APIRouter()


@router.get("/bot/v1/index/all")
def index_all():
    df = pd.read_csv("../data/KB.csv")
    for index, row in df.iterrows():
        print(row.index)
        bert_body = {
            "id": 0,
            "texts": [[row['Вопрос']]],
            "is_tokenized": True,
        }
        vector = requests.post("http://127.0.0.1:8125/encode", json=bert_body).json()['result']
        # TODO: Добавление в БД
        break
    pass


@router.post("/bot/v1/index/new")
async def index_one(body: dict):
    id = 1
    is_tokenized = True
    bert_body = {
        "id": id,
        "texts": [[body["question"]]],
        "is_tokenized": is_tokenized
    }
    r = requests.post("http://127.0.0.1:8125/encode", json=bert_body)
    if r.status_code == 200:
        vector = r.json()['result']
        # TODO: Добавление в БД
        return {"vector": vector}
    return r.raise_for_status()
