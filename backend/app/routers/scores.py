"""
Rutas para gestión de puntuaciones y rankings de liga.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.core import Matchday, PlayerScore, League, Team, TransferStatus
from app.schemas.score import MatchdayCreate, PlayerScoreIn, MatchdayScoreboard, TeamMatchdayScore, LeagueRanking
from app.routers.auth import get_current_user

router = APIRouter(prefix="/scores", tags=["scores"])


@router.post("/matchday", response_model=Matchday)
def create_matchday(matchday_in: MatchdayCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Crea una jornada para una liga."""
    league = db.query(League).get(matchday_in.league_id)
    if not league:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liga no encontrada")
    matchday = Matchday(league_id=matchday_in.league_id, number=matchday_in.number, date=matchday_in.date)
    db.add(matchday)
    db.commit()
    db.refresh(matchday)
    return matchday


@router.post("/player", response_model=PlayerScore)
def add_player_score(score_in: PlayerScoreIn, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Guarda puntuación de un jugador en una jornada."""
    matchday = db.query(Matchday).get(score_in.matchday_id)
    if not matchday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada inexistente")
    score = db.query(PlayerScore).filter(
        PlayerScore.player_id == score_in.player_id, PlayerScore.matchday_id == score_in.matchday_id
    ).first()
    if score:
        score.points = score_in.points
    else:
        score = PlayerScore(player_id=score_in.player_id, matchday_id=score_in.matchday_id, points=score_in.points)
        db.add(score)
    db.commit()
    db.refresh(score)
    return score


@router.get("/matchday/{league_id}/{matchday_id}", response_model=MatchdayScoreboard)
def get_matchday_scores(league_id: int, matchday_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Calcula puntos por equipo en una jornada dada."""
    matchday = db.query(Matchday).get(matchday_id)
    if not matchday or matchday.league_id != league_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada en la liga")
    teams = db.query(Team).filter(Team.league_id == league_id).all()
    results = []
    for team in teams:
        player_ids = [t.player_id for t in team.transfers if t.status == TransferStatus.WON]
        if not player_ids:
            results.append(TeamMatchdayScore(team_id=team.id, team_name=team.name, points=0))
            continue
        points = (
            db.query(func.sum(PlayerScore.points))
            .filter(PlayerScore.matchday_id == matchday_id, PlayerScore.player_id.in_(player_ids))
            .scalar()
            or 0
        )
        results.append(TeamMatchdayScore(team_id=team.id, team_name=team.name, points=float(points)))
    results.sort(key=lambda r: r.points, reverse=True)
    return MatchdayScoreboard(matchday_id=matchday_id, teams=results)


@router.get("/ranking/{league_id}", response_model=LeagueRanking)
def league_ranking(league_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Calcula ranking acumulado por liga."""
    teams = db.query(Team).filter(Team.league_id == league_id).all()
    ranking = []
    for team in teams:
        player_ids = [t.player_id for t in team.transfers if t.status == TransferStatus.WON]
        if not player_ids:
            ranking.append(TeamMatchdayScore(team_id=team.id, team_name=team.name, points=0))
            continue
        points = (
            db.query(func.sum(PlayerScore.points))
            .join(Matchday, PlayerScore.matchday_id == Matchday.id)
            .filter(Matchday.league_id == league_id, PlayerScore.player_id.in_(player_ids))
            .scalar()
            or 0
        )
        ranking.append(TeamMatchdayScore(team_id=team.id, team_name=team.name, points=float(points)))
    ranking.sort(key=lambda r: r.points, reverse=True)
    return LeagueRanking(league_id=league_id, ranking=ranking)
