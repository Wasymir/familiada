import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed

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
        await asyncio.sleep(1)


@app.post("/send/")
async def update(target: str, query: str):
    await hub.broadcast({"target": target, "query": query})
    return


