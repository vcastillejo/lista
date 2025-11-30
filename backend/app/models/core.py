"""
Modelos principales de la aplicación de fantasy.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PositionEnum(str, enum.Enum):
    """Enumeración de posiciones de jugador."""

    GK = "POR"
    DEF = "DEF"
    MID = "MED"
    FWD = "DEL"


class BidStatus(str, enum.Enum):
    """Estado de la puja."""

    PENDING = "pending"
    WON = "won"
    LOST = "lost"


class TransferStatus(str, enum.Enum):
    """Estado de la transferencia/compra de jugador."""

    WON = "won"
    RELEASED = "released"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    leagues = relationship("LeagueMember", back_populates="user", cascade="all, delete")
    teams = relationship("Team", back_populates="user", cascade="all, delete")


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User")
    members = relationship("LeagueMember", back_populates="league", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")
    matchdays = relationship("Matchday", back_populates="league", cascade="all, delete-orphan")


class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("user_id", "league_id", name="uq_member_league"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="leagues")
    league = relationship("League", back_populates="members")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("user_id", "league_id", name="uq_team_per_league"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    budget = Column(Float, default=200_000_000)
    formation = Column(String, default="4-4-2")
    total_value = Column(Float, default=0)

    user = relationship("User", back_populates="teams")
    league = relationship("League", back_populates="teams")
    transfers = relationship("Transfer", back_populates="team", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="team", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    real_team = Column(String, nullable=False)
    position = Column(Enum(PositionEnum), nullable=False)
    market_value = Column(Float, default=0)
    active = Column(Boolean, default=True)

    scores = relationship("PlayerScore", back_populates="player", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="player")
    bids = relationship("Bid", back_populates="player")


class Matchday(Base):
    __tablename__ = "matchdays"
    __table_args__ = (UniqueConstraint("league_id", "number", name="uq_matchday_league"),)

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    number = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    league = relationship("League", back_populates="matchdays")
    scores = relationship("PlayerScore", back_populates="matchday", cascade="all, delete-orphan")


class PlayerScore(Base):
    __tablename__ = "player_scores"
    __table_args__ = (UniqueConstraint("player_id", "matchday_id", name="uq_player_matchday"),)

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    matchday_id = Column(Integer, ForeignKey("matchdays.id"), nullable=False)
    points = Column(Float, default=0)

    player = relationship("Player", back_populates="scores")
    matchday = relationship("Matchday", back_populates="scores")


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransferStatus), default=TransferStatus.WON)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="transfers")
    player = relationship("Player", back_populates="transfers")


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(BidStatus), default=BidStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    player = relationship("Player", back_populates="bids")
    team = relationship("Team", back_populates="bids")
