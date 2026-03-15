from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
suits = ["H","D","C","S"]

rooms = {}
game_data = {}

def value(card_rank):
    if card_rank == "A":
        return 1
    if card_rank in ["10","J","Q","K"]:
        return 0
    return int(card_rank)

def draw():
    rank = random.choice(ranks)
    suit = random.choice(suits)

    code_rank = "0" if rank == "10" else rank
    code = code_rank + suit

    return {"rank": rank, "suit": suit, "code": code}

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

    if len(rooms[room]) > 2:
        emit("full")
        leave_room(room)
        return

    if len(rooms[room]) == 2:
        socketio.emit("start", room=room)
    else:
        emit("waiting")

@socketio.on("play")
def play(data):

    room = data["room"]

    p1 = [draw(), draw()]
    p2 = [draw(), draw()]

    game_data[room] = {
        "p1_cards": p1,
        "p2_cards": p2
    }

    p1_score = (value(p1[0]["rank"]) + value(p1[1]["rank"])) % 10
    p2_score = (value(p2[0]["rank"]) + value(p2[1]["rank"])) % 10

    socketio.emit("result",{
        "p1_cards":p1,
        "p2_cards":p2,
        "p1_score":p1_score,
        "p2_score":p2_score,
        "winner":"Waiting for Hit or Stand"
    },room=room)

@socketio.on("hit")
def hit(data):

    room = data["room"]

    if room not in game_data:
        return

    new_card = draw()

    game_data[room]["p1_cards"].append(new_card)

    p1_cards = game_data[room]["p1_cards"]
    p2_cards = game_data[room]["p2_cards"]

    p1_score = sum(value(c["rank"]) for c in p1_cards) % 10
    p2_score = sum(value(c["rank"]) for c in p2_cards) % 10

    if p1_score > p2_score:
        winner = "Player 1 Wins"
    elif p2_score > p1_score:
        winner = "Player 2 Wins"
    else:
        winner = "Tie"

    socketio.emit("result",{
        "p1_cards":p1_cards,
        "p2_cards":p2_cards,
        "p1_score":p1_score,
        "p2_score":p2_score,
        "winner":winner
    },room=room)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
