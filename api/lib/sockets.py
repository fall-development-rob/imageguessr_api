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