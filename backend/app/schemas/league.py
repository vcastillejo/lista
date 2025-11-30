"""
Esquemas Pydantic para ligas y membresías.
"""
from datetime import datetime
from pydantic import BaseModel
from typing import List

from app.schemas.user import UserOut


class LeagueBase(BaseModel):
    name: str


class LeagueCreate(LeagueBase):
    pass


class LeagueOut(LeagueBase):
    id: int
    invite_code: str
    admin_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class LeagueMemberOut(BaseModel):
    user: UserOut
    role: str
    joined_at: datetime

    class Config:
        orm_mode = True


class LeagueWithMembers(LeagueOut):
    members: List[LeagueMemberOut] = []
