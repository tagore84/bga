# backend/app/core/seed.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import Player, PlayerType  # Import the Player model
from app.models.game import Game  # Import the Game model


async def seed_games(db: AsyncSession):
    """
    Inserta juegos por defecto si no existen.
    """
    juegos = [
        ("tictactoe", "Juego clásico de tres en raya"),
        ("azul", "Juego de losetas y patrones inspirado en el Palacio Real de Évora")
    ]
    for name, description in juegos:
        result = await db.execute(select(Game).where(Game.name == name))
        existing = result.scalar_one_or_none()
        if not existing:
            game = Game(name=name, description=description)
            db.add(game)
            await db.commit()
            await db.refresh(game)
            print(f"Juego {game.name} creado.")
        else:
            print(f"Juego {existing.name} ya existe. No se ha creado nada nuevo.")
  



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
    
        # Comprueba si ya existe la IA "RandomAzul"
    result = await db.execute(
        select(Player).where(Player.name == "RandomAzul")
    )
    existing_azul_ai = result.scalar_one_or_none()

    
