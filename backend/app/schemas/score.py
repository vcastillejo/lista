"""
Esquemas Pydantic para puntuaciones y rankings.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel

from app.schemas.player import PlayerOut


class MatchdayCreate(BaseModel):
    league_id: int
    number: int
    date: datetime


class PlayerScoreIn(BaseModel):
    player_id: int
    matchday_id: int
    points: float


class PlayerScoreOut(PlayerScoreIn):
    id: int

    class Config:
        orm_mode = True


class TeamMatchdayScore(BaseModel):
    team_id: int
    team_name: str
    points: float


class LeagueRanking(BaseModel):
    league_id: int
    ranking: List[TeamMatchdayScore]


class PlayerScoreDetail(BaseModel):
    player: PlayerOut
    points: float


class MatchdayScoreboard(BaseModel):
    matchday_id: int
    teams: List[TeamMatchdayScore]
