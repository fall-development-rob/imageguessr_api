from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import RedirectResponse
import json
import asyncio
from typing import Dict, List, Tuple
from api.lib.stablehorde import generate_async, generate_status

from api.schema import game as Game

import random

import string

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