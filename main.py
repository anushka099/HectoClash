from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "thiskeyissupersecure"
socketio = SocketIO(app)

gameid = 0
rooms = {}

def generate_no():
    return [random.randint(1, 9) for _ in range(6)]

@app.route("/", methods=["GET", "POST"])
def home():
    global gameid
    if request.method == "POST":
        name = request.form.get("name")
        play = request.form.get("play", False)

        if play:
            room = gameid
            if room not in rooms:
                rooms[room] = {"members": 0, "numbers": None}

            if rooms[room]["members"] >= 2:
                gameid += 1
                room = gameid
                rooms[room] = {"members": 0, "numbers": None}

            session["room"] = room
            session["name"] = name
            return redirect(url_for("play"))

    return render_template("home.html")

@app.route("/play")
def play():
    room = session.get("room")
    name = session.get("name")

    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("play.html", ROOM=room)

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")

    if not name or room not in rooms:
        return
    
    join_room(room)

    if "connected_players" not in rooms[room]:
        rooms[room]["connected_players"] = 0
    rooms[room]["connected_players"] += 1

    if rooms[room]["connected_players"] == 2:
        rooms[room]["numbers"] = generate_no()
        emit("game_status", {"message": "2 players in the game. Starting now!"}, room=room)
        emit("show_numbers", rooms[room]["numbers"], room=room)

    elif rooms[room]["connected_players"] > 2 and rooms[room]["numbers"] is not None:
        emit("game_status", {"message": "Game already started!"})
        emit("show_numbers", rooms[room]["numbers"])

if __name__ == "__main__":
    socketio.run(app, debug=True)
