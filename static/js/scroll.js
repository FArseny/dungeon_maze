Vue.component("scroll", {
    props: ["init_value"],

    data() {
        return {
            value: this.init_value,
            wheelBaseOffset: -8,
            wheelOffset: 0,
            lastMouseOffset: 0
        }
    },

    created() {

        this.inlineMouseMoveHandler = (event) => {
            const dif = event.clientX - this.lastMouseOffset;
            this.lastMouseOffset = event.clientX;
            let newValue = this.value + dif;
            if (newValue < 0) newValue = 0
            if (newValue > 100) newValue = 100
            this.changeScrollPostion(newValue)
        }

        this.inlineMouseUpHandler = (event) => {
            document.removeEventListener("mousemove", this.inlineMouseMoveHandler);
            document.removeEventListener("mouseup", this.inlineMouseUpHandler);
        }

        if (this.value < 0) this.value = 0;
        if (this.value > 100) this.value = 100;
        this.wheelOffset = this.value + this.wheelBaseOffset;
    },

    methods: {

        changeScrollPostion(newValue) {
            if (this.value == newValue)
                return;

            this.value = newValue
            this.wheelOffset = this.value + this.wheelBaseOffset;
            this.$emit("valuechanged", newValue);
        },
        
        wheelMouseDownHandler(event) {
            this.lastMouseOffset = event.clientX;
            document.addEventListener("mousemove", this.inlineMouseMoveHandler);
            document.addEventListener("mouseup", this.inlineMouseUpHandler);
        },

        scrollClickHandler(event) {
            if (event.offsetX < 0)
                return;
            this.changeScrollPostion(event.offsetX);
            this.lastMouseOffset = event.clientX;
        }

    },

    template: `
        <div class="scroll-wrapper">
            <div class="scroll-panel" @click="scrollClickHandler">
                <div class="scroll-wheel" :style="{left: wheelOffset + 'px'}" @mousedown.stop="wheelMouseDownHandler" @click.stop></div>
            </div>
        </div>
    `
});