from time import time
from enum import Enum, auto
from tools import Vector, Rectangular, RecoveryTool
import random



class GameStatus(Enum):
    WAITING = auto()
    ONGOING = auto()
    FINISHED = auto()



class CharacterType(Enum):
    VAMPIRE = auto()
    THIEF = auto()



class Character:

    MODEL_SIZE_HEIGHT = 30
    MODEL_SIZE_WIDTH  = 22
    
    def __init__ (self, game, user_sid, position):
        self.game      = game
        self.user_sid   = user_sid
        self.position  = position
        self.tile_pos  = game.calcTile(position.x, position.y)
        self.last_move = 1          # move direction: -1 left; 1 right
        self.v_fence   = [[0] * (Game.FIELD_SIZE_IN_TILES.w - 1) for i in range(Game.FIELD_SIZE_IN_TILES.h)]
        self.h_fence   = [[0] * Game.FIELD_SIZE_IN_TILES.w for i in range(Game.FIELD_SIZE_IN_TILES.h - 1)]
        self.saw_exit  = False
        self.saw_gold  = False
        self.enemy     = None
        self.see_enemy = False
        self.view_dist = 1
        self.online    = True
    

    def setEnemy(self, enemy):
        self.enemy = enemy


    def tryMove(self, vector):
        move_made = False
        if vector.x != 0: move_made = self.tryMoveOneAxis(Vector(vector.x, 0))
        if vector.y != 0: move_made = self.tryMoveOneAxis(Vector(0, vector.y)) or move_made

        if not move_made:
            return False
        
        self.tile_pos = self.game.calcTile(self.position.x, self.position.y)
        return True


    def tryMoveOneAxis(self, vector, steps=[3, 1]):
        for step in steps:
            if self.canMoveTo(self.position.x + step * vector.x, self.position.y + step * vector.y):
                if (vector.x != 0): self.last_move = vector.x
                self.position.x += step * vector.x
                self.position.y += step * vector.y
                return True
        return False
    

    def canMoveTo(self, x, y):
        char_rect = Rectangular(Character.MODEL_SIZE_WIDTH,
                                      Character.MODEL_SIZE_HEIGHT)
        char_rect.setByTopLeft(x - Character.MODEL_SIZE_WIDTH / 2,
                                     y - Character.MODEL_SIZE_HEIGHT / 5)

        if (char_rect.tl.x < self.game.FLOOR_TOP_LEFT.x or
            char_rect.tl.y < self.game.FLOOR_TOP_LEFT.y or
            char_rect.br.x > self.game.FLOOR_BOT_RIGHT.x or
            char_rect.br.y > self.game.FLOOR_BOT_RIGHT.y):
            return False
        
        for septum in self.game.septum_models:
            if char_rect.isIntersectWith(septum):
                return False
        
        for i_row, row in enumerate(self.game.v_fence):
            for i_col, v in enumerate(row):
                if v == 1 and char_rect.isIntersectWith(self.game.v_fence_model[i_row][i_col]):
                    return False
        
        for i_row, row in enumerate(self.game.h_fence):
            for i_col, v in enumerate(row):
                if v == 1 and char_rect.isIntersectWith(self.game.h_fence_model[i_row][i_col]):
                    return False

        return True

    
    def checkVisability(self):
        self.see_enemy = False
        self.refreshTileVisability(self.tile_pos)

        true_v_fence, true_h_fence = self.game.v_fence, self.game.h_fence
        for cur_dist in range(1, self.view_dist + 1):
            
            have_fence, i = False, 1
            while(i <= cur_dist and self.tile_pos.x - i >= 0):
                have_fence |= true_v_fence[self.tile_pos.y][self.tile_pos.x - i] == 1
                i += 1
            if self.tile_pos.x - cur_dist >= 0 and not have_fence:
                self.refreshTileVisability(self.tile_pos + Vector(-cur_dist, 0))
            
            have_fence, i = False, 1
            while(i <= cur_dist and self.tile_pos.x + i < Game.FIELD_SIZE_IN_TILES.w):
                have_fence |= true_v_fence[self.tile_pos.y][self.tile_pos.x + i - 1] == 1
                i += 1
            if self.tile_pos.x + cur_dist < Game.FIELD_SIZE_IN_TILES.w and not have_fence:
                self.refreshTileVisability(self.tile_pos + Vector(cur_dist, 0))

            have_fence, i = False, 1
            while(i <= cur_dist and self.tile_pos.y - i >= 0):
                have_fence |= true_h_fence[self.tile_pos.y - i][self.tile_pos.x] == 1
                i += 1
            if self.tile_pos.y - cur_dist >= 0 and not have_fence:
                self.refreshTileVisability(self.tile_pos + Vector(0, -cur_dist))

            have_fence, i = False, 1
            while(i <= cur_dist and self.tile_pos.y + i < Game.FIELD_SIZE_IN_TILES.h):
                have_fence |= true_h_fence[self.tile_pos.y + i - 1][self.tile_pos.x] == 1
                i += 1
            if self.tile_pos.y + cur_dist < Game.FIELD_SIZE_IN_TILES.h and not have_fence:
                self.refreshTileVisability(self.tile_pos + Vector(0, cur_dist))


    def refreshTileVisability(self, tile):
        true_v_fence, true_h_fence = self.game.v_fence, self.game.h_fence
        self.see_enemy = self.see_enemy or tile == self.enemy.tile_pos

        if tile == self.game.exit_tile:
            self.saw_exit = True
        
        if tile == self.game.gold_tile:
            self.saw_gold = True
        
        if (tile.x > 0):                   self.v_fence[tile.y][tile.x - 1] = true_v_fence[tile.y][tile.x - 1]
        if (tile.x < Game.FIELD_SIZE_IN_TILES.w - 1): self.v_fence[tile.y][tile.x] = true_v_fence[tile.y][tile.x]
        if (tile.y > 0):                   self.h_fence[tile.y - 1][tile.x] = true_h_fence[tile.y - 1][tile.x]
        if (tile.y < Game.FIELD_SIZE_IN_TILES.h - 1): self.h_fence[tile.y][tile.x] = true_h_fence[tile.y][tile.x]
    

    def getInfo(self):
        self.checkVisability()
        data = {
            "p": { "x": self.position.x, "y": self.position.y },
            "lm": self.last_move,
            "vf": Game.getBitFence(self.v_fence),
            "hf": Game.getBitFence(self.h_fence),
            "vd": self.view_dist,
            "gs": "ongoing"
        }
        if self.saw_exit:
            data["et"] = { "x": self.game.exit_tile.x, "y": self.game.exit_tile.y }
        if self.see_enemy:
            data["ep"] = { "x": self.enemy.position.x, "y": self.enemy.position.y }
            data["elm"] = self.enemy.last_move
        return data
    

    def getFinishInfo(self):
        data = {
            "p":  { "x": self.position.x, "y": self.position.y },
            "ep": { "x": self.enemy.position.x, "y": self.enemy.position.y },
            "lm": self.last_move,
            "elm": self.enemy.last_move,
            "vf": Game.getBitFence(self.game.v_fence),
            "hf": Game.getBitFence(self.game.h_fence),
            "et": { "x": self.game.exit_tile.x, "y": self.game.exit_tile.y },
            "vd": self.view_dist,
            "gs": "finished",
            "w": self.game.winner
        }
        if self.game.isGoldOnFloor():
            data["gt"] = { "x": self.game.gold_tile.x, "y": self.game.gold_tile.y }
        return data



class Vampire(Character):

    BATS_RECOVERY_SECONDS = 12
    BATS_DURATION_SECONDS  = 3

    def __init__(self, game, user_sid):
        x = round(game.FLOOR_TOP_LEFT.x + Game.TILE_SIZE / 2)
        y = round(game.FLOOR_TOP_LEFT.y + Game.TILE_SIZE / 2)
        super(Vampire, self).__init__(game, user_sid, Vector(x, y))

        self.bats = RecoveryTool(
            Vampire.BATS_RECOVERY_SECONDS, 
            Vampire.BATS_DURATION_SECONDS,
            game.created_time + Game.DELAY_START_SECONDS
        )
        self.seen_gold_tile = Vector(-1, -1)
        self.push_away_tick = 0


    def refreshTileVisability(self, tile):
        super(Vampire, self).refreshTileVisability(tile)

        if tile == self.game.gold_tile and self.game.isGoldOnFloor():
            self.seen_gold_tile.x = self.game.gold_tile.x
            self.seen_gold_tile.y = self.game.gold_tile.y
        
        if tile == self.game.gold_tile and not self.game.isGoldOnFloor():
            self.seen_gold_tile.x, self.seen_gold_tile.y = -1, -1
    

    def canMoveTo(self, x, y):
        char_rect = Rectangular(Character.MODEL_SIZE_WIDTH, Character.MODEL_SIZE_HEIGHT)
        char_rect.setByTopLeft(x - Character.MODEL_SIZE_WIDTH / 2, y - Character.MODEL_SIZE_HEIGHT / 5)

        if (self.game.isGoldOnFloor() and (abs(self.tile_pos.x - self.game.gold_tile.x) +
            abs(self.tile_pos.y - self.game.gold_tile.y)) <= 1):

            gold_tile_rect = Rectangular(Game.TILE_SIZE, Game.TILE_SIZE)
            gold_tile_rect.setByTopLeft(
                self.game.FLOOR_TOP_LEFT.x + self.game.gold_tile.x * Game.TILE_SIZE,
                self.game.FLOOR_TOP_LEFT.y + self.game.gold_tile.y * Game.TILE_SIZE
            )
            if char_rect.isIntersectWith(gold_tile_rect):
                return False

        if abs(self.tile_pos.x - self.game.exit_tile.x) + abs(self.tile_pos.y - self.game.exit_tile.y) <= 1:
            exit_tile_rect = Rectangular(Game.TILE_SIZE, Game.TILE_SIZE)
            exit_tile_rect.setByTopLeft(
                self.game.FLOOR_TOP_LEFT.x + self.game.exit_tile.x * Game.TILE_SIZE,
                self.game.FLOOR_TOP_LEFT.y + self.game.exit_tile.y * Game.TILE_SIZE
            )
            if char_rect.isIntersectWith(exit_tile_rect):
                return False

        return super(Vampire, self).canMoveTo(x, y)
    

    def tryMoveOneAxis(self, vector):
        if self.push_away_tick > 0:
            return super(Vampire, self).tryMoveOneAxis(vector, [8, 1])
        else:
            return super(Vampire, self).tryMoveOneAxis(vector, [4, 1])
    

    def useBats(self):
        if self.bats.canUse():
            self.bats.use()
            return True
        return False


    def getInfo(self):
        if self.game.status == GameStatus.FINISHED:
            return self.getFinishInfo()

        data = super(Vampire, self).getInfo()
        if self.seen_gold_tile.x != -1:
            data["gt"] = { "x": self.game.gold_tile.x, "y": self.game.gold_tile.y }
        
        active_time = self.bats.getActiveTimeLeft()
        if not self.see_enemy and active_time > 0 and self.bats.used:
            data["bat"] = active_time
            data["ep"] = { "x": self.enemy.position.x, "y": self.enemy.position.y }
        
        if self.see_enemy and self.enemy.torch.used and self.enemy.torch.getActiveTimeLeft() > 0:
            data["eut"] = True
        
        if self.see_enemy and self.enemy.picked_gold:
            data["epg"] = True

        data["trl"] = round(self.bats.getRecoveryTimeLeft() * 100)

        return data

    
    def getFinishInfo(self):
        data = super(Vampire, self).getFinishInfo()
        data["epg"]  = self.enemy.picked_gold
        return data



class Thief(Character):

    TORCH_RECOVERY_SECONDS = 6
    TORCG_DURATION_SECONDS  = 1

    def __init__(self, game, user_sid):
        x = game.FLOOR_TOP_LEFT.x + Game.TILE_SIZE * (Game.FIELD_SIZE_IN_TILES.w - 1) + Game.TILE_SIZE / 2
        y = game.FLOOR_TOP_LEFT.y + Game.TILE_SIZE * (Game.FIELD_SIZE_IN_TILES.h - 1) + Game.TILE_SIZE / 2
        super(Thief, self).__init__(game, user_sid, Vector(round(x), round(y)))
        self.torch = RecoveryTool(
            Thief.TORCH_RECOVERY_SECONDS,
            Thief.TORCG_DURATION_SECONDS,
            game.created_time + Game.DELAY_START_SECONDS
        )
        self.picked_gold = False
        self.just_picked_gold = False
        self.push_away_vec = Vector(0, 0)
    

    def tryMove(self, vector):
        success = super(Thief, self).tryMove(vector)
        if self.picked_gold and self.tile_pos == self.game.exit_tile and self.checkThiefRichExit():
            self.game.status = GameStatus.FINISHED
            self.game.winner = "thief"
    
        if not success:
            return False
        
        if not self.picked_gold and self.tile_pos == self.game.gold_tile:
            char_rect = Rectangular(Character.MODEL_SIZE_WIDTH, Character.MODEL_SIZE_HEIGHT)
            char_rect.setByTopLeft(self.position.x - Character.MODEL_SIZE_WIDTH / 2,
                                         self.position.y - Character.MODEL_SIZE_HEIGHT / 5)
            if char_rect.isIntersectWith(self.game.gold_model):
                self.picked_gold = True
                self.just_picked_gold = True

        return True
    

    def checkThiefRichExit(self):
        char_rect = Rectangular(Character.MODEL_SIZE_WIDTH, Character.MODEL_SIZE_HEIGHT)
        char_rect.setByTopLeft(self.position.x - Character.MODEL_SIZE_WIDTH / 2,
                               self.position.y - Character.MODEL_SIZE_HEIGHT / 5)
        exit_rect = self.game.exit_model

        if self.game.exit_tile.y == 0:

            if (char_rect.tl.y - exit_rect.bl.y <= 2 and
                char_rect.tl.x >= exit_rect.bl.x and char_rect.tr.x <= exit_rect.br.x):
                return True

        elif self.game.exit_tile.y == Game.FIELD_SIZE_IN_TILES.h - 1:

            if (exit_rect.tl.y - char_rect.bl.y <= 2 and
                char_rect.bl.x >= exit_rect.tl.x and char_rect.br.x <= exit_rect.tr.x):
                return True

        elif self.game.exit_tile.x == 0:

            if (char_rect.tl.x - exit_rect.tr.x <= 2 and
                char_rect.tl.y >= exit_rect.tr.y and char_rect.bl.y <= exit_rect.br.y):
                return True

        else:

            if (exit_rect.tl.x - char_rect.tr.x <= 2 and
                char_rect.tr.y >= exit_rect.tl.y and char_rect.br.y <= exit_rect.bl.y):
                return True

        return False
    

    def useTorch(self):
        if self.torch.canUse():
            if self.see_enemy:
                self.pushEnemyAway()
            self.torch.use()
            self.view_dist = 2
            self.checkVisability()
            return True
        return False
    

    def pushEnemyAway(self):
        self.enemy.push_away_tick = 20
        self.push_away_vec = Vector(0, 0)

        x_dif = self.position.x - self.enemy.position.x
        y_dif = self.position.y - self.enemy.position.y
        
        if abs(x_dif) > abs(y_dif):
            self.push_away_vec.x = -1 if x_dif > 0 else 1
            
            y_coord_tile_relative = (self.enemy.position.y - self.game.FLOOR_TOP_LEFT.y) % Game.TILE_SIZE
            character_top_height = Character.MODEL_SIZE_HEIGHT / 5
            if y_coord_tile_relative - character_top_height <= Game.SEPTUM_SIZE // 2:
                self.push_away_vec.y = -1
            if y_coord_tile_relative + (Character.MODEL_SIZE_HEIGHT - character_top_height) >= Game.TILE_SIZE - Game.SEPTUM_SIZE // 2:
                self.push_away_vec.y = 1
        else:
            self.push_away_vec.y = -1 if y_dif > 0 else 1

            x_coord_tile_relative = (self.enemy.position.x - self.game.FLOOR_TOP_LEFT.x) % Game.TILE_SIZE
            if x_coord_tile_relative - Character.MODEL_SIZE_WIDTH / 2 <= Game.SEPTUM_SIZE // 2:
                self.push_away_vec.x = -1
            if x_coord_tile_relative + Character.MODEL_SIZE_WIDTH / 2 >= Game.TILE_SIZE - Game.SEPTUM_SIZE // 2:
                self.push_away_vec.x = 1


    def getInfo(self):
        data = dict()

        if self.enemy.push_away_tick > 0:
            self.enemy.push_away_tick -= 1
            self.enemy.tryMove(self.push_away_vec)

        active_time = self.torch.getActiveTimeLeft()
        if active_time == 0 and self.view_dist == 2:
            self.view_dist = 1
            self.checkVisability()
        
        if active_time > 0 and self.torch.used:
            data["ut"] = True

        if self.game.status == GameStatus.FINISHED:
            return self.getFinishInfo()
        
        bats_active_time = self.enemy.bats.getActiveTimeLeft()
        if bats_active_time > 0 and self.enemy.bats.used:
            data["eba"] = True

        data.update(super(Thief, self).getInfo())
        if self.saw_gold and not self.picked_gold:
            data["gt"] = { "x": self.game.gold_tile.x, "y": self.game.gold_tile.y }
        
        if self.just_picked_gold:
            data["jpg"] = True
            self.just_picked_gold = False
        
        data["pg"] = self.picked_gold
        data["trl"]  = round(self.torch.getRecoveryTimeLeft() * 100)
        return data
    

    def getFinishInfo(self):
        data = super(Thief, self).getFinishInfo()
        data["pg"] = self.picked_gold
        return data



class Game:

    FIELD_SIZE_IN_TILES = Rectangular(12, 8)
    TILE_SIZE     = 80
    SEPTUM_SIZE   = 30
    GOLD_SIZE     = 40
    TRACKER_SIZE  = 30
    BRICK_SIZE    = Rectangular(30, 15)
    FENCE_SIZE    = Rectangular(50, 10)
    EXIT_SIZE     = Rectangular(40, 30)
    N_BRICK_LAYER = 2

    DELAY_START_SECONDS       = 3 ########### !!!!!!!!!!!!!!!!       CHENGE AFTER FINISH                 !!!!!!!!!
    AVAILABLE_VELOCITY_VALUES = {1, 0, -1}

    def __init__(self, game_id, vampire_user_sid, thief_user_sid):
        self.FIELD_SIZE = Rectangular(2 * Game.N_BRICK_LAYER * Game.BRICK_SIZE.h + Game.FIELD_SIZE_IN_TILES.w * Game.TILE_SIZE,
                                      2 * Game.N_BRICK_LAYER * Game.BRICK_SIZE.h + Game.FIELD_SIZE_IN_TILES.h * Game.TILE_SIZE)
        self.FLOOR_TOP_LEFT  = Vector(Game.N_BRICK_LAYER * Game.BRICK_SIZE.h, Game.N_BRICK_LAYER * Game.BRICK_SIZE.h)
        self.FLOOR_BOT_RIGHT = Vector(Game.N_BRICK_LAYER * Game.BRICK_SIZE.h + Game.TILE_SIZE * Game.FIELD_SIZE_IN_TILES.w - 1,
                                      Game.N_BRICK_LAYER * Game.BRICK_SIZE.h + Game.TILE_SIZE * Game.FIELD_SIZE_IN_TILES.h - 1)

        self.game_id       = game_id
        self.v_fence       = [[0] * (Game.FIELD_SIZE_IN_TILES.w - 1) for i in range(Game.FIELD_SIZE_IN_TILES.h)]
        self.h_fence       = [[0] * Game.FIELD_SIZE_IN_TILES.w for i in range(Game.FIELD_SIZE_IN_TILES.h - 1)]
        self.v_fence_model = []
        self.h_fence_model = []
        self.septum_models = []
        self.gold_tile     = None
        self.gold_model    = None
        self.exit_tile     = None
        self.exit_model    = None
        self.status        = GameStatus.WAITING
        self.winner        = None
        self.created_time  = time()
        self.vampire       = Vampire(self, vampire_user_sid)
        self.thief         = Thief(self, thief_user_sid)
        self.initGoldAndExit()
        self.initSeptumModels()
        self.initFenceModels()
        self.initRandomFance()
        self.checkFenceCorrectnessWithTile(self.exit_tile)
        self.checkFenceCorrectnessWithTile(self.gold_tile)
        self.vampire.setEnemy(self.thief)
        self.vampire.checkVisability()
        self.thief.setEnemy(self.vampire)
        self.thief.checkVisability()


    def initGoldAndExit(self):
        self.gold_tile = Vector(*random.choice([
            (x, y) for x in range(Game.FIELD_SIZE_IN_TILES.w) for y in range(Game.FIELD_SIZE_IN_TILES.h)
            if (x + y) >= 5 and (Game.FIELD_SIZE_IN_TILES.w + Game.FIELD_SIZE_IN_TILES.h - 2 - x - y) >= 5
        ]))
        self.gold_model = Rectangular(Game.GOLD_SIZE, Game.GOLD_SIZE)
        self.gold_model.setByCenter(self.FLOOR_TOP_LEFT.x + self.gold_tile.x * Game.TILE_SIZE + Game.TILE_SIZE // 2,
                                    self.FLOOR_TOP_LEFT.y + self.gold_tile.y * Game.TILE_SIZE + Game.TILE_SIZE // 2)

        self.exit_tile = Vector(*random.choice([
            (x, y) for x in range(Game.FIELD_SIZE_IN_TILES.w) for y in range(Game.FIELD_SIZE_IN_TILES.h)
            if (x == 0 or x == Game.FIELD_SIZE_IN_TILES.w - 1 or y == 0 or y == Game.FIELD_SIZE_IN_TILES.h - 1) and
                (x + y) >= 5 and (Game.FIELD_SIZE_IN_TILES.w + Game.FIELD_SIZE_IN_TILES.h - 2 - x - y) >= 5 and
                abs(self.gold_tile.x - x) + abs(self.gold_tile.y - y) >= 6
        ]))
    
        half_exit_width, half_tile_size = Game.EXIT_SIZE.w // 2, Game.TILE_SIZE // 2
        exit_x_top_left, exit_y_top_left = self.FLOOR_TOP_LEFT.x, self.FLOOR_TOP_LEFT.y
        if self.exit_tile.y == 0 or self.exit_tile.y == Game.FIELD_SIZE_IN_TILES.h - 1:
            self.exit_model = Rectangular(Game.EXIT_SIZE.w, Game.EXIT_SIZE.h)
            if self.exit_tile.y == 0:
                exit_x_top_left += self.exit_tile.x * Game.TILE_SIZE + half_tile_size - half_exit_width
                exit_y_top_left -= Game.EXIT_SIZE.h
            else:
                exit_x_top_left += self.exit_tile.x * Game.TILE_SIZE + half_tile_size - half_exit_width
                exit_y_top_left = self.FLOOR_BOT_RIGHT.y + 1
        else:
            self.exit_model = Rectangular(Game.EXIT_SIZE.h, Game.EXIT_SIZE.w)
            if self.exit_tile.x == 0:
                exit_x_top_left -= Game.EXIT_SIZE.h
                exit_y_top_left += self.exit_tile.y * Game.TILE_SIZE + half_tile_size - half_exit_width
            else:
                exit_x_top_left = self.FLOOR_BOT_RIGHT.x + 1
                exit_y_top_left += self.exit_tile.y * Game.TILE_SIZE + half_tile_size - half_exit_width
        self.exit_model.setByTopLeft(exit_x_top_left, exit_y_top_left)


    def initSeptumModels(self):
        for column in range(1, Game.FIELD_SIZE_IN_TILES.w):
            for row in range(1, Game.FIELD_SIZE_IN_TILES.h):
                septum = Rectangular(Game.SEPTUM_SIZE, Game.SEPTUM_SIZE)
                septum.setByCenter(self.FLOOR_TOP_LEFT.x + Game.TILE_SIZE * column,
                                   self.FLOOR_TOP_LEFT.y + Game.TILE_SIZE * row,)
                self.septum_models.append(septum)
    

    def initFenceModels(self):
        for row in range(Game.FIELD_SIZE_IN_TILES.h):
            v_fences = []
            for column in range(1, Game.FIELD_SIZE_IN_TILES.w):
                x = self.FLOOR_TOP_LEFT.x + column * Game.TILE_SIZE - Game.FENCE_SIZE.h // 2
                y = self.FLOOR_TOP_LEFT.y + row * Game.TILE_SIZE
                if row > 0:
                    y += Game.SEPTUM_SIZE // 2
                height = Game.FENCE_SIZE.w
                if row == 0 or row == Game.FIELD_SIZE_IN_TILES.w - 1:
                    height += Game.SEPTUM_SIZE // 2
                
                fence = Rectangular(Game.FENCE_SIZE.h, height)
                fence.setByTopLeft(x, y)
                v_fences.append(fence)
            self.v_fence_model.append(v_fences)
        
        for row in range(1, Game.FIELD_SIZE_IN_TILES.h):
            h_fences = []
            for column in range(Game.FIELD_SIZE_IN_TILES.w):
                x = self.FLOOR_TOP_LEFT.x + column * Game.TILE_SIZE
                if column > 0:
                    x += Game.SEPTUM_SIZE // 2
                y = self.FLOOR_TOP_LEFT.y + row * Game.TILE_SIZE - Game.FENCE_SIZE.h // 2
                width = Game.FENCE_SIZE.w
                if (column == 0 or column == Game.FIELD_SIZE_IN_TILES.w - 1):
                    width += Game.SEPTUM_SIZE // 2         
                
                fence = Rectangular(width, Game.FENCE_SIZE.h)
                fence.setByTopLeft(x, y)
                h_fences.append(fence)
            self.h_fence_model.append(h_fences)

    
    def initRandomFance(self):
        N_ADDITION_FENCE_DIVISOR = 100

        ## create vertical fence
        available_verticle_rows = list(range(Game.FIELD_SIZE_IN_TILES.h))
        last_row_ix = Game.FIELD_SIZE_IN_TILES.h - 1
        last_col_ix = Game.FIELD_SIZE_IN_TILES.w - 2
        while(len(available_verticle_rows)):
            row = random.choice(available_verticle_rows)
            available_column = []
            for column in range(Game.FIELD_SIZE_IN_TILES.w - 1):
                if self.checkFenceAvailable(self.v_fence, row, column, last_row_ix, last_col_ix):
                    available_column.append(column)

            if len(available_column) > 0:
                column = random.choice(available_column)
                self.v_fence[row][column] = 1
            else:
                available_verticle_rows.remove(row)

        ## additional v fence
        n_additional_v_fence = Game.FIELD_SIZE_IN_TILES.h * Game.FIELD_SIZE_IN_TILES.w // N_ADDITION_FENCE_DIVISOR
        available_verticle_rows = list(range(1, Game.FIELD_SIZE_IN_TILES.h - 1))
        while(len(available_verticle_rows) and n_additional_v_fence):
            row = random.choice(available_verticle_rows)
            available_column = []
            for column in range(1, Game.FIELD_SIZE_IN_TILES.w - 2):
                if (self.v_fence[row][column] == 0 and self.v_fence[row - 1][column] == 0 and
                    self.v_fence[row + 1][column] == 0 and self.v_fence[row][column - 1] == 0 and
                    self.v_fence[row][column + 1] == 0):
                    available_column.append(column)
            
            if len(available_column) > 0:
                column = random.choice(available_column)
                self.v_fence[row][column] = 1
                n_additional_v_fence -= 1
            else:
                available_verticle_rows.remove(row)

        ## create horrizontal fence
        available_horizontal_rows = list(range(Game.FIELD_SIZE_IN_TILES.h - 1))
        last_row_ix = Game.FIELD_SIZE_IN_TILES.h - 2
        last_col_ix = Game.FIELD_SIZE_IN_TILES.w - 1
        while(len(available_horizontal_rows)):
            row = random.choice(available_horizontal_rows)
            available_column = []    
            for column in range(Game.FIELD_SIZE_IN_TILES.w):
                if self.checkFenceAvailable(self.h_fence, row, column, last_row_ix, last_col_ix):
                    if ((row == 0 and column == 0 and self.v_fence[0][0] == 1) or
                        (row == 0 and column == last_col_ix and self.v_fence[0][last_col_ix - 1] == 1) or
                        (row == last_row_ix and column == 0 and self.v_fence[last_row_ix + 1][0] == 1) or
                        (row == last_row_ix and column == last_col_ix and self.v_fence[last_row_ix + 1][last_col_ix - 1] == 1)):
                        continue
                    available_column.append(column)

            if len(available_column) > 0:
                column = random.choice(available_column)
                self.h_fence[row][column] = 1
            else:
                available_horizontal_rows.remove(row)

        ## additional h fence
        n_additional_h_fence = Game.FIELD_SIZE_IN_TILES.h * Game.FIELD_SIZE_IN_TILES.w // N_ADDITION_FENCE_DIVISOR
        available_horizontal_rows = list(range(1, Game.FIELD_SIZE_IN_TILES.h - 2))
        while(len(available_horizontal_rows) and n_additional_h_fence):
            row = random.choice(available_horizontal_rows)
            available_column = []
            for column in range(1, Game.FIELD_SIZE_IN_TILES.w - 1):
                if (self.h_fence[row][column] == 0  and self.h_fence[row - 1][column] == 0 and
                    self.h_fence[row + 1][column] == 0 and self.h_fence[row][column - 1] == 0 and
                    self.h_fence[row][column + 1] == 0):
                    available_column.append(column)
            
            if len(available_column) > 0:
                column = random.choice(available_column)
                self.h_fence[row][column] = 1
                n_additional_h_fence -= 1
            else:
                available_horizontal_rows.remove(row)


    def checkFenceAvailable(self, all_fence, row, column, last_row_ix, last_col_ix):
        is_available  = all_fence[row][column] == 0
        is_available &= row == 0 or column == 0 or all_fence[row - 1][column - 1] == 0
        is_available &= row == 0 or all_fence[row - 1][column] == 0
        is_available &= row == 0 or column == last_col_ix or all_fence[row - 1][column + 1] == 0
        is_available &= column == 0 or all_fence[row][column - 1] == 0
        is_available &= column == last_col_ix or all_fence[row][column + 1] == 0
        is_available &= row == last_row_ix or column == 0 or all_fence[row + 1][column - 1] == 0
        is_available &= row == last_row_ix or all_fence[row + 1][column] == 0
        is_available &= row == last_row_ix or column == last_col_ix or all_fence[row + 1][column + 1] == 0

        return is_available
    

    def checkFenceCorrectnessWithTile(self, tile):
        if tile.y == 0:

            if tile.x == Game.FIELD_SIZE_IN_TILES.w - 1:
                self.v_fence[0][Game.FIELD_SIZE_IN_TILES.w - 2] = 0
                self.h_fence[0][Game.FIELD_SIZE_IN_TILES.w - 1] = 0
            elif self.v_fence[0][tile.x - 1] + self.v_fence[0][tile.x] + self.h_fence[0][tile.x] == 2:
                self.h_fence[0][tile.x] = 0

        elif tile.y == Game.FIELD_SIZE_IN_TILES.h - 1:

            if tile.x == 0:
                self.v_fence[Game.FIELD_SIZE_IN_TILES.h - 1][0] = 0
                self.h_fence[Game.FIELD_SIZE_IN_TILES.h - 2][0] = 0
            elif (self.v_fence[Game.FIELD_SIZE_IN_TILES.h - 1][tile.x] +
                  self.v_fence[Game.FIELD_SIZE_IN_TILES.h - 1][tile.x - 1] +
                  self.h_fence[Game.FIELD_SIZE_IN_TILES.h - 2][tile.x]) == 2:
                self.h_fence[Game.FIELD_SIZE_IN_TILES.h - 2][tile.x] = 0

        elif tile.x == 0:

            if self.v_fence[tile.y][0] + self.h_fence[tile.y][0] + self.h_fence[tile.y - 1][0] == 2:
                self.v_fence[tile.y][0] = 0
    
        else:
            
            if (self.v_fence[tile.y][Game.FIELD_SIZE_IN_TILES.w - 2] +
                self.h_fence[tile.y][Game.FIELD_SIZE_IN_TILES.w - 1] +
                self.h_fence[tile.y - 1][Game.FIELD_SIZE_IN_TILES.w - 1]) == 2:
                self.v_fence[tile.y][Game.FIELD_SIZE_IN_TILES.w - 2] = 0


    def getGameSettings(self):
        return {
            "field_size_in_tiles": {
                "width": Game.FIELD_SIZE_IN_TILES.w,
                "height": Game.FIELD_SIZE_IN_TILES.h
            },
            "field_size": { "width": self.FIELD_SIZE.w, "height": self.FIELD_SIZE.h },
            "brick_size": { "width": Game.BRICK_SIZE.w, "height": Game.BRICK_SIZE.h },
            "fence_size": { "width": Game.FENCE_SIZE.w, "height": Game.FENCE_SIZE.h },
            "exit_size":  { "width": Game.EXIT_SIZE.w,  "height": Game.EXIT_SIZE.h },
            "tile_size":   Game.TILE_SIZE,
            "septum_size": Game.SEPTUM_SIZE,
            "gold_size":   Game.GOLD_SIZE,
            "tracker_size":  Game.TRACKER_SIZE,
            "game_start_delay": Game.DELAY_START_SECONDS
        }
    

    def getTimeBeforeStart(self):
        return self.created_time + Game.DELAY_START_SECONDS - time()


    def isGameAvailable(self):
        if self.status == GameStatus.ONGOING:
            return True
        
        if self.status == GameStatus.FINISHED:
            return False
        
        if time() - self.created_time >= Game.DELAY_START_SECONDS:
            self.status = GameStatus.ONGOING
        
        return self.status == GameStatus.ONGOING


    def getOpponentId(self, user_sid):
        return self.vampire.user_sid if self.vampire.user_sid != user_sid else self.thief.user_sid
    

    def calcTile(self, x, y):
        column = (x - self.FLOOR_TOP_LEFT.x) // Game.TILE_SIZE
        row    = (y - self.FLOOR_TOP_LEFT.y) // Game.TILE_SIZE
        return Vector(column, row)
    

    def getPosition(self, user_sid):
        pos = self.vampire.position
        if self.thief.user_sid == user_sid:
            pos = self.thief.position
        return { "x": pos.x, "y": pos.y }
    

    def makeMove(self, user_sid, x, y):
        vector  = Vector(x, y)
        success = False

        if user_sid == self.thief.user_sid:
            success = self.thief.tryMove(vector)
        elif self.vampire.push_away_tick == 0:
            success = self.vampire.tryMove(vector)
        
        if success:
            self.checkVampireCaughtThief()
    

    def checkVampireCaughtThief(self):
        vampire_rect = Rectangular(Character.MODEL_SIZE_WIDTH, Character.MODEL_SIZE_HEIGHT)
        vampire_rect.setByTopLeft(
            self.vampire.position.x - Character.MODEL_SIZE_WIDTH / 2,
            self.vampire.position.y - Character.MODEL_SIZE_HEIGHT / 5)
        
        thief_rect = Rectangular(Character.MODEL_SIZE_WIDTH, Character.MODEL_SIZE_HEIGHT)
        thief_rect.setByTopLeft(
            self.thief.position.x - Character.MODEL_SIZE_WIDTH / 2,
            self.thief.position.y - Character.MODEL_SIZE_HEIGHT / 5)

        if vampire_rect.isIntersectWith(thief_rect):
            self.status = GameStatus.FINISHED
            self.winner = "vampire"


    def useBats(self, user_sid):
        if self.vampire.user_sid == user_sid:
            self.vampire.useBats()
    

    def useTorch(self, user_sid):
        if self.thief.user_sid == user_sid:
            self.thief.useTorch()
        

    def getInfo(self, user_sid):
        if user_sid == self.vampire.user_sid:
            return self.vampire.getInfo()
        return self.thief.getInfo()


    def isGoldOnFloor(self):
        return not self.thief.picked_gold


    def userOffline(self, user_sid):
        if self.vampire.user_sid == user_sid:
            self.vampire.online = False
        else:
            self.thief.online = False
    

    @staticmethod
    def getBitFence(fence):
        bf = []
        for row in fence:
            res = 0
            power = 1
            for val in reversed(row):
                res += power * val
                power *= 2
            bf.append(res)
        return bf
