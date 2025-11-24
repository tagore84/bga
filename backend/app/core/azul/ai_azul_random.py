import random
from app.core.ai_base import AIBase, register_ai


class RandomAzulAI(AIBase):
    def select_move(self, state):
        return self.predict(state)

    def predict(self, state):
        """
        Dado el estado del juego (AzulGameState), construye la lista de acciones legales
        y devuelve una elegida al azar.
        """
        from app.models.azul.azul import get_legal_moves
        
        legal_moves = get_legal_moves(state)
        
        if not legal_moves:
            # Esto no debería pasar si el juego no ha terminado
            raise RuntimeError("No hay acciones legales disponibles")
            
        output_move = random.choice(legal_moves)
        print(f"RandomAzulAI ha elegido el movimiento: {output_move}")
        return output_move

# al importar este módulo, se registra
register_ai("RandomAzul", RandomAzulAI())