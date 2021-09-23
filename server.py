from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, send
from game_manager import GameManager
import json


app = Flask(__name__)
socketio = SocketIO(app)
game_manager = GameManager()

@app.route('/')
def main():
    return send_from_directory('static/templates', "index.html")


@app.route("/static/<path:filename>")
def downloadStaticFile(filename):
    return send_from_directory('static/', filename)


@socketio.on('connect')
def socketConnect():
    pass


@socketio.on('find_game')
def findGame(options):
    game_manager.findGame(request.sid, options)


@socketio.on('get_info')
def getInfo(msg):
    emit("new_info", game_manager.getGameInfo(request.sid))


@socketio.on('move')
def move(vector):
    game_manager.makeMove(request.sid, vector)


@socketio.on('use_torch')
def useTorch(options):
    game_manager.useTorch(request.sid)


@socketio.on('use_bats')
def useBats(options):
    game_manager.useBats(request.sid)


@socketio.on('disconnect')
def socket_disconnect():
    game_manager.userDisconnected(request.sid)


socketio.run(app, host='0.0.0.0', port=8000)
