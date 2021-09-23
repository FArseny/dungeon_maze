const LOADING_ERROR_TEXT = "Error have occure while loading the game. Try again";
const OPPONENT_LEFT_TEXT = "Your opponent have left the game. Easy win! Keep it up!";


Vue.component("dungeon-field", {
    props: ["rm", "game_settings"],

    data() {
        return {
            conclusion: "",
            cooldown: 0,
            countdown_timer_id: null,
            countdown: null,
            game: null,
            picked_gold: false,
            state: "loading",  // loading -> game_starts -> ongoing  -> finished
            tool_total_recovery: 1,
            volume: 50,
            won: null
        };
    },

    created () {
        if (localStorage.getItem("volume") != null) {
            const value = localStorage.getItem("volume");
            if (isFinite(value)) {
                this.volume = Number(value);
            }
        }
    },

    mounted: function() {
        Promise.all([
            new Promise((resolve, reject) => this.loadImg("./static/img/floor_320.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/brick_x.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/brick_y.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/septum.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/gold_40.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/gold.svg", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/exit_up.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/exit_down.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/exit_right.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/exit_left.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/vamp_right.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/vamp_left.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/thief_right.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/thief_left.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/tracker.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/torch_left.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadImg("./static/img/torch_right.png", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/background.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/running.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/gold.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/vampire_laugh.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/radar_signal.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/torch.mp3", resolve, reject)),
            new Promise((resolve, reject) => this.loadSound("./static/sound/bats.mp3", resolve, reject))
        ]).then(
            (result) => {
                this.game = new Game(this.rm, this.game_settings);
                this.game.setMedia(result);
                this.tool_total_recovery = this.game_settings.tool_total_recovery * 100

                this.state = "game_starts";
                this.countdown = this.game_settings.game_start_delay;
                this.countdown_timer_id = setInterval(() => {
                    this.countdown -= 1;
                    if (this.countdown <= 0) {
                        clearInterval(this.countdown_timer_id);
                        this.countdown = 0;
                        this.countdown_timer_id = null;
                        this.state = "ongoing";
                        this.startGame();
                    }
                }, 1000);
            }
        ).catch(
            (error) => this.$emit("gameerror", error.message)
        );
    },

    methods: {

        loadImg(url, resolve, reject) {
            let img = new Image();
            img.src = url;
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error(LOADING_ERROR_TEXT));
        },

        loadSound(url, resolve, reject) {
            let sound = new Audio(url);
            sound.oncanplay = () => resolve(sound);
            sound.onerror = () => reject(new Error(LOADING_ERROR_TEXT));
            sound.load();
        },

        startGame() {
            this.game.initContext();
            this.game.initMoveManager();
            this.game.initSound(this.volume / 100);
            this.game.initDataCycle((data) => this.leftPanelCallback(data));
        },

        leftPanelCallback(data) {
            this.state = data.gs;

            if (this.game_settings.role == "thief" && this.state != "finished")
                this.picked_gold = data.pg

            if ("trl" in data) {
                const pass = this.tool_total_recovery - data.trl
                this.cooldown = Math.floor(100 * (pass / this.tool_total_recovery));
            }

            if (this.state == "finished")
                this.won = data.w == this.game.role;
                
            if (this.won) this.conclusion = "Well Done!";
            else this.conclusion = "Next time try run faster";
        },

        menuClickHandler() {
            this.$emit("backtomenu");
        },

        volumeChangedHandler(newValue) {
            this.game.changeVolume(newValue / 100);
            localStorage.setItem("volume", newValue);
        }
    },

    template: `
    <div class="dungeon-field-wrapper">

        <div v-if="state == 'loading'" class="load-wrapper">
            <div class="load-content dungeon-loader">
                <div class="load-bar load-bar-one"></div>
                <div class="load-bar load-bar-two"></div>
                <div class="load-bar load-bar-three"></div>
            </div>
        </div>

        <div v-if="state == 'game_starts'" class="popup-background">
            <div class="popup-window popup-window-countdown">
                <div class="popup-content popup-content-countdown">
                    <div class="popup-content-label">Game starts in {{ countdown }}</div>
                </div>
            </div>
        </div>

        <div v-if="state != 'loading'" class="dungeon-field-wrapper">

            <div class="dungeon-field-panel-left">
                <scroll :init_value="volume" @valuechanged="volumeChangedHandler"></scroll>
                <div :class="{'cooldown-line': true, 'bat-cooldown': game_settings.role == 'vampire', 'torch-cooldown': game_settings.role != 'vampire'}"
                     :style="{background: 'linear-gradient(to right, green ' + cooldown + '%, transparent 0%)' }"></div>
                <div v-if="game_settings.role == 'thief'" :class="{'gold-checkbox': true, 'gold-checkbox-chosen': picked_gold}">
                    <img src="./static/img/gold_40.png">
                </div>
                <div v-if="state == 'finished'" :class="{'conclusion-text': true, 'text-winner': won, 'text-looser': !won}">{{ conclusion }}</div>
                <div v-if="state == 'finished'" class="back-menu-button" @click="menuClickHandler">Back to menu</div>
            </div>

            <div class="dungeon-field-canvas-wrapper"
                        :style="{width: game_settings.field_size.width + 'px', height: game_settings.field_size.height + 'px'}">

                <canvas id="dungeon_floor_canvas"
                        :width="game_settings.field_size.width" :height="game_settings.field_size.height">
                </canvas>

                <canvas id="dungeon_fence_canvas"
                        :width="game_settings.field_size.width" :height="game_settings.field_size.height">
                </canvas>

                <canvas id="dungeon_main_canvas"
                        :width="game_settings.field_size.width" :height="game_settings.field_size.height">
                </canvas>

            </div>
        </div>
    </div>
    `
})