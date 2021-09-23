const RULE_TEXT_RU = "Воришка пробрался в подземелье вампира и хочет украсть его золото. Но чтобы это сделать, \
золото нужно сначала найти и уж потом донести его до выхода, желательно, не сталкиваясь со злым обитателем. \
Ходят слухи, что вампир настолько боится света, что даже не может близко подойти к сверкающему золоту или выходу из подземелья. \
Зная это, воршика купил себе факел на ближайшем рынке, жаль только он оказался бракованым и гаснет через секунду. \
У вампира же в логове живут летучие мыши, которые по команде легко могут определить местоположение нежелательного гостя, однако \
они летаю так громко, что выдают себя.";

const RULE_TEXT_EN = "Thief just get into vampire's dungeon to steal his gold. First he needs to find this gold \
and second - get out alive. There is gossip aroud: vampire fear of light so much, he can't even come close to the gold or dungeon exit. \
To be aware of it thief bought a torch in a market. It turned out the torch was broken and blows out after one second. \
There are bats in dungeon can help vampire to find out thief's location. But they fly so loudly so thief can easely hear them.";

const CONTROL_TEXT_RU = "Для управления используйте клавиши AWSD или стрелки влево/вверх/вниз/вправо, \
для использования способности (факел или вызов летучих мышей) нажмите клавишу 'Space'";

const CONTROL_TEXT_EN = "For movement use AWSD or left/up/down/right arrows. To use character ability (torch or bats help) \
press 'Space' button";

const CONTACTS_TEXT = "If you have any suggestions or you found a bug, please contact me on email: falkoarseny@gmail.com";


Vue.component("dungeon-menu", {
    props: ["popup_text"],
    data() {
        return {
            displayPopup: false,
            plainPopup: true,
            popupText: this.popup_text,
            rulesLanguage: "en",
            searchingGame: false,
            thiefChoose: true,
            vampireChoose:true,
            rulesText: RULE_TEXT_EN,
            controlText: CONTROL_TEXT_EN
        };
    },
    created: function() {
        if (this.popupText != null) {
            this.plainPopup = true;
            this.displayPopup = true;
        }
        
        if (localStorage.getItem("vampire_choose") != null) 
            this.vampireChoose = Boolean(localStorage.getItem("vampire_choose"));
        
        if (localStorage.getItem("thief_choose") != null) 
            this.thiefChoose = Boolean(localStorage.getItem("thief_choose"));

        if (localStorage.getItem("language") != null) {
            this.rulesLanguage = localStorage.getItem("language");
            this.changeLanguage();
        }
    },
    methods : {

        findGameHandler() {
            if (!this.vampireChoose && !this.thiefChoose)
                return;
            
            this.searchingGame = true;
            this.rm = new RequestManager({ 
                vampire: this.vampireChoose,
                thief: this.thiefChoose
            },
            (rm, settings) => this.$emit("gamefound", rm, settings));
        },

        stopSearchRequest() {
            this.rm.disconnect();
            this.searchingGame = false;
        },

        checkboxHandler(value) {
            if (value == 'vampire') {
                this.vampireChoose = !this.vampireChoose;
                localStorage.setItem("vampire_choose", this.vampireChoose ? "1" : "");
            } else {
                this.thiefChoose = !this.thiefChoose;
                localStorage.setItem("thief_choose", this.thiefChoose ? "1" : "");
            }
        },

        rulesClickHandler() {
            this.displayPopup = true;
            this.plainPopup = false;
        },

        contactClickHandler() {
            this.displayPopup = true;
            this.plainPopup = true;
            this.popupText = CONTACTS_TEXT;
        },

        hidePopupHandler() {
            this.plainPopup = true;
            this.displayPopup = false;
        },

        changeLanguageHandler(language) {
            this.rulesLanguage = language;
            localStorage.setItem("language", this.rulesLanguage);
            this.changeLanguage();
        },

        changeLanguage() {
            this.rulesText = this.rulesLanguage == "en" ? RULE_TEXT_EN : RULE_TEXT_RU;
            this.controlText = this.rulesLanguage == "en" ? CONTROL_TEXT_EN : CONTROL_TEXT_RU;
        }
    },
    template : `
    <div class="dungeon-menu-wrapper">
        <div class="dungeon-menu">
            <p class="dungeon-menu-title">Vampire & Thief</p>
            <p class="dungeon-role-title">Wished role : </p>
            <p :class="{'dungeon-role': true, 'checkbox-role-chosen': vampireChoose}" @click="checkboxHandler('vampire')">Vampire</p>
            <p :class="{'dungeon-role': true, 'checkbox-role-chosen': thiefChoose}" @click="checkboxHandler('thief')">Thief</p>
            <p :class="{'dungeon-role-hint': true, 'hint-visible': !(vampireChoose || thiefChoose)}">Choose at least one role</p>
            <div class="button-wrapper">
                <div :class="{'find-game-button': true, 'button-correct': vampireChoose || thiefChoose, 'button-disabled': !(vampireChoose || thiefChoose)}"
                    @click="findGameHandler">Find game</div>
            </div>
            <div class="dungeon-menu-bottom-panel">
                <div class="dungeon-menu-rules" @click="rulesClickHandler">rules</div>
                <div class="dungeon-menu-contact" @click="contactClickHandler">contacts</div>
            </div>
        </div>
        <div v-if="displayPopup" class="popup-background" @click="hidePopupHandler">
            <div class="popup-window">
                <div class="popup-content" @click.stop>
                    <p v-if="plainPopup" class="popup-content-text">{{ popupText }}</p>
                    <div v-if="!plainPopup" class="rules-wrapper">
                        <div class="language-wrapper">
                            <div :class="{'language-option': true, 'language-active-option': rulesLanguage == 'en'}"
                                 @click="changeLanguageHandler('en')">
                                Eng
                            </div>
                            <div :class="{'language-option': true, 'language-active-option': rulesLanguage == 'ru'}"
                                  @click="changeLanguageHandler('ru')">
                                Ru
                            </div>
                        </div>
                        <p>{{ rulesText }}</p>
                        <p>{{ controlText }}</p>
                    </div>
                    <div class="popup-close" @click="hidePopupHandler"></div>
                </div>
            </div>
        </div>
        <div v-if="searchingGame" class="popup-background">
            <div class="popup-window">
                <div class="popup-content">
                    <div class="popup-content-title">Looking for opponent</div>
                    <div class="load-wrapper">
                        <div class="load-content">
                            <div class="load-bar load-bar-one"></div>
                            <div class="load-bar load-bar-two"></div>
                            <div class="load-bar load-bar-three"></div>
                        </div>
                    </div>
                    <div class="stop-button" @click="stopSearchRequest">Stop search</div>
                </div>
            </div>
        </div>
    </div>
    `
})