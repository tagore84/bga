from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.game import Game
from app.models.azul.azul import AzulGame, AzulGameOutput, AzulGameState, AzulMove, aplicar_movimiento
from app.core.azul.game import init_game_state
from app.core.events import publish_azul_update
import json
from typing import List
from sqlalchemy.future import select
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

router = APIRouter()

class CreateGameRequest(BaseModel):
    game_name: str
    jugadores: List[dict]  # cada uno con 'id' y 'type'

async def run_ai_turns_background(game_id: int, azul_id: int):
    """
    Helper to run AI turns in background with its own DB session.
    """
    async with AsyncSessionLocal() as db:
        # Re-fetch the game/state within this new session
        result = await db.execute(select(AzulGame).where(AzulGame.id == azul_id))
        partida = result.scalar_one_or_none()
        if not partida:
            return
        
        try:
            state = AzulGameState.parse_obj(partida.state)
        except Exception as e:
            print(f"Error parsing state in background task: {e}")
            return

        await process_ai_turns(game_id, partida, state, db)

@router.post("/", response_model=dict)
async def crear_partida_azul(req: CreateGameRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # 1) Obtener o crear entrada en la tabla 'games'
    result = await db.execute(select(Game).where(Game.name == req.game_name))
    base_game = result.scalar_one_or_none()
    if base_game is None:
        base_game = Game(name=req.game_name)
        db.add(base_game)
        await db.commit()
        await db.refresh(base_game)

    # 2) Generar estado inicial del juego pasando la lista completa de jugadores
    estado = init_game_state(req.jugadores)
    
    # 3) Crear entrada en azul_games
    partida = AzulGame(
        game_id=base_game.id,
        state=json.loads(estado.json())
    )
    db.add(partida)
    await db.commit()
    await db.refresh(partida)
    
    # Trigger AI turns in background
    background_tasks.add_task(run_ai_turns_background, base_game.id, partida.id)
    
    return {"game_id": base_game.id, "azul_id": partida.id, "state": partida.state}


# Listar partidas activas
@router.get("/", response_model=List[AzulGameOutput])
async def list_azul_games(db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(AzulGame))
    games = q.scalars().all()
    out = []
    for g in games:
        state = AzulGameState.parse_obj(g.state)
        id = g.id
        gameOutput = AzulGameOutput(id=id, state=state)
        if not state.terminado:  # o state.fase == "oferta"
            out.append(gameOutput)

    return out

@router.get("/{game_id}", response_model=AzulGameState)
async def get_azul_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AzulGame).where(AzulGame.id == game_id))
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Partida Azul no encontrada")

    try:
        state = AzulGameState.parse_obj(game.state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al parsear el estado: {str(e)}")

    return state

@router.delete("/{game_id}")
async def delete_azul_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AzulGame).where(AzulGame.id == game_id))
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Partida Azul no encontrada")
    
    await db.delete(game)
    await db.commit()
    
    return {"message": "Partida eliminada correctamente", "id": game_id}


@router.post("/{game_id}/move")
async def make_move(game_id: int, move: AzulMove, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AzulGame).where(AzulGame.id == game_id))
    partida = result.scalar_one_or_none()
    if not partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    try:
        state = AzulGameState.parse_obj(partida.state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estado corrupto: {str(e)}")

    # Buscar jugador activo
    jugador_id = state.turno_actual
    if jugador_id is None or jugador_id not in state.jugadores:
        raise HTTPException(status_code=400, detail="No hay jugador activo o ID inválido")

    # Aplicar el movimiento
    old_round = state.ronda
    aplicar_movimiento(state, jugador_id, move)

    # Avanzar al siguiente turno SOLO si la ronda no ha cambiado y el juego no ha terminado
    # Si la ronda cambió, aplicar_movimiento -> prepare_next_round ya actualizó turno_actual
    if state.ronda == old_round and not state.terminado:
        jugadores_ids = list(state.jugadores.keys())
        if jugadores_ids:
            idx = jugadores_ids.index(jugador_id)
            for offset in range(1, len(jugadores_ids) + 1):
                siguiente = jugadores_ids[(idx + offset) % len(jugadores_ids)]
                # Verifica si el siguiente jugador tiene movimientos posibles
                if True:  # <- aquí luego se puede mejorar con una lógica real
                    state.turno_actual = siguiente
                    break

    # Guardar el nuevo estado
    partida.state = json.loads(state.json())
    db.add(partida)
    await db.commit()
    await db.refresh(partida)

    await publish_azul_update(game_id, partida.state)

    await process_ai_turns(game_id, partida, state, db)
    return {"ok": True, "state": partida.state}

async def process_ai_turns(game_id: int, partida: AzulGame, state: AzulGameState, db: AsyncSession):
    # Jugada IA si aplica (bucle IA)
    while True:
        if state.terminado:
            break
            
        siguiente_jugador = state.turno_actual
        jugador_info = state.jugadores.get(siguiente_jugador)
        if not jugador_info or jugador_info.type != "ai":
            break

        from app.core.ai_base import get_ai  # Asegúrate de tener este helper
        ai = get_ai(jugador_info.name)
        ai_move = ai.select_move(state)

        # Aplicar jugada IA
        old_round = state.ronda
        aplicar_movimiento(state, siguiente_jugador, ai_move)
        print(f"IA {jugador_info.name} ha jugado: {ai_move}")
        
        # Avanzar turno nuevamente si quedan movimientos y NO cambió la ronda
        if state.ronda == old_round and not state.terminado:
            jugadores_ids = list(state.jugadores.keys())
            if jugadores_ids:
                idx = jugadores_ids.index(siguiente_jugador)
                for offset in range(1, len(jugadores_ids) + 1):
                    siguiente = jugadores_ids[(idx + offset) % len(jugadores_ids)]
                    if True:  # reemplazar con lógica real de si el jugador puede mover
                        state.turno_actual = siguiente
                        break

        # Guardar nuevo estado después del movimiento IA
        partida.state = json.loads(state.json())
        db.add(partida)
        print(f"Estado actualizado después del movimiento IA: {partida.state}")
        await db.commit()
        await db.refresh(partida)

        await publish_azul_update(game_id, partida.state)
    print(f"Estado final después de todas las jugadas: {partida.state}")
