class RequestManager {
    
    constructor(options, fond_game_cb) {
        this.fond_game_cb = fond_game_cb;
        this.socket = io.connect()

        this.socket.on('connect', () => this.socket.emit("find_game", {
                vampire: options.vampire,
                thief: options.thief
        }));

        this.socket.on('found_game', (settings) => {
            this.fond_game_cb(this, settings);
        })
    }

    emit(event, message) {
        this.socket.emit(event, message);
    }

    listen(event, cb) {
        this.socket.on(event, cb);
    }

    disconnect() {
        this.socket.close();
    }

}