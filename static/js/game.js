const LAUGH_PLAY_INTERVAL_SECONDS = 20;
const PICKED_GOLD_SIZE = 16


class Vector {

    constructor(x=0, y=0) {
        this.x = x;
        this.y = y;
    }
}


class Rectangular {
    
    constructor(width, height) {
        this.w = width;
        this.h = height;
    }
}


class Field {

    constructor(data) {
        this.SIZE          = new Rectangular(data.field_size.width, data.field_size.height);
        this.SIZE_IN_TILES = new Rectangular(data.field_size_in_tiles.width, data.field_size_in_tiles.height);
        this.TILE_SIZE     = data.tile_size;
        this.SEPTUM_SIZE   = data.septum_size;
        this.GOLD_SIZE     = data.gold_size;
        this.TRACKER_SIZE  = data.tracker_size;
        this.BRICK_SIZE    = new Rectangular(data.brick_size.width, data.brick_size.height);
        this.FENCE_SIZE    = new Rectangular(data.fence_size.width, data.fence_size.height);
        this.EXIT_SIZE     = new Rectangular(data.exit_size.width,  data.exit_size.height);
        this.N_BRICK_LAYER = 2;
        this.TILES_IN_IMG  = 4;
        this.FLOOR_TOP_LEFT  = new Vector(2 * this.BRICK_SIZE.h, 2 * this.BRICK_SIZE.h);
        this.FLOOR_BOT_RIGHT = new Vector(this.FLOOR_TOP_LEFT.x + this.SIZE_IN_TILES.w * this.TILE_SIZE,
                                          this.FLOOR_TOP_LEFT.y + this.SIZE_IN_TILES.h * this.TILE_SIZE);
    }
}


class Game {

    constructor(rm, data) {
        this.rm = rm;
        this.field = new Field(data);

        this.role       = data.role;
        this.char_pos   = new Vector(data.p.x, data.p.y);
        this.last_move  = 1  // move direction: -1 left; 1 right
        this.enemy_role = this.role == "vampire" ? "thief" : "vampire";
        this.enemy_pos  = null;
        this.enemy_last_move = 1;
        this.gold_tile  = null;
        this.exit_drew  = false;
        this.v_fence    = Array(this.field.SIZE_IN_TILES.h).fill(0).map(() => Array(this.field.SIZE_IN_TILES.w - 1).fill(0));
        this.h_fence    = Array(this.field.SIZE_IN_TILES.h - 1).fill(0).map(() => Array(this.field.SIZE_IN_TILES.w).fill(0));
        this.view_dist  = 1;
        this.status     = "waiting";
        this.picked_gold    = false;
        this.using_torch    = false;
        this.action_manager = null;
        this.data_cycle_id  = null;
        this.left_panel_cb  = null;
        this.enemy_using_torch    = false;
        this.enemy_picked_gold    = false;
        this.last_time_laugh_play = 0;
    }

    setMedia(media) {
        this.imgs = {};
        this.sounds = {};
        [
            this.imgs.tiles, this.imgs.brick_x, this.imgs.brick_y,
            this.imgs.septum, this.imgs.gold, this.imgs.gold_mini,
            this.imgs.exit_up, this.imgs.exit_down, this.imgs.exit_right,
            this.imgs.exit_left, this.imgs.vamp_right, this.imgs.vamp_left,
            this.imgs.thief_right, this.imgs.thief_left, this.imgs.tracker,
            this.imgs.torch_left, this.imgs.torch_right, this.sounds.background,
            this.sounds.running, this.sounds.gold, this.sounds.vampire_laugh,
            this.sounds.radar, this.sounds.torch, this.sounds.bats
        ] = media;
    }

    initContext() {
        this.ctx_1 = document.getElementById("dungeon_floor_canvas").getContext("2d");
        this.ctx_2 = document.getElementById("dungeon_fence_canvas").getContext("2d");
        this.ctx_3 = document.getElementById("dungeon_main_canvas").getContext("2d");

        this.renderFloor();
        this.renderWall();
        this.renderSeptum();
    }

    initMoveManager() {
        this.action_manager = new ActionManager(this.rm, this.role, this.sounds.running);
    }

    initSound(volume) {
        for (let sound of Object.values(this.sounds))
            sound.volume = volume;
        this.sounds.background.loop = true;
        this.sounds.running.loop = true;
        this.sounds.radar.loop = true;
        this.sounds.background.play();
    }

    initDataCycle(left_panel_cb) {
        this.left_panel_cb = left_panel_cb;
        this.status = "ongoing";
        this.rm.listen("new_info", (data) => this.setFreshData(data));
        this.data_cycle_id = setInterval(() =>  this.rm.emit("get_info", {}), 50);
    }

    renderWall() {
        let cur_x = 0, cur_y = 0;

        // fill first column
        while(cur_y < this.field.SIZE.h) {
            this.ctx_1.drawImage(this.imgs.brick_y, cur_x, cur_y);
            cur_y += this.field.BRICK_SIZE.w;
        }

        // fill second column
        cur_x = this.field.BRICK_SIZE.h;
        cur_y = Math.round(-this.field.BRICK_SIZE.w/2);
        while(cur_y < this.field.SIZE.h) {
            this.ctx_1.drawImage(this.imgs.brick_y, cur_x, cur_y);
            cur_y += this.field.BRICK_SIZE.w;
        }

        // fill last row
        cur_x = 0;
        cur_y = this.field.SIZE.h - this.field.BRICK_SIZE.h;
        while(cur_x < this.field.SIZE.w) {
            this.ctx_1.drawImage(this.imgs.brick_x, cur_x, cur_y);
            cur_x += this.field.BRICK_SIZE.w;
        }

        // fill second to last row
        cur_x = Math.round(-this.field.BRICK_SIZE.w/2);
        cur_y = this.field.SIZE.h - 2 * this.field.BRICK_SIZE.h;
        while(cur_x < this.field.SIZE.w) {
            this.ctx_1.drawImage(this.imgs.brick_x, cur_x, cur_y);
            cur_x += this.field.BRICK_SIZE.w;
        }

        // fill last column
        cur_x = this.field.SIZE.w - this.field.BRICK_SIZE.h;
        cur_y = 0;
        while(cur_y < this.field.SIZE.h) {
            this.ctx_1.drawImage(this.imgs.brick_y, cur_x, cur_y);
            cur_y += this.field.BRICK_SIZE.w;
        }

        // fill second to last column
        cur_x = this.field.SIZE.w - 2 * this.field.BRICK_SIZE.h;
        cur_y = Math.round(-this.field.BRICK_SIZE.w/2);
        while(cur_y < this.field.SIZE.h) {
            this.ctx_1.drawImage(this.imgs.brick_y, cur_x, cur_y);
            cur_y += this.field.BRICK_SIZE.w;
        }

        // fill first row
        cur_x = 2 * this.field.BRICK_SIZE.h;
        cur_y = 0;
        while(cur_x < this.field.SIZE.w) {
            this.ctx_1.drawImage(this.imgs.brick_x, cur_x, cur_y);
            cur_x += this.field.BRICK_SIZE.w;
        }

        // fill second row
        cur_x = 2 * this.field.BRICK_SIZE.h - Math.round(this.field.BRICK_SIZE.w / 2);
        cur_y = this.field.BRICK_SIZE.h;
        while(cur_x < this.field.SIZE.w) {
            this.ctx_1.drawImage(this.imgs.brick_x, cur_x, cur_y);
            cur_x += this.field.BRICK_SIZE.w;
        }
    }

    renderFloor() {
        for(let row = 0; row < this.field.SIZE_IN_TILES.h; row += this.field.TILES_IN_IMG) {
            for (let column = 0; column < this.field.SIZE_IN_TILES.w; column += this.field.TILES_IN_IMG) {
                const x = this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE;
                const y = this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE;
                this.ctx_1.drawImage(this.imgs.tiles, x, y);
            }
        }
        
    }

    renderSeptum() {
        for(let row = 1; row < this.field.SIZE_IN_TILES.h; row += 1) {
            for (let column = 1; column < this.field.SIZE_IN_TILES.w; column += 1) {
                const x = this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE - this.field.SEPTUM_SIZE / 2;
                const y = this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE - this.field.SEPTUM_SIZE / 2;
                this.ctx_1.drawImage(this.imgs.septum, x, y);
            }
        }
    }

    drawExit(column, row) {
        const half_exit_width = Math.floor(this.field.EXIT_SIZE.w / 2);
        const half_tile_size  = Math.floor(this.field.TILE_SIZE / 2);

        if (row == 0)
            this.ctx_1.drawImage(
                this.imgs.exit_up,
                this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE + half_tile_size - half_exit_width,
                this.field.FLOOR_TOP_LEFT.y - this.field.EXIT_SIZE.h
            );
        else if (row == this.field.SIZE_IN_TILES.h - 1)
            this.ctx_1.drawImage(
                this.imgs.exit_down,
                this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE + half_tile_size - half_exit_width,
                this.field.FLOOR_BOT_RIGHT.y + 1
            );
        else if (column == 0)
            this.ctx_1.drawImage(
                this.imgs.exit_left,
                this.field.FLOOR_TOP_LEFT.x - this.field.EXIT_SIZE.h,
                this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE + half_tile_size - half_exit_width
            );
        else
            this.ctx_1.drawImage(
                this.imgs.exit_right,
                this.field.FLOOR_BOT_RIGHT.x + 1,
                this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE + half_tile_size - half_exit_width
            );
        
        this.exit_drew = true;
    }

    setFreshData(data) {
        this.setFence(data.vf, data.hf)
        this.view_dist = data.vd;
        this.gold_tile = "gt" in data ? new Vector(data.gt.x, data.gt.y) : null;

        [this.char_pos.x, this.char_pos.y] = [data.p.x, data.p.y];
        this.last_move = data.lm;
        this.refreshCharTilePos();

        this.picked_gold = "pg" in data && data["pg"]
        this.enemy_picked_gold = "epg" in data && data["epg"]

        if ("ep" in data && !("bat" in data)) {
            this.enemy_pos = new Vector(data.ep.x, data.ep.y);
            this.enemy_last_move = data.elm;
        } else this.enemy_pos = null;
        
        if ("ut" in data && data.ut) { 
            this.using_torch = true
            this.sounds.torch.play();
        } else
            this.using_torch = false;
        
        if ("eut" in data && data.eut) {
            this.enemy_using_torch = true
            this.sounds.torch.play();
        } else
            this.enemy_using_torch = false;

        if (!this.exit_drew && "et" in data)
            this.drawExit(data.et.x, data.et.y);
        
        if (data.gs == "finished")
            this.finishGame();
        
        this.left_panel_cb(data);
        this.renderField();

        if ("bat" in data && data.gs != "finished")
            this.showEnemyPosByBats(data.ep, data.bat);
        else {
            this.sounds.radar.pause();
            this.sounds.radar.currentTime = 0;
        }
        
        if ("jpg" in data && data.jpg)
            this.sounds.gold.play();
        
        if ("eba" in data && data.eba)
            this.sounds.bats.play();
        
        const cur_time = Math.round( Date.now() / 1000);
        if (this.role == "thief" && "ep" in data && this.status != "finished" &&
            cur_time - this.last_time_laugh_play >= LAUGH_PLAY_INTERVAL_SECONDS) {
            this.sounds.vampire_laugh.play();
            this.last_time_laugh_play = cur_time;
        }
    }

    finishGame() {
        this.action_manager.destructor();
        clearInterval(this.data_cycle_id);
        clearTimeout(this.last_time_laugh_play);
        this.rm.disconnect();
        this.status = "finished";
        for (let sound of Object.values(this.sounds))
            sound.pause();
    }

    calcTileByCoord(x, y) {
        const column = Math.floor((x - this.field.FLOOR_TOP_LEFT.x) / this.field.TILE_SIZE);
        const row    = Math.floor((y - this.field.FLOOR_TOP_LEFT.y) / this.field.TILE_SIZE);
        return new Vector(column, row);
    }

    changeVolume(volume) {
        for (let sound of Object.values(this.sounds)) 
            sound.volume = volume;
    }

    refreshCharTilePos() {
        this.char_tile = this.calcTileByCoord(this.char_pos.x, this.char_pos.y);
    }

    setFence(v_bit_fence, h_bit_fence) {
        const v_fence = this.getFenceFromBits(v_bit_fence, this.field.SIZE_IN_TILES.w - 1);
        const h_fence = this.getFenceFromBits(h_bit_fence, this.field.SIZE_IN_TILES.w);

        let changed = false;
        for (let row = 0; row < this.field.SIZE_IN_TILES.h; row++){
            for (let column = 0; column < this.field.SIZE_IN_TILES.w - 1; column++) {
                if (this.v_fence[row][column] != v_fence[row][column]) {
                    changed = true;
                    this.v_fence[row][column] = v_fence[row][column];
                }
            }
        }

        for (let row = 0; row < this.field.SIZE_IN_TILES.h - 1; row++){
            for (let column = 0; column < this.field.SIZE_IN_TILES.w; column++) {
                if (this.h_fence[row][column] != h_fence[row][column]) {
                    changed = true;
                    this.h_fence[row][column] = h_fence[row][column];
                }
            }
        }

        if (changed)
            this.showFence();
    }

    getFenceFromBits(bf, second_d_size) {
        let fence = []
        for (let row_v of bf) {
            let row = []
            let bit_val = 1
            for (let bit = 0; bit < second_d_size; bit++) {
                const res = (bit_val & row_v) > 0 ? 1 : 0;
                row.push(res);
                bit_val *= 2;
            }
            row.reverse();
            fence.push(row);
        }
        return fence;
    }

    showFence() {
        this.ctx_2.clearRect(0, 0, this.field.SIZE.w, this.field.SIZE.h);
        this.ctx_2.fillStyle = "#bb7b26";

        for (let row = 0; row < this.field.SIZE_IN_TILES.h; row++){
            for (let column = 0; column < this.field.SIZE_IN_TILES.w - 1; column++) {
                if (this.v_fence[row][column] == 0)
                    continue;
                
                let x = this.field.FLOOR_TOP_LEFT.x + (column + 1) * this.field.TILE_SIZE - Math.floor(this.field.FENCE_SIZE.h / 2);
                let y = this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE;
                if (row > 0) y += Math.floor(this.field.SEPTUM_SIZE / 2);
                let height = this.field.FENCE_SIZE.w;
                if (row == 0 || row == this.field.SIZE_IN_TILES.h - 1)
                    height += Math.floor(this.field.SEPTUM_SIZE / 2);
                this.ctx_2.fillRect(x, y, this.field.FENCE_SIZE.h, height);
            }
        }

        for (let row = 0; row < this.field.SIZE_IN_TILES.h - 1; row++){
            for (let column = 0; column < this.field.SIZE_IN_TILES.w; column++) {
                if (this.h_fence[row][column] == 0)
                    continue;
                
                let x = this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE;
                if (column > 0) x += Math.floor(this.field.SEPTUM_SIZE / 2);
                let y = this.field.FLOOR_TOP_LEFT.y + (row + 1) * this.field.TILE_SIZE - Math.floor(this.field.FENCE_SIZE.h / 2);
                let width = this.field.FENCE_SIZE.w;
                if (column == 0 || column == this.field.SIZE_IN_TILES.w - 1)
                    width += Math.floor(this.field.SEPTUM_SIZE / 2);
                this.ctx_2.fillRect(x, y, width, this.field.FENCE_SIZE.h);
            }
        }

    }

    renderField() {
        this.ctx_3.clearRect(0, 0, this.field.SIZE.w, this.field.SIZE.h);

        if (this.gold_tile != null) {
            const offset = Math.floor(this.field.TILE_SIZE / 2) - Math.floor(this.field.GOLD_SIZE / 2);
            this.ctx_3.drawImage(
                this.imgs.gold,
                this.field.FLOOR_TOP_LEFT.x + this.gold_tile.x * this.field.TILE_SIZE + offset,
                this.field.FLOOR_TOP_LEFT.y + this.gold_tile.y * this.field.TILE_SIZE + offset)
        }

        if (this.status != "finished")
            this.renderShadows()

        this.showCharacter(this.char_pos, this.last_move, this.role, this.using_torch, this.picked_gold);
        if (this.enemy_pos)
            this.showCharacter(this.enemy_pos, this.enemy_last_move, this.enemy_role, this.enemy_using_torch,
                               this.enemy_picked_gold);
    }

    showCharacter(pos, last_move, role, using_torch, picked_gold) {
        if (role == "vampire") {
            const img = last_move == 1 ? this.imgs.vamp_right : this.imgs.vamp_left;
            this.ctx_3.drawImage(img, Math.round(pos.x - img.width / 2), Math.round(pos.y - img.height / 2));
        } else {
            const img = last_move == 1 ? this.imgs.thief_right : this.imgs.thief_left;
            this.ctx_3.drawImage(img, Math.round(pos.x - img.width / 2), Math.round(pos.y - img.height / 2));
        }

        if (picked_gold) {
            
            if (last_move == 1) this.ctx_3.drawImage(this.imgs.gold_mini, pos.x - 4, pos.y - 2, PICKED_GOLD_SIZE, PICKED_GOLD_SIZE);
            else this.ctx_3.drawImage(this.imgs.gold_mini, pos.x - 12, pos.y - 2, PICKED_GOLD_SIZE, PICKED_GOLD_SIZE);
        }

        if (using_torch) {
            if (last_move == 1) this.ctx_3.drawImage(this.imgs.torch_right, pos.x - 2, pos.y - 15);
            else this.ctx_3.drawImage(this.imgs.torch_left, pos.x - 28, pos.y - 15);
        }
    }

    showEnemyPosByBats(enemy_pos, active_time) {
        const FREQ_SHOW = 2;
        if (Math.floor(active_time * FREQ_SHOW) % 2) {
            const tracker_hals_size = this.field.TRACKER_SIZE / 2;
            this.ctx_3.drawImage(
                this.imgs.tracker,
                enemy_pos.x - tracker_hals_size,
                enemy_pos.y - tracker_hals_size);
        }
        this.sounds.radar.play();
    }


    renderShadows() {
        for (let i = 0;i < this.field.SIZE_IN_TILES.h; i++) {
            for (let j = 0;j < this.field.SIZE_IN_TILES.w; j++) {
                if (j == this.char_tile.x && i == this.char_tile.y)
                    continue;

                if (j == this.char_tile.x) {
                    let dist = i - this.char_tile.y;
                    let have_fence = false;
                    if (dist > 0) {
                        while(dist > 0) {
                            have_fence = have_fence || this.h_fence[this.char_tile.y + dist - 1][this.char_tile.x] == 1;
                            dist--;
                        }
                    } else {
                        while(dist < 0) {
                            have_fence = have_fence || this.h_fence[this.char_tile.y + dist][this.char_tile.x] == 1;
                            dist++;
                        }
                    }
                    if (!have_fence && Math.abs(i - this.char_tile.y) <= this.view_dist)
                        continue;
                }

                if (i == this.char_tile.y) {
                    let dist = j - this.char_tile.x;
                    let have_fence = false;
                    if (dist > 0) {
                        while(dist > 0) {
                            have_fence = have_fence || this.v_fence[this.char_tile.y][this.char_tile.x + dist - 1] == 1;
                            dist--;
                        }
                    } else {
                        while(dist < 0) {
                            have_fence = have_fence || this.v_fence[this.char_tile.y][this.char_tile.x + dist] == 1;
                            dist++;
                        }
                    }
                    if (!have_fence && Math.abs(j - this.char_tile.x) <= this.view_dist)
                        continue;
                }

                this.shadowTile(i, j);
            }
        }
    }


    shadowTile(row, column) {
        // reserve one more shadow space to sure shadow full tile
        const SEPTUM_SIZE_HALF = this.field.SEPTUM_SIZE / 2 - 1;

        this.ctx_3.fillStyle = "rgba(0, 0, 0, 0.65)";

        this.ctx_3.beginPath();
        let x_cur = this.field.FLOOR_TOP_LEFT.x + column * this.field.TILE_SIZE;
        let y_cur = this.field.FLOOR_TOP_LEFT.y + row * this.field.TILE_SIZE;

        if (row > 0 && column > 0) { x_cur += SEPTUM_SIZE_HALF; }
        this.ctx_3.moveTo(x_cur, y_cur);

        x_cur += row > 0 && column > 0 ? this.field.TILE_SIZE - SEPTUM_SIZE_HALF : this.field.TILE_SIZE;
        if (row > 0 && column < this.field.SIZE_IN_TILES.w - 1) {
            x_cur -= SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            y_cur += SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            x_cur += SEPTUM_SIZE_HALF;
        }
        this.ctx_3.lineTo(x_cur, y_cur);

        y_cur += (row > 0 && column < this.field.SIZE_IN_TILES.w - 1 ?
                  this.field.TILE_SIZE - SEPTUM_SIZE_HALF : this.field.TILE_SIZE);
        if (row < this.field.SIZE_IN_TILES.h - 1 && column < this.field.SIZE_IN_TILES.w- 1) {
            y_cur -= SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            x_cur -= SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            y_cur += SEPTUM_SIZE_HALF;
        }
        this.ctx_3.lineTo(x_cur, y_cur);

        x_cur -= (row < this.field.SIZE_IN_TILES.h - 1 && column < this.field.SIZE_IN_TILES.w - 1 ?
                  this.field.TILE_SIZE - SEPTUM_SIZE_HALF : this.field.TILE_SIZE);
        if (row < this.field.SIZE_IN_TILES.h - 1 && column > 0) {
            x_cur += SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            y_cur -= SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            x_cur -= SEPTUM_SIZE_HALF;
        }
        this.ctx_3.lineTo(x_cur, y_cur);

        y_cur -= (row < this.field.SIZE_IN_TILES.h - 1 && column > 0 ?
                  this.field.TILE_SIZE - SEPTUM_SIZE_HALF : this.field.TILE_SIZE);
        if (row > 0 && column > 0) {
            y_cur += SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            x_cur += SEPTUM_SIZE_HALF;
            this.ctx_3.lineTo(x_cur, y_cur);
            y_cur -= SEPTUM_SIZE_HALF;
        }
        this.ctx_3.lineTo(x_cur, y_cur);

        this.ctx_3.closePath();
        this.ctx_3.fill();
    }

}
