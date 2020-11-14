from fastapi import FastAPI
import question_handler

app = FastAPI()
app.include_router(question_handler.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
