/**
 * Simulation WebSocket Client (Vanilla JS)
 * Adapted from use-simulation-websocket.ts
 * 
 * Manages WebSocket connection to FastAPI backend with auto-reconnect
 */

class SimulationWebSocket {
    constructor(options = {}) {
        this.url = options.url || 'ws://localhost:8000/ws';
        this.autoConnect = options.autoConnect !== false;
        this.reconnectDelay = options.reconnectDelay || 3000;
        this.onMessage = options.onMessage || null;
        this.onError = options.onError || null;
        this.onConnect = options.onConnect || null;
        this.onDisconnect = options.onDisconnect || null;

        this.ws = null;
        this.isConnected = false;
        this.lastUpdate = null;
        this.shouldReconnect = true;
        this.reconnectTimeout = null;

        if (this.autoConnect) {
            this.connect();
        }
    }

    connect() {
        try {
            console.log('[WebSocket] Connecting to:', this.url);
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[WebSocket] Connected');
                this.isConnected = true;
                if (this.onConnect) this.onConnect();
            };

            this.ws.onmessage = (event) => {
                try {
                    const update = JSON.parse(event.data);
                    this.lastUpdate = update;
                    if (this.onMessage) this.onMessage(update);
                } catch (err) {
                    console.error('[WebSocket] Failed to parse message:', err);
                }
            };

            this.ws.onerror = (event) => {
                console.error('[WebSocket] Error:', event);
                if (this.onError) this.onError(event);
            };

            this.ws.onclose = () => {
                console.log('[WebSocket] Disconnected');
                this.isConnected = false;
                this.ws = null;
                if (this.onDisconnect) this.onDisconnect();

                // Auto-reconnect if enabled
                if (this.shouldReconnect && this.autoConnect) {
                    console.log(`[WebSocket] Reconnecting in ${this.reconnectDelay}ms...`);
                    this.reconnectTimeout = setTimeout(() => {
                        this.connect();
                    }, this.reconnectDelay);
                }
            };
        } catch (err) {
            console.error('[WebSocket] Connection failed:', err);
        }
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[WebSocket] Cannot send - not connected');
        }
    }

    getLastUpdate() {
        return this.lastUpdate;
    }

    getConnectionStatus() {
        return this.isConnected;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimulationWebSocket;
}
