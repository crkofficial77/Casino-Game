from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
suits = ["H","D","C","S"]

rooms = {}
ready = {}

def value(rank):
    if rank == "A":
        return 1
    if rank in ["10","J","Q","K"]:
        return 0
    return int(rank)

def draw():
    rank = random.choice(ranks)
    suit = random.choice(suits)

    code_rank = "0" if rank == "10" else rank
    code = code_rank + suit

    return {"rank":rank,"suit":suit,"code":code}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join")
def join(data):

    room = data["room"]
    join_room(room)

    if room not in rooms:
        rooms[room] = []

    if request.sid not in rooms[room]:
        rooms[room].append(request.sid)

    if room not in ready:
        ready[room] = 0

    if len(rooms[room]) == 2:
        socketio.emit("start", room=room)
    else:
        emit("waiting")

@socketio.on("ready")
def ready_player(data):

    room = data["room"]
    ready[room] += 1

    socketio.emit("readyCount",{
        "ready": ready[room]
    }, room=room)

@socketio.on("play")
def play(data):

    room = data["room"]
    bet = data["bet"]

    pot = bet * 2

    p1 = [draw(), draw()]
    p2 = [draw(), draw()]

    p1_score = (value(p1[0]["rank"]) + value(p1[1]["rank"])) % 10
    p2_score = (value(p2[0]["rank"]) + value(p2[1]["rank"])) % 10

    winner = "Tie"
    win = False

    if p1_score > p2_score:
        winner = "Player 1 Wins"
        win = True
    elif p2_score > p1_score:
        winner = "Player 2 Wins"

    socketio.emit("result",{
        "p1_cards":p1,
        "p2_cards":p2,
        "p1_score":p1_score,
        "p2_score":p2_score,
        "winner":winner,
        "pot":pot,
        "win":win
    }, room=room)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)