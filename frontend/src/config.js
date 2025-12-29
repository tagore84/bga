// Centralized configuration for API URLs

// Determine the backend URL dynamically based on the current hostname.
// This works for both local development (localhost) and NAS deployment (NAS IP).
// It assumes the backend is always running on port 8000.

const hostname = window.location.hostname;
const protocol = window.location.protocol;

export const API_BASE = `${protocol}//${hostname}:8000`;
export const WS_BASE = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${hostname}:8000`;
