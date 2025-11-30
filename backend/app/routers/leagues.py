"""
Rutas para gestión de ligas: creación, unión y consulta.
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import League, LeagueMember, Team
from app.schemas.league import LeagueCreate, LeagueOut
from app.schemas.team import TeamOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/leagues", tags=["leagues"])

DEFAULT_BUDGET = 200_000_000


def generate_invite_code() -> str:
    """Genera un código de invitación único y legible."""
    return secrets.token_hex(4)


@router.post("/", response_model=LeagueOut, status_code=status.HTTP_201_CREATED)
def create_league(league_in: LeagueCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Crea una liga privada y asigna al usuario como administrador."""
    code = generate_invite_code()
    league = League(name=league_in.name, invite_code=code, admin_id=current_user.id)
    db.add(league)
    db.flush()
    membership = LeagueMember(user_id=current_user.id, league=league, role="admin")
    team = Team(name=f"Equipo de {current_user.full_name}", user_id=current_user.id, league=league, budget=DEFAULT_BUDGET)
    db.add_all([membership, team])
    db.commit()
    db.refresh(league)
    return league


@router.post("/join", response_model=LeagueOut)
def join_league(invite_code: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Permite a un usuario unirse a una liga mediante código."""
    league = db.query(League).filter(League.invite_code == invite_code).first()
    if not league:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liga no encontrada")
    existing_member = (
        db.query(LeagueMember)
        .filter(LeagueMember.league_id == league.id, LeagueMember.user_id == current_user.id)
        .first()
    )
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya estás en la liga")
    membership = LeagueMember(user_id=current_user.id, league_id=league.id, role="member")
    team = Team(name=f"Equipo de {current_user.full_name}", user_id=current_user.id, league_id=league.id, budget=DEFAULT_BUDGET)
    db.add_all([membership, team])
    db.commit()
    db.refresh(league)
    return league


@router.get("/me", response_model=list[LeagueOut])
def my_leagues(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Lista las ligas en las que participa el usuario."""
    memberships = db.query(LeagueMember).filter(LeagueMember.user_id == current_user.id).all()
    league_ids = [m.league_id for m in memberships]
    leagues = db.query(League).filter(League.id.in_(league_ids)).all()
    return leagues
