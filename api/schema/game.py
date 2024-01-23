from pydantic import BaseModel

class NewGame(BaseModel):
    id: str

class JoinGame(BaseModel):
    id: str
