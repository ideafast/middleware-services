from pydantic import BaseModel

class VerifyToken(BaseModel):
    token: str

