class ActionManager {

    constructor(rm, role, run_sound) {
        this.rm = rm;
        this.role = role;
        this.run_sound = run_sound;
        this.move_cycle_id = null;
        this.keys_dict = {
            KeyW: 0, ArrowUp: 0,
            KeyS: 0, ArrowDown: 0,
            KeyD: 0, ArrowRight: 0,
            KeyA: 0, ArrowLeft: 0
        }

        this.initKeyHandlers();
        this.startMoveCycle();
    }

    initKeyHandlers() {
        this.inlineKeyDownHandler = (event) => {
            if (event.repeat)
                return;
            
            if (event.code in this.keys_dict) {
                this.keys_dict[event.code] = 1;
                this.run_sound.play();
            }
            
            if (event.code == "Space")
                this.sendActionRequest();
        };

        this.inlineKeyUpHandler = (event) => {
            if (event.code in this.keys_dict)
                this.keys_dict[event.code] = 0;
            
            let n_key_down = 0;
            for (let code in this.keys_dict)
                n_key_down += this.keys_dict[code];

            if (n_key_down == 0)
                this.run_sound.pause();
        }

        document.addEventListener("keydown", this.inlineKeyDownHandler);
        document.addEventListener("keyup", this.inlineKeyUpHandler);

    }

    startMoveCycle() {
        this.move_cycle_id = setInterval(() => this.sendMovesRequest(), 50);
    }

    sendActionRequest() {
        const event_name = this.role == "vampire" ? "use_bats" : "use_torch";
        this.rm.emit(event_name);
    }

    sendMovesRequest() {
        const x_sum = this.keys_dict.KeyD + this.keys_dict.ArrowRight - this.keys_dict.KeyA - this.keys_dict.ArrowLeft;
        const y_sum = this.keys_dict.KeyS + this.keys_dict.ArrowDown - this.keys_dict.KeyW - this.keys_dict.ArrowUp;
        const x = x_sum < 0 ? -1 : (x_sum > 0 ? 1 : 0);
        const y = y_sum < 0 ? -1 : (y_sum > 0 ? 1 : 0);
        if (x != 0 || y != 0)
            this.rm.emit("move", {x, y});
    }

    destructor() {
        clearInterval(this.move_cycle_id);
        document.removeEventListener("keydown", this.inlineKeyDownHandler);
        document.removeEventListener("keyup", this.inlineKeyUpHandler);
    }
}