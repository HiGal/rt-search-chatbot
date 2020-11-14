from fastapi import FastAPI
import uvicorn
from routers import indexer

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == '__main__':
    app.include_router(indexer.router)
    uvicorn.run(app, host='0.0.0.0', port=8000)