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
        - move_type: 'move_build' or 'place_worker'
        - worker_start: (r, c) (optional for placement)
        - move_to: (r, c) (placement target)
        - build_at: (r, c) (optional for placement)
        """
        moves = []
        workers = []
        
        # Find player workers
        all_workers = []
        for r in range(5):
            for c in range(5):
                if board[r][c]['worker'] is not None:
                    all_workers.append(board[r][c]['worker'])
                    if board[r][c]['worker'] == player:
                        workers.append((r, c))

        # Check for Placement Phase
        # Total workers should be 4 (2 per player)
        # If less than 4, and it's this player's turn (logic handled by caller/implied), then generating placement moves.
        # But we need to know if it is indeed placement phase. 
        # Actually simplest logic: if this player has < 2 workers, they can place.
        
        if len(workers) < 2:
            # Generate placement moves
            for r in range(5):
                for c in range(5):
                    if board[r][c]['worker'] is None:
                        moves.append({
                            'move_type': 'place_worker',
                            'move_to': (r, c),
                            'worker_start': None,
                            'build_at': None
                        })
            return moves

        # Normal Move Phase
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
                    
                    if target_cell['level'] == 3:
                        # Winning move! No build needed.
                        moves.append({
                            'move_type': 'move_build',
                            'worker_start': (wr, wc),
                            'move_to': (nr, nc),
                            'build_at': None # No build triggered
                        })
                        continue # Skip build check for this move path

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
                                'move_type': 'move_build',
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
        
        move_type = move.get('move_type', 'move_build')
        
        if move_type == 'place_worker':
            nr, nc = move['move_to']
            if new_board[nr][nc]['worker'] is not None:
                raise ValueError("Cell occupied")
            new_board[nr][nc]['worker'] = player
            
            # Status check for placement
            # If after this placement, the player has 2 workers? 
            # Actually status is managed by the route mostly for turns, but we can return 'in_progress'
            return new_board, "in_progress"

        if move_type == 'move_build':
            wr, wc = move['worker_start']
            nr, nc = move['move_to']
            if move['build_at'] is None:
                br, bc = None, None
            else:
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
            if br is not None and bc is not None:
                new_board[br][bc]['level'] += 1
            else:
                 # This should only happen if we moved to level 3 (captured above) or if logic allows moves without build (not aiming for that except win)
                 # But if we are here and didn't win, and have no build, it's weird unless we allow "optional build"?
                 # Rules say build is mandatory. So we can raise error or check consistency.
                 # Given new valid_moves logic, we only pass None if level==3.
                 pass
            
            return new_board, "in_progress"
            
        return new_board, "in_progress"

    @staticmethod
    def check_loss(board: List[List[Dict]], player: str) -> bool:
        """
        Returns True if player has NO valid moves.
        """
        moves = SantoriniLogic.get_valid_moves(board, player)
        return len(moves) == 0
