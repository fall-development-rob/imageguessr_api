from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import RedirectResponse
import json
import asyncio
from typing import Dict, List, Tuple
from api.lib.stablehorde import generate_async, generate_status

from api.schema import game as Game

import random

import string

from api.lib import connections_manager as manager

router = APIRouter(
    prefix="/game",
    tags=["game"],
    responses={404: {"description": "Not found"}},
)

@router.get("/new", response_model=Game.NewGame)
async def new_game():
    game_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    return RedirectResponse(f"http://localhost:3000/game?id={game_id}")

@router.websocket("/ws2")
async def websocket_endpoint(websocket: WebSocket, id: str = Query(...)):
    print(id)
    await manager.connect(websocket, id)
    await roles_allocation(websocket, id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await handle_message(data, websocket, id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, id)

async def handle_message(data, websocket, id):
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


# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, id: str = Query(...)):
#     await manager.connect(websocket, id)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await sockets_instance.handle_message(data, websocket, id)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket, id)

