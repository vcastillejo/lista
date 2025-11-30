"""
Punto de entrada de la API FastAPI para la liga fantasy.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, leagues, teams, market, scores
from app.models import core  # noqa: F401 - asegura carga de modelos

# Crear tablas si no existen (para desarrollo rápido).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fantasy League API")

# Configuración básica de CORS para permitir frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers.
app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(teams.router)
app.include_router(market.router)
app.include_router(scores.router)


@app.get("/")
def root():
    """Endpoint base para verificar estado."""
    return {"message": "API de liga fantasy funcionando"}
