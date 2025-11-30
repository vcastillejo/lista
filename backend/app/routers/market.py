"""
Rutas para mercado de jugadores y pujas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.core import Player, Bid, Team, BidStatus, Transfer, TransferStatus, PositionEnum
from app.schemas.player import PlayerOut, BidCreate, BidOut, MarketListing
from app.routers.auth import get_current_user

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/players", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    """Lista jugadores activos disponibles en el mercado."""
    players = db.query(Player).filter(Player.active == True).order_by(Player.market_value.desc()).all()
    return players


@router.post("/bootstrap", response_model=list[PlayerOut])
def bootstrap_players(db: Session = Depends(get_db)):
    """Crea jugadores de ejemplo si la tabla está vacía."""
    existing = db.query(func.count(Player.id)).scalar()
    if existing > 0:
        return db.query(Player).all()
    sample = [
        Player(
            name="Marc André ter Stegen",
            real_team="FC Barcelona",
            position=PositionEnum.GK,
            market_value=35_000_000,
        ),
        Player(
            name="Ronald Araújo",
            real_team="FC Barcelona",
            position=PositionEnum.DEF,
            market_value=50_000_000,
        ),
        Player(
            name="Pedri",
            real_team="FC Barcelona",
            position=PositionEnum.MID,
            market_value=70_000_000,
        ),
        Player(
            name="Robert Lewandowski",
            real_team="FC Barcelona",
            position=PositionEnum.FWD,
            market_value=45_000_000,
        ),
        Player(
            name="Thibaut Courtois",
            real_team="Real Madrid",
            position=PositionEnum.GK,
            market_value=40_000_000,
        ),
        Player(
            name="Jude Bellingham",
            real_team="Real Madrid",
            position=PositionEnum.MID,
            market_value=120_000_000,
        ),
        Player(
            name="Vinícius Jr",
            real_team="Real Madrid",
            position=PositionEnum.FWD,
            market_value=110_000_000,
        ),
    ]
    db.add_all(sample)
    db.commit()
    return db.query(Player).all()


@router.post("/bid", response_model=BidOut, status_code=status.HTTP_201_CREATED)
def create_bid(
    bid_in: BidCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crea una puja para un jugador desde el equipo del usuario."""
    team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primero únete a una liga")
    player = db.query(Player).get(bid_in.player_id)
    if not player or not player.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no disponible")
    if bid_in.amount > team.budget:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fondos insuficientes")
    bid = Bid(player_id=player.id, team_id=team.id, amount=bid_in.amount)
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.post("/close/{player_id}", response_model=BidOut)
def close_bids(player_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Cierra pujas de un jugador y asigna al mejor postor."""
    player = db.query(Player).get(player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jugador no encontrado")
    bids = db.query(Bid).filter(Bid.player_id == player_id, Bid.status == BidStatus.PENDING).order_by(Bid.amount.desc()).all()
    if not bids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay pujas")
    winner = bids[0]
    # Marcar estados
    for bid in bids:
        bid.status = BidStatus.WON if bid.id == winner.id else BidStatus.LOST
    team = db.query(Team).get(winner.team_id)
    if team.budget < winner.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Presupuesto insuficiente al cerrar")
    team.budget -= winner.amount
    transfer = Transfer(team_id=team.id, player_id=player.id, amount=winner.amount, status=TransferStatus.WON)
    db.add(transfer)
    db.commit()
    db.refresh(winner)
    return winner


@router.get("/bids", response_model=list[BidOut])
def my_bids(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Lista las pujas realizadas por el usuario."""
    team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not team:
        return []
    bids = db.query(Bid).filter(Bid.team_id == team.id).order_by(Bid.created_at.desc()).all()
    return bids


@router.get("/listings", response_model=list[MarketListing])
def market_listings(db: Session = Depends(get_db)):
    """Devuelve jugadores con su puja más alta registrada."""
    listings = []
    players = db.query(Player).filter(Player.active == True).all()
    for player in players:
        top_bid = (
            db.query(Bid)
            .filter(Bid.player_id == player.id)
            .order_by(Bid.amount.desc())
            .first()
        )
        listings.append(MarketListing(player=player, highest_bid=top_bid))
    return listings
