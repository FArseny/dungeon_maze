const app = new Vue({
    el: "#app",
    data: {
        gameSettings: null,
        popupText: null,
        requestManager: null,
        state: "MAIN_MENU" // MAIN_MENU, GAME_READY
    },
    methods: {
        gameFoundHandler(requestManager, game_settings) {
            this.state = "GAME_READY";
            this.popupText = null;
            this.requestManager = requestManager;
            this.gameSettings = game_settings
        },

        gameErrHandler(text) {
            this.requestManager.disconnect();
            this.popupText = text;
            this.state = "MAIN_MENU";
        },

        backToMenuHandler() {
            this.state = "MAIN_MENU";
        }
    }
})
