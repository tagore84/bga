function ensurePlayerNames(state) {
    if (state && state.jugadores && typeof state.jugadores === 'object') {
        for (const [id, jugador] of Object.entries(state.jugadores)) {
            if (!('name' in jugador)) {
                jugador.name = null;
            }
            if (state.turno_actual === id) {
                state.turno_actual = jugador.name ?? id;
            }
        }
    }
}
