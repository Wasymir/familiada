import asyncio
from typing import Annotated

from fastapi import FastAPI, WebSocket, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed

from database import DataBase, Question, Answer

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pages", StaticFiles(directory="page"), name="page")


class Hub:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    async def broadcast(self, msg):
        for connection in self.connections:
            try:
                await connection.send_json(msg)
            except ConnectionClosed:
                print("Broken chanel")
                continue


hub = Hub()


@app.websocket("/ws/")
async def counter(ws: WebSocket):
    await hub.connect(ws)
    while True:
        await asyncio.sleep(0.5)


@app.post("/send/")
async def update(target: str, query: str):
    await hub.broadcast({"target": target, "query": query})


db = DataBase()

@app.get("/questions/")
async def get_questions():
    return db.get_questions()


@app.delete("/questions/", status_code=204)
async def remove_question(id: int):
    db.remove_question(id)


@app.get("/answers/")
async def get_answers(id: int):
    return db.get_answers(id)


@app.put("/answers/")
async def update_answers(id: int, answers: Annotated[list[Answer], Body()]):
    db.update_answers(id, answers)


@app.post("/questions/", status_code=200)
async def new_question(question: Question):
    db.add_question(question)

