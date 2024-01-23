from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import RedirectResponse
import json
import asyncio
from typing import Dict, List, Tuple
from api.lib.stablehorde import generate_async, generate_status

from api.schema import game as Game

import random

import string

router = APIRouter(
    prefix="/game",
    tags=["game"],
    responses={404: {"description": "Not found"}},
)

@router.get("/new", response_model=Game.NewGame)
async def new_game():
    game_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    return RedirectResponse(f"http://localhost:3000/game?id={game_id}")

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def validate_game_id(self, game_id: str) -> bool:
        # Add validation logic here
        return True

    async def connect(self, websocket: WebSocket, game_id: str):
        is_valid = await self.validate_game_id(game_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid game ID")

        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = []
        self.connections[game_id].append(websocket)

    def disconnect(self, websocket: WebSocket, game_id: str):
        if game_id in self.connections and websocket in self.connections[game_id]:
            self.connections[game_id].remove(websocket)

    async def broadcast(self, data: str, game_id: str):
        if game_id in self.connections:
            for connection in self.connections[game_id]:
                await connection.send_text(data)




class Sockets:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def handle_message(self, data: str, websocket: WebSocket, game_id: str):
        try:
            json_data = json.loads(data)
            await self.process_image_generation(json_data, websocket, game_id)
        except json.JSONDecodeError:
            await self.send_error_message(websocket, "Invalid JSON format", game_id)

    async def process_image_generation(self, json_data: dict, websocket: WebSocket, game_id: str):
        image_id = await generate_async(json_data['prompt'])
        await self.check_image_generation_status(image_id, websocket, game_id)

    async def check_image_generation_status(self, image_id: str, websocket: WebSocket, game_id: str):
        generated = False
        while not generated:
            image_gen = await generate_status(image_id)
            generated, response_data = self.evaluate_generation_status(image_gen)
            await self.manager.broadcast(json.dumps(response_data), game_id)
            if not generated:
                await asyncio.sleep(20)

    def evaluate_generation_status(self, image_gen: dict) -> Tuple[bool, dict]:
        if image_gen["finished"] and len(image_gen["generations"]) == 1:
            return True, self.build_response_data(image_gen, "completed")
        if image_gen["processing"]:
            return False, self.build_response_data(image_gen, "processing")
        if image_gen["faulted"]:
            return False, self.build_response_data(image_gen, "faulted")
        return False, self.build_response_data(image_gen, "waiting")

    def build_response_data(self, image_gen: dict, status: str) -> dict:
        return {
            "id": image_gen["generations"][0]["id"] if status == "completed" else '',
            "status": status,
            "image_url": image_gen["generations"][0]["img"] if status == "completed" else None
        }

    async def send_error_message(self, websocket: WebSocket, message: str, game_id: str):
        await self.manager.broadcast(json.dumps({"status": "error", "message": message}), game_id)


manager = ConnectionManager()
sockets_instance = Sockets(manager)

# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, id: str = Query(...)):
#     await manager.connect(websocket, id)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await sockets_instance.handle_message(data, websocket, id)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket, id)


@router.websocket("/ws2")
async def websocket_endpoint(websocket: WebSocket, id: str = Query(...)):
    print(id)
    await manager.connect(websocket, id)
    await roles_allocation(websocket, id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await handle_message2(data, websocket, id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, id)

async def handle_message2(data, websocket, id):
    json_data = json.loads(data)

    await manager.broadcast(json.dumps(json_data), id)

async def roles_allocation(websocket, id):

    role = {
        'type': 'role_allocation',
        'status' : 'finished',
        "role": 'controller'   
    }
    if len(manager.connections[id]) > 1:
        role['role'] = 'guesser'

    await websocket.send_text(json.dumps(role))

