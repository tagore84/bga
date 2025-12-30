<template>
  <div class="chess-game-container">
    <div class="glass-panel header mb-2">
        <h2 class="text-center">{{ game ? game.config.game_name : 'Loading...' }}</h2>
        <div v-if="game" class="status-bar text-center">
            Turn: <span :class="game.current_turn === 'white' ? 'text-primary' : 'text-secondary'">{{ game.current_turn === 'white' ? 'White' : 'Black' }}</span>
            <span v-if="game.status !== 'in_progress'" class="game-over"> | {{ game.status }}</span>
            <span v-if="isCheck && game.status === 'in_progress'" class="text-danger font-bold ml-2"> | JAQUE!</span>
        </div>
        
        <!-- Evaluation Bar -->
        <div v-if="game && game.status === 'in_progress'" class="eval-bar-container mt-2" title="Win Probability">
             <div class="eval-bar-fill" :style="{ width: whiteEvalPercentage + '%' }"></div>
        </div>

        <div v-if="currentUser" class="player-info text-center mt-1">
             Playing as: <b class="text-accent">{{ getUserRole() }}</b>
        </div>
    </div>

    <div class="game-layout">
        <!-- Left Panel: Pieces captured by White (Black pieces) OR depending on orientation -->
        <!-- Strategy: Show pieces captured by the player AT THE TOP vs BOTTOM? -->
        <!-- Or just side by side. Let's do: Left = Captured Black pieces (White's trophies), Right = Captured White pieces (Black's trophies) -->
        <!-- Wait, usually you show "My Captured Material" near me. -->
        <!-- If I am White (bottom), I want to see Black pieces I captured. -->
        <!-- Let's stick to: Left Panel = Lost White Pieces (Captured by Black), Right Panel = Lost Black Pieces (Captured by White) -->
        <!-- Actually user asked "fichas comidas se vean en cada uno de los laterales". -->
        <!-- Let's put White's captured pieces (Black pieces) on one side, and Black's captured pieces (White pieces) on the other. -->
        
        <div class="captured-panel left-panel glass-panel">
            <h4 class="text-center text-secondary">Captured by Black</h4>
            <div class="captured-list">
                <div v-for="(p, i) in capturedPieces.whiteLost" :key="i" class="captured-piece">
                    <ChessPiece :piece="p" />
                </div>
            </div>
        </div>

        <div class="board-wrapper">
            <div class="board">
                <div v-for="(rank, rIndex) in displayRanks" :key="rank" class="rank">
                    <div v-for="(file, fIndex) in displayFiles" :key="file" 
                         class="square" 
                         :class="[getSquareClass(rank, file), { 'selected': isSelected(rank, file), 'in-check': isKingInCheck(rank, file) }]"
                         @click="handleSquareClick(rank, file)"
                         @dragover.prevent
                         @drop="handleDrop(rank, file)">
                         
                         <!-- Coordinates (Inside Style) -->
                         <span v-if="shouldShowRank(fIndex)" class="coord-rank" :class="getCoordClass(rank, file)">{{ rank }}</span>
                         <span v-if="shouldShowFile(rIndex)" class="coord-file" :class="getCoordClass(rank, file)">{{ getFileChar(file) }}</span>

                         <!-- Highlight Markers -->
                         <div v-if="isLastMove(rank, file)" class="last-move-marker"></div>
                         <div v-if="getValidMoveType(rank, file) === 'quiet'" class="valid-move-marker"></div>
                         <div v-if="getValidMoveType(rank, file) === 'capture'" class="valid-capture-marker"></div>

                        <!-- Piece -->
                        <div v-if="getPiece(rank, file)" 
                               class="piece-container" 
                               :draggable="canMove() && isOwnPiece(getPiece(rank, file))"
                               @dragstart="handleDragStart(rank, file, $event)">
                            <ChessPiece :piece="getPiece(rank, file)" />
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="captured-panel right-panel glass-panel">
            <h4 class="text-center text-primary">Captured by White</h4>
             <div class="captured-list">
                <div v-for="(p, i) in capturedPieces.blackLost" :key="i" class="captured-piece">
                    <ChessPiece :piece="p" />
                </div>
            </div>
        </div>
    </div>
    
    <div class="controls mt-2">
        <label class="toggle-container">
            <input type="checkbox" v-model="showHints">
            Mostrar posibles movimientos
        </label>
        <button v-if="canUndo" class="btn-undo" @click="undoMove">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-undo"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>
            Undo Move
        </button>
        <button class="btn-danger" @click="$router.push('/games')">Exit Game</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ChessPiece from './ChessPiece.vue'
import { API_BASE, WS_BASE } from '../../config'
import { Chess } from 'chess.js'

export default {
    name: 'ChessGame',
    components: {
        ChessPiece
    },
    data() {
        return {
            game: null,
            currentUser: null,
            error: null,
            selectedSquare: null, // {r, f}
            boardMatrix: [], // 8x8
            ws: null,
            dragSource: null,
            lastMove: null, // {from: {r, f}, to: {r, f}}
            evaluation: 0.0,
            isCheck: false,
            chessInstance: new Chess(),
            showHints: false,
            legalMoves: [] // List of legal moves for selected square
        }
    },
    computed: {
        capturedPieces() {
            if (!this.boardMatrix || this.boardMatrix.length === 0) return { whiteLost: [], blackLost: [] };

            const standardCounts = {
                'P': 8, 'R': 2, 'N': 2, 'B': 2, 'Q': 1, 'K': 1,
                'p': 8, 'r': 2, 'n': 2, 'b': 2, 'q': 1, 'k': 1
            };
            
            const currentCounts = {};
            // Init current counts to 0
            Object.keys(standardCounts).forEach(k => currentCounts[k] = 0);

            // Count pieces on board
            for (let r = 0; r < 8; r++) {
                for (let c = 0; c < 8; c++) {
                    const p = this.boardMatrix[r][c];
                    if (p) {
                         currentCounts[p] = (currentCounts[p] || 0) + 1;
                    }
                }
            }

            const whiteLost = [];
            const blackLost = [];

            // Calculate White Lost (Upper case)
            ['Q', 'R', 'B', 'N', 'P'].forEach(p => {
                const lost = standardCounts[p] - (currentCounts[p] || 0);
                for (let i = 0; i < lost; i++) whiteLost.push(p);
            });

            // Calculate Black Lost (Lower case)
            ['q', 'r', 'b', 'n', 'p'].forEach(p => {
                const lost = standardCounts[p] - (currentCounts[p] || 0);
                for (let i = 0; i < lost; i++) blackLost.push(p);
            });

            return { whiteLost, blackLost };
        },
        isBlackPlayer() {
            if (!this.game || !this.currentUser) return false;
            return this.currentUser.id === this.game.black_player_id;
        },
        displayRanks() {
            // White wants 1 at bottom -> [8, 7, ..., 1]
            // Black wants 8 at bottom -> [1, 2, ..., 8]
            const ranks = [1, 2, 3, 4, 5, 6, 7, 8];
            return this.isBlackPlayer ? ranks : [...ranks].reverse();
        },
        displayFiles() {
            // White wants a (1) at left -> [1, 2, ..., 8]
            // Black wants h (8) at left -> [8, 7, ..., 1]
            const files = [1, 2, 3, 4, 5, 6, 7, 8];
            return this.isBlackPlayer ? [...files].reverse() : files;
        },
        whiteEvalPercentage() {
            // Clamp score between -20 and 20
            const maxScore = 20;
            let val = parseFloat(this.evaluation);
            if (isNaN(val)) val = 0;
            
            // Backend sends centipawns (100 = 1 pawn). Frontend expects pawns.
            val = val / 100.0;

            // Sigmoid-ish or simpler linear mapping
            // -20 -> 0%, 0 -> 50%, 20 -> 100%
            let pct = 50 + (val / maxScore) * 50;
            if (pct < 5) pct = 5; // Minimum vis
            if (pct > 95) pct = 95; // Max vis
            
            return pct;
        },
        canUndo() {
            if (!this.game || !this.currentUser) return false;
            
            const isParticipant = (this.currentUser.id === this.game.white_player_id || 
                                   this.currentUser.id === this.game.black_player_id);
            if (!isParticipant) return false;
            
            // Check if there are moves
            if (!this.game.config || !this.game.config.moves || this.game.config.moves.length === 0) return false;
            
            return true;
        }
    },
    async created() {
        const gameId = this.$route.params.id;
        await this.fetchCurrentUser();
        await this.fetchGame(gameId);
        this.connectWebSocket(gameId);
    },
    beforeUnmount() {
        if (this.ws) this.ws.close();
    },
    methods: {
        async fetchCurrentUser() {
             try {
                const token = localStorage.getItem('token');
                if (!token) return;
                const res = await axios.get(`${API_BASE}/auth/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                this.currentUser = res.data;
            } catch (e) {
                console.error("Error fetching user", e);
            }
        },
        async fetchGame(id) {
            try {
                const token = localStorage.getItem('token');
                const res = await axios.get(`${API_BASE}/chess/${id}`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                this.game = res.data;
                this.evaluation = this.game.evaluation || 0.0;
                this.isCheck = this.game.is_check || false;
                
                // Sync chess.js
                try {
                    this.chessInstance.load(this.game.board_fen);
                } catch (err) {
                    console.error("Failed to load FEN into chess.js", err);
                }
                
                this.parseFen(this.game.board_fen);
                
                // Restore last move
                if (this.game.config && this.game.config.moves && this.game.config.moves.length > 0) {
                    const lastUci = this.game.config.moves[this.game.config.moves.length - 1];
                    this.lastMove = this.uciToCoords(lastUci);
                } else {
                    this.lastMove = null;
                }
            } catch (e) {
                this.error = "Error loading game";
                console.error(e);
            }
        },
        connectWebSocket(gameId) {
            this.ws = new WebSocket(`${WS_BASE}/ws/chess/${gameId}`);
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'move' || data.type === 'create') {
                     // Update game state
                     this.game.board_fen = data.fen;
                     // We should trust the server's next turn closer, but toggle logic is ok for simple sync
                     this.game.current_turn = data.by === 'white' ? 'black' : 'white'; 
                     this.game.status = data.status;
                     
                     // Sync chess.js
                     try {
                        this.chessInstance.load(data.fen);
                     } catch (err) {
                        console.error("Failed to sync chess.js", err);
                     }
                     
                     this.parseFen(data.fen);
                     
                     if (data.evaluation !== undefined) {
                        this.evaluation = parseFloat(data.evaluation);
                     }
                     
                     if (data.is_check !== undefined) {
                        this.isCheck = data.is_check === 'True' || data.is_check === true;
                     } else {
                        this.isCheck = false;
                     }

                     // Store last move for highlighting
                     if (data.move_uci) {
                        this.lastMove = this.uciToCoords(data.move_uci);
                        
                        // Update moves list so Undo becomes available immediately
                        if (!this.game.config) this.game.config = {};
                        if (!this.game.config.moves) this.game.config.moves = [];
                        this.game.config.moves.push(data.move_uci);
                     }

                     this.selectedSquare = null; 
                     this.legalMoves = [];
                } else if (data.type === 'undo') {
                    this.game.board_fen = data.fen;
                    this.fetchGame(gameId);
                }
            };
        },
        parseFen(fen) {
            // FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
            const rows = fen.split(' ')[0].split('/');
            const matrix = [];
            for (let r = 0; r < 8; r++) {
                const rowStr = rows[r];
                const row = [];
                for (let i = 0; i < rowStr.length; i++) {
                    const char = rowStr[i];
                    if (isNaN(char)) {
                        row.push(char);
                    } else {
                        const empties = parseInt(char);
                        for (let k = 0; k < empties; k++) row.push(null);
                    }
                }
                matrix.push(row);
            }
            this.boardMatrix = matrix;
        },
        getPiece(rank, file) {
            const rIndex = 8 - rank;
            const cIndex = file - 1;
            return this.boardMatrix[rIndex] ? this.boardMatrix[rIndex][cIndex] : null;
        },
        getSquareClass(rank, file) {
            return (rank + file) % 2 !== 0 ? 'light-square' : 'dark-square';
        },
        getCoordClass(rank, file) {
             return (rank + file) % 2 !== 0 ? 'coord-on-light' : 'coord-on-dark';
        },
        shouldShowRank(fIndex) {
            // Show rank only on the FIRST column displayed
            return fIndex === 0;
        },
        shouldShowFile(rIndex) {
            // Show file only on the LAST row displayed
            return rIndex === 7;
        },
        getFileChar(fileIdx) {
            return String.fromCharCode(96 + fileIdx); // 1->a
        },
        isSelected(rank, file) {
            return this.selectedSquare && this.selectedSquare.r === rank && this.selectedSquare.f === file;
        },
        isKingInCheck(rank, file) {
            if (!this.isCheck) return false;
            const piece = this.getPiece(rank, file);
            if (!piece) return false;
            // Check if it's the current turn's King
            // If turn is White, we look for 'K'. If Black, 'k'.
            const targetKing = this.game.current_turn === 'white' ? 'K' : 'k';
            return piece === targetKing;
        },
        isLastMove(rank, file) {
            if (!this.lastMove) return false;
            return (this.lastMove.from.r === rank && this.lastMove.from.f === file) ||
                   (this.lastMove.to.r === rank && this.lastMove.to.f === file);
        },
        getValidMoveType(rank, file) {
            if (!this.showHints) return null;
            const move = this.legalMoves.find(m => m.r === rank && m.f === file);
            return move ? (move.isCapture ? 'capture' : 'quiet') : null;
        },
        isValidMove(rank, file) {
             return !!this.getValidMoveType(rank, file);
        },
        toUCI(sq) {
            const files = "abcdefgh";
            return files[sq.f - 1] + sq.r;
        },
        uciToCoords(uci) {
             // e2e4 -> {from:{r:2,f:5}, to:{r:4,f:5}}
             if (!uci || uci.length < 4) return null;
             const files = "abcdefgh";
             const f1 = files.indexOf(uci[0]) + 1;
             const r1 = parseInt(uci[1]);
             const f2 = files.indexOf(uci[2]) + 1;
             const r2 = parseInt(uci[3]);
             return { from: {r:r1, f:f1}, to: {r:r2, f:f2} };
        },
        getUserRole() {
            if (!this.game || !this.currentUser) return 'Spectator';
            if (this.currentUser.id === this.game.white_player_id) return 'White';
            if (this.currentUser.id === this.game.black_player_id) return 'Black';
            return 'Spectator';
        },
        canMove() {
            if (!this.game || !this.currentUser) return false;
            if (this.game.status !== 'in_progress') return false;
            
            const isWhiteTurn = this.game.current_turn === 'white';
            const isWhitePlayer = this.currentUser.id === this.game.white_player_id;
            const isBlackPlayer = this.currentUser.id === this.game.black_player_id;

            if (isWhiteTurn && isWhitePlayer) return true;
            if (!isWhiteTurn && isBlackPlayer) return true;
            
            return false;
        },
        updateLegalMoves() {
            if (!this.selectedSquare) {
                this.legalMoves = [];
                return;
            }
            // Get moves for the selected square
            const fromSq = this.toUCI(this.selectedSquare).substring(0, 2); // e.g. "e2"
            const moves = this.chessInstance.moves({
                square: fromSq,
                verbose: true
            });
            
            // Map to coordinates {r, f}
            this.legalMoves = moves.map(m => {
                const target = m.to; // "e4"
                const files = "abcdefgh";
                const f = files.indexOf(target[0]) + 1;
                const r = parseInt(target[1]);
                const isCapture = m.flags.includes('c') || m.flags.includes('e');
                return { r, f, isCapture };
            });
        },
        handleSquareClick(rank, file) {
            if (!this.canMove()) return;

            const piece = this.getPiece(rank, file);
            const isOwnPiece = this.isOwnPiece(piece);
            
            if (this.selectedSquare) {
                // Deselect if clicking same
                if (this.selectedSquare.r === rank && this.selectedSquare.f === file) {
                    this.selectedSquare = null;
                    this.legalMoves = [];
                    return;
                }
                // Switch if clicking own
                if (isOwnPiece) {
                    this.selectedSquare = {r: rank, f: file};
                    this.updateLegalMoves();
                    return;
                }
                // Attempt Move
                this.makeMove(this.selectedSquare, {r: rank, f: file});
            } else {
                if (isOwnPiece) {
                    this.selectedSquare = {r: rank, f: file};
                    this.updateLegalMoves();
                }
            }
        },
        handleDragStart(rank, file, event) {
             if (!this.canMove()) {
                 event.preventDefault();
                 return;
             }
             const piece = this.getPiece(rank, file);
             if (!this.isOwnPiece(piece)) {
                 event.preventDefault();
                 return;
             }
             this.dragSource = {r: rank, f: file};
             this.selectedSquare = {r: rank, f: file};
             this.updateLegalMoves();
        },
        handleDrop(rank, file) {
            if (this.dragSource) {
                 this.makeMove(this.dragSource, {r: rank, f: file});
                 this.dragSource = null;
                 this.selectedSquare = null;
                 this.legalMoves = [];
            }
        },
        isOwnPiece(p) {
            if (!p) return false;
            const isWhitePiece = p === p.toUpperCase();
            return this.game.current_turn === 'white' ? isWhitePiece : !isWhitePiece;
        },
        async makeMove(from, to) {
            // 1. Validation Logic
            const fromSq = this.toUCI(from).substring(0, 2);
            const toSq = this.toUCI(to).substring(0, 2);
            
            // Check with chess.js
            // Note: We need to handle promotion. For simplicity, auto-queen if promotion available.
            // chess.js move() handles validation.
            
            // We can check if move is in .moves({square: fromSq})
            
            const potentialMoves = this.chessInstance.moves({ verbose: true });
            const moves = potentialMoves.filter(m => m.from === fromSq && m.to === toSq);
            
            if (moves.length === 0) {
                // Illegal move - Snap back / Do nothing
                console.warn("Illegal move attempted locally:", fromSq, toSq);
                this.selectedSquare = null;
                this.legalMoves = [];
                return;
            }

            // Default to Queen promotion if multiple moves (promotion) available
            let move = moves.find(m => m.promotion === 'q');
            if (!move) move = moves[0];

            // Construct UCI for backend
            let finalUci = move.from + move.to;
            if (move.promotion) {
                finalUci += move.promotion;
            }

            try {
                // Optimistic UI update could go here, but waiting for server is safer for now.
                
                const token = localStorage.getItem('token');
                await axios.post(`${API_BASE}/chess/${this.game.id}/move`, 
                    { move_uci: finalUci },
                    { headers: { Authorization: `Bearer ${token}` } }
                );
            } catch (e) {
                console.error(e);
                alert("Move failed: " + (e.response?.data?.detail || e.message));
            }
        },
        async undoMove() {
            if (!confirm("Are you sure you want to undo the last move?")) return;
            try {
                const token = localStorage.getItem('token');
                await axios.post(`${API_BASE}/chess/${this.game.id}/undo`, 
                    {},
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                // Frontend update will happen via WebSocket or we can force refetch
            } catch (e) {
                console.error("Undo failed", e);
                alert("Failed to undo move: " + (e.response?.data?.detail || e.message));
            }
        }
    }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

.chess-game-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
    min-height: 100vh;
}

@media (max-width: 600px) {
    .chess-game-container {
        padding: 0.5rem;
    }
}

.game-layout {
    display: flex;
    align-items: flex-start;
    gap: 2rem;
    justify-content: center;
    width: 100%;
    margin-top: 1rem;
}

@media (max-width: 900px) {
    .game-layout {
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
}

.captured-panel {
    width: 80px;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    padding: 1rem 0.5rem;
    align-items: center;
    background: rgba(255, 255, 255, 0.15);
}

@media (max-width: 900px) {
    .captured-panel {
        width: 100%;
        min-height: auto;
        flex-direction: row;
        padding: 0.5rem 1rem;
        justify-content: flex-start;
        overflow-x: auto;
    }
    
    .captured-panel h4 {
        margin-right: 1rem;
        margin-bottom: 0;
        font-size: 0.9rem;
        white-space: nowrap;
    }
}

.captured-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-top: 10px;
    align-items: center;
}

@media (max-width: 900px) {
    .captured-list {
        flex-direction: row;
        margin-top: 0;
        flex-wrap: wrap;
    }
}

.captured-piece {
    width: 40px;
    height: 40px;
}

.header { 
    width: 100%; 
    max-width: 600px;
}

.status-bar { 
    font-size: 1.2rem; 
    font-weight: 500; 
    margin-top: 0.5rem;
}
.text-primary { color: var(--primary); }
.text-secondary { color: var(--text-secondary); }
.text-accent { color: var(--accent); }

.board-wrapper {
    padding: 12px;
    background: linear-gradient(135deg, #4b3621 0%, #2c1e12 100%);
    border-radius: 6px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
    max-width: 100%;
}

.board {
    display: flex;
    flex-direction: column;
    width: min(90vw, 80vh, 600px);
    height: min(90vw, 80vh, 600px);
    user-select: none;
}

.rank {
    display: flex;
    flex: 1;
}

.square {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    cursor: default;
}

/* Colors based on standard brown board - slightly adjusted for contrast if needed */
.light-square { background-color: #f0d9b5; color: #b58863; }
.dark-square { background-color: #b58863; color: #f0d9b5; }

/* Coordinates */
.coord-rank {
    position: absolute;
    top: 2px;
    left: 4px;
    font-size: 0.8rem;
    font-weight: bold;
    pointer-events: none;
}
.coord-file {
    position: absolute;
    bottom: 0px;
    right: 4px;
    font-size: 0.8rem;
    font-weight: bold;
    pointer-events: none;
}
.coord-on-light { color: #b58863; }
.coord-on-dark { color: #f0d9b5; }

/* Selection & Highlights */
.square.selected {
    /* More visible highlight */
    box-shadow: inset 0 0 0 4px rgba(255, 255, 0, 0.8);
}
.square.in-check {
    box-shadow: inset 0 0 0 3px #ff4444, inset 0 0 20px rgba(255, 0, 0, 0.6);
    background-color: rgba(255, 0, 0, 0.15) !important;
    animation: check-pulse 1.5s ease-in-out infinite alternate;
}

@keyframes check-pulse {
    from {
        box-shadow: inset 0 0 0 2px #ff4444, inset 0 0 10px rgba(255, 0, 0, 0.4);
        background-color: rgba(255, 0, 0, 0.1);
    }
    to {
        box-shadow: inset 0 0 0 5px #ff0000, inset 0 0 25px rgba(255, 0, 0, 0.7);
        background-color: rgba(255, 0, 0, 0.25);
    }
}
.last-move-marker {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(155, 199, 0, 0.4); /* Greenish highlight */
    pointer-events: none;
}
/* Valid Move Marker - Small dot */
.valid-move-marker {
    position: absolute;
    width: 20%;
    height: 20%;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 50%;
    pointer-events: none;
}
.square:hover .valid-move-marker {
    background-color: rgba(0, 0, 0, 0.5);
}

/* Valid Capture Marker - Ring */
.valid-capture-marker {
    position: absolute;
    width: 85%;
    height: 85%;
    border: 6px solid rgba(0, 0, 0, 0.3);
    border-radius: 50%;
    pointer-events: none;
    z-index: 15; /* Above piece (z-index 10) */
}
.square:hover .valid-capture-marker {
    border-color: rgba(0, 0, 0, 0.5);
    background-color: rgba(0,0,0,0.1);
}


.piece-container {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10;
    cursor: grab;
    transition: transform 0.1s;
}
.piece-container:active { cursor: grabbing; transform: scale(1.1); }
.square[draggable=false] .piece-container { cursor: default; }

.error-msg {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-sm);
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.controls {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1rem;
    flex-wrap: wrap;
    align-items: center;
}

.btn-danger {
    margin-top: 0; /* Override */
}

.btn-undo {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: var(--text-primary);
    padding: 0.6rem 1.2rem;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s ease;
}

.btn-undo:hover {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
    border-color: var(--text-primary);
    transform: translateY(-2px);
}

.btn-undo svg {
    width: 20px;
    height: 20px;
}

.eval-bar-container {
    width: 100%;
    height: 12px;
    background-color: #333; /* Black side */
    border-radius: 6px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}

.eval-bar-fill {
    height: 100%;
    background-color: #eee; /* White side */
    transition: width 0.5s ease-in-out;
}

.toggle-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-right: 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
}
</style>
