"""
Rutas para gestión de equipos y alineaciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Team, Transfer, Player, TransferStatus
from app.schemas.team import TeamDetail, LineupUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/{league_id}", response_model=TeamDetail)
def get_my_team(league_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Obtiene el equipo del usuario para una liga específica."""
    team = db.query(Team).filter(Team.league_id == league_id, Team.user_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado en la liga")
    return team


@router.post("/{league_id}/lineup", response_model=TeamDetail)
def update_lineup(
    league_id: int,
    update: LineupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Actualiza formación y jugadores adquiridos en el equipo."""
    team = db.query(Team).filter(Team.league_id == league_id, Team.user_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipo no encontrado")
    if update.formation:
        team.formation = update.formation
    valid_players = db.query(Player).filter(Player.id.in_(update.player_ids)).all() if update.player_ids else []
    if update.player_ids and len(valid_players) != len(update.player_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IDs de jugador inválidos")
    for player in valid_players:
        existing = (
            db.query(Transfer)
            .filter(
                Transfer.team_id == team.id,
                Transfer.player_id == player.id,
                Transfer.status == TransferStatus.WON,
            )
            .first()
        )
        if not existing:
            transfer = Transfer(
                team_id=team.id,
                player_id=player.id,
                amount=player.market_value,
                status=TransferStatus.WON,
            )
            team.total_value += player.market_value
            db.add(transfer)
    db.commit()
    db.refresh(team)
    return team
