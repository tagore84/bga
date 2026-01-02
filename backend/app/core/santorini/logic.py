from typing import List, Tuple, Optional, Dict

class SantoriniLogic:
    ROWS = 5
    COLS = 5

    @staticmethod
    def initialize_board() -> List[List[Dict]]:
        """
        Board is 5x5.
        Each cell: {'level': 0, 'worker': None}
        level: 0=ground, 1, 2, 3, 4=dome
        worker: 'p1' or 'p2' or None
        """
        return [[{'level': 0, 'worker': None} for _ in range(5)] for _ in range(5)]

    @staticmethod
    def is_valid_pos(r: int, c: int) -> bool:
        return 0 <= r < 5 and 0 <= c < 5

    @staticmethod
    def get_valid_moves(board: List[List[Dict]], player: str) -> List[Dict]:
        """
        Returns list of valid moves.
        A move consists of:
        - worker_pos: (r, c)
        - move_to: (r, c)
        - build_at: (r, c)
        """
        moves = []
        workers = []
        
        # Find player workers
        for r in range(5):
            for c in range(5):
                if board[r][c]['worker'] == player:
                    workers.append((r, c))

        # Can only move if game not over (checked outside/implied)

        for wr, wc in workers:
            current_level = board[wr][wc]['level']
            
            # 1. Move Phase
            # Adjacent cells including diagonals
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    
                    nr, nc = wr + dr, wc + dc
                    
                    if not SantoriniLogic.is_valid_pos(nr, nc): continue
                    
                    target_cell = board[nr][nc]
                    
                    # Cannot move to occupied cell (worker or dome)
                    if target_cell['worker'] is not None: continue
                    if target_cell['level'] == 4: continue # Dome
                    
                    # Max 1 level up, any level down
                    if target_cell['level'] > current_level + 1: continue
                    
                    # Valid move found. Now checks for build
                    # Simulate move temporarily
                    # But need to check if there is AT LEAST one valid build spot from new pos
                    
                    # Worker is now at nr, nc
                    # Build adjacent to nr, nc
                    
                    can_build = False
                    possible_builds = []
                    
                    for bdr in [-1, 0, 1]:
                        for bdc in [-1, 0, 1]:
                            if bdr == 0 and bdc == 0: continue
                            
                            br, bc = nr + bdr, nc + bdc
                            if not SantoriniLogic.is_valid_pos(br, bc): continue
                            
                            build_cell = board[br][bc]
                            
                            # Cannot build on occupied cell 
                            # NOTE: The worker 'wr, wc' has moved to 'nr, nc'. 
                            # So 'wr, wc' is now EMPTY and available to build on, UNLESS it's the same spot (impossible)
                            # But other workers are obstacles.
                            
                            # Check if occupied by OTHER worker
                            is_occupied_by_worker = build_cell['worker'] is not None
                            
                            # Special case: The spot we just left (wr, wc) is NOT occupied anymore
                            if br == wr and bc == wc:
                                is_occupied_by_worker = False
                            
                            if is_occupied_by_worker: continue
                            if build_cell['level'] == 4: continue # Dome
                            
                            possible_builds.append((br, bc))
                            
                    if possible_builds:
                        for br, bc in possible_builds:
                            moves.append({
                                'worker_start': (wr, wc),
                                'move_to': (nr, nc),
                                'build_at': (br, bc)
                            })
                            
        return moves

    @staticmethod
    def apply_move(board: List[List[Dict]], move: Dict, player: str) -> Tuple[List[List[Dict]], str]:
        """
        Applies move and returns (new_board, status)
        """
        import copy
        new_board = copy.deepcopy(board)
        
        wr, wc = move['worker_start']
        nr, nc = move['move_to']
        br, bc = move['build_at']
        
        # 1. Move
        if new_board[wr][wc]['worker'] != player:
            raise ValueError("Invalid worker ownership")
            
        new_board[wr][wc]['worker'] = None
        new_board[nr][nc]['worker'] = player
        
        # Check Win Condition: Moved to level 3
        if new_board[nr][nc]['level'] == 3:
            return new_board, f"{player}_won"
            
        # 2. Build
        new_board[br][bc]['level'] += 1
        
        return new_board, "in_progress"

    @staticmethod
    def check_loss(board: List[List[Dict]], player: str) -> bool:
        """
        Returns True if player has NO valid moves.
        """
        moves = SantoriniLogic.get_valid_moves(board, player)
        return len(moves) == 0
