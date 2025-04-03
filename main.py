import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
from string import ascii_uppercase

app = Flask(__name__)
app.secret_key = "thisisasupersecretkey"
socketio = SocketIO(app)
rooms = {}

def generate_unique_code(length=4):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        play = request.form.get("play", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        if create:
            room = generate_unique_code()
            rooms[room] = {"members": 1, "messages": []}
        elif play:
            room = next((r for r in rooms if rooms[r]["members"] == 1), None)
            if not room:
                room = generate_unique_code()
                rooms[room] = {"members": 1, "messages": []}
            else:
                rooms[room]["members"] += 1
        elif code in rooms and rooms[code]["members"] < 2:
            room = code
            rooms[room]["members"] += 1
        else:
            return render_template("home.html", error="Room does not exist or is full.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/play")
def room():
    room = session.get("room")
    if not room or session.get("name") is None or room not in rooms or rooms[room]["members"] > 2:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# WebSocket Event Handlers
@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    if room and name:
        socketio.emit("message", {"name": "System", "message": f"{name} has joined the room {room}."}, room=room)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    if room in rooms:
        rooms[room]["messages"].append({"name": session["name"], "message": data["message"]})
        socketio.emit("message", {"name": session["name"], "message": data["message"]}, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
