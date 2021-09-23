from collections import deque
from enum import Enum, auto
from game import Game, GameStatus, Vampire, Thief
from flask_socketio import SocketIO, emit, send
from t_bot import notifyMeInTelegram
import time
import random



class UserStatus(Enum):
    SEARCHING_GAME = auto()
    PLAYING = auto()



def check_game(orig_func):

    def inner_func(self, user_sid):
        game_id = self.user_game_dict.get(user_sid, None)
        if game_id is None or self.games.get(game_id, None) is None:
            return
        return orig_func(self, user_sid)

    return inner_func



class GameManager:

    SEARCH_GAME_REQUEST_WAIT_TIME_SECONDDS = 10


    def __init__(self):
        self.n_games = 0
        self.games = dict()
        self.user_status = dict()
        self.user_game_dict = dict()
        self.free_vampires = set()
        self.free_thiefs = set()
        self.free_vt = set()
    

    def getNewGameId(self):
        self.n_games += 1
        return self.n_games
    

    def findPair(self, user_sid, options):
        vampire_sid, thief_sid = None, None

        if options["vampire"] + options["thief"] == 2:

            if len(self.free_thiefs) > len(self.free_vampires):
                vampire_sid, thief_sid = user_sid, self.free_thiefs.pop()
            elif len(self.free_vampires) > len(self.free_thiefs) or len(self.free_vampires) > 0:
                vampire_sid, thief_sid = self.free_vampires.pop(), user_sid
            elif len(self.free_vt) > 0:
                if random.randrange(2) == 1:
                    vampire_sid, thief_sid = self.free_vt.pop(), user_sid
                else:
                    vampire_sid, thief_sid = user_sid, self.free_vt.pop()

        elif options["vampire"]:

            if len(self.free_thiefs) > 0:
                vampire_sid, thief_sid = user_sid, self.free_thiefs.pop()
            elif len(self.free_vt) > 0:
                vampire_sid, thief_sid = user_sid,  self.free_vt.pop()

        else:

            if len(self.free_vampires) > 0:
                vampire_sid, thief_sid = self.free_vampires.pop(), user_sid
            elif len(self.free_vt) > 0:
                vampire_sid, thief_sid = self.free_vt.pop(), user_sid
        
        if vampire_sid is None:
            return False
        
        return (vampire_sid, thief_sid)


    def findGame(self, user_sid, options):
        res = self.findPair(user_sid, options)

        if res:
            vampire_sid, thief_sid = res
            self.user_status[vampire_sid] = UserStatus.PLAYING
            self.user_status[thief_sid]   = UserStatus.PLAYING
            game_id = self.getNewGameId()
            game = Game(game_id, vampire_sid, thief_sid)
            self.games[game_id] = game
            self.user_game_dict[vampire_sid] = game_id
            self.user_game_dict[thief_sid]   = game_id
            game_settings = game.getGameSettings()
            emit(
                "found_game",
                {
                    "role": "vampire",
                    "p": game.getPosition(vampire_sid),
                    "tool_total_recovery": Vampire.BATS_RECOVERY_SECONDS,
                    **game_settings
                },
                room=vampire_sid
            )
            emit(
                "found_game",
                {
                    "role": "thief",
                    "p": game.getPosition(thief_sid),
                    "tool_total_recovery": Thief.TORCH_RECOVERY_SECONDS,
                    **game_settings
                },
                room=thief_sid
            )
        else:

            if options["vampire"] and options["thief"]: self.free_vt.add(user_sid)
            elif options["vampire"]: self.free_vampires.add(user_sid)
            else: self.free_thiefs.add(user_sid)

            self.user_status[user_sid] = UserStatus.SEARCHING_GAME
            # notifyMeInTelegram()
            

    def userDisconnected(self, user_sid):
        if self.user_status[user_sid] == UserStatus.SEARCHING_GAME:
            self.free_vampires.discard(user_sid)
            self.free_thiefs.discard(user_sid)
            self.free_vt.discard(user_sid)
        else:
            game_id = self.user_game_dict[user_sid]
            del self.user_game_dict[user_sid]
            game = self.games[game_id]
            game.userOffline(user_sid)

            if (game.vampire.online == False and game.thief.online == False):
                del self.games[game_id]

        del self.user_status[user_sid]
    

    def makeMove(self, user_sid, vector):
        x, y = vector.get("x"), vector.get("y")
        if (not isinstance(x, int) or not isinstance(y, int) or
            x not in Game.AVAILABLE_VELOCITY_VALUES or
            y not in Game.AVAILABLE_VELOCITY_VALUES):
            return

        game_id = self.user_game_dict.get(user_sid)
        if game_id is None: return

        game = self.games.get(game_id)
        if game is None or not game.isGameAvailable(): return

        game.makeMove(user_sid, x, y)
    

    @check_game
    def useBats(self, user_sid):
        game_id = self.user_game_dict[user_sid]
        self.games[game_id].useBats(user_sid)

    
    @check_game
    def useTorch(self, user_sid):
        game_id = self.user_game_dict[user_sid]
        self.games[game_id].useTorch(user_sid)
        

    @check_game
    def getGameInfo(self, user_sid):
        game_id = self.user_game_dict[user_sid]
        return self.games[game_id].getInfo(user_sid)
