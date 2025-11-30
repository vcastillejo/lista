"""
Esquemas Pydantic para jugadores y mercado.
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.models.core import PositionEnum


class PlayerBase(BaseModel):
    name: str
    real_team: str
    position: PositionEnum
    market_value: float
    active: bool = True


class PlayerCreate(PlayerBase):
    pass


class PlayerOut(PlayerBase):
    id: int

    class Config:
        orm_mode = True


class BidCreate(BaseModel):
    player_id: int
    amount: float


class BidOut(BaseModel):
    id: int
    player: PlayerOut
    team_id: int
    amount: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class MarketListing(BaseModel):
    player: PlayerOut
    highest_bid: Optional[BidOut] = None
