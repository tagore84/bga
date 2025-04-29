# backend/app/core/seed.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player, PlayerType  # Import the Player model
from app.models.game import Game  # Import the Game model


async def seed_games(db: AsyncSession):
    """
    Inserta juegos por defecto si no existen.
    """
    # Comprueba si ya existe el juego "tictactoe"
    result = await db.execute(
        select(Game).where(Game.name == "tictactoe")
    )
    existing = result.scalar_one_or_none()
    if not existing:
        game = Game(
            name="tictactoe",
            description="Juego clásico de tres en raya"
        )
        db.add(game)
        await db.commit()
        await db.refresh(game)
        print(f"Juego {game.name} creado.")
    else:
        print(f"Juego {existing.name} ya existe. No se ha creado nada nuevo.")
        return existing
    return game



async def seed_ai_players(db: AsyncSession):
    """
    Inserta jugadores IA por defecto si no existen.
    """
    # Comprueba si ya existe el juego "tictactoe"
    game_result = await db.execute(
        select(Game).where(Game.name == "tictactoe")
    )
    game_existing = game_result.scalar_one_or_none()

    # Comprueba si ya existe la IA "RandomTicTacToe"
    result = await db.execute(
        select(Player).where(Player.name == "RandomTicTacToe")
    )
    existing = result.scalar_one_or_none()
    if not existing:
        ia = Player(
            name="RandomTicTacToe",
            description="Elige movimientos válidos al azar",
            game_id=game_existing.id,
            hashed_password=None,
            type = PlayerType.ai,
        )
        db.add(ia)
        await db.commit()
    else:
        print(f"IA {existing.name} ya existe. No se ha creado nada nuevo.")
        # Si la IA ya existe, no hacemos nada
        return existing

    
