from fastapi import APIRouter

router = APIRouter()


@router.post("/bot/v1/question")
async def get_question(body: dict):
    try:
        question = body["question"]
    except KeyError as e:
        status = "BAD REQUEST"
        answer = ""
        response = {"status": status, "answer": answer}
        return response
    status = "OK"
    answer = "cock"
    response = {"status": status, "answer": answer}
    return response
