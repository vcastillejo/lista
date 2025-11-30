"""
Esquemas Pydantic para equipos y transferencias.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.user import UserOut
from app.schemas.player import PlayerOut


class TeamBase(BaseModel):
    name: str
    formation: str


class TeamCreate(TeamBase):
    league_id: int


class TeamOut(TeamBase):
    id: int
    user: UserOut
    budget: float
    total_value: float

    class Config:
        orm_mode = True


class TransferOut(BaseModel):
    id: int
    player: PlayerOut
    amount: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class TeamDetail(TeamOut):
    transfers: List[TransferOut] = []


class LineupUpdate(BaseModel):
    formation: Optional[str] = None
    player_ids: List[int] = []
