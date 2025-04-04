import random
import time
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, emit
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

def msg():
    return random.randint(100000, 999999)  # Generates a random 6-digit number

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
            rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif play:
            room = next((r for r in rooms if len(rooms[r]["members"]) == 1), None)
            if not room:
                room = generate_unique_code()
                rooms[room] = {"members": [], "messages": [], "timer_started": False}
            rooms[room]["members"].append(name)
        elif code in rooms and len(rooms[code]["members"]) < 2:
            room = code
            rooms[room]["members"].append(name)
        else:
            return render_template("home.html", error="Room does not exist or is full.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    return render_template("home.html")

@app.route("/play")
def room():
    room = session.get("room")
    if not room or session.get("name") is None or room not in rooms or len(rooms[room]["members"]) > 2:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"], players=rooms[room]["members"])

# WebSocket Event Handlers
@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    if room and name:
        join_room(room)
        emit("update_players", {"players": rooms[room]["members"]}, room=room)
        
        # Start timer if two players are in the room
        if len(rooms[room]["members"]) == 2 and not rooms[room]["timer_started"]:
            rooms[room]["timer_started"] = True
            socketio.start_background_task(start_timer, room)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    
    if room in rooms:
        # Ignore messages if the game hasn't started
        if not rooms[room].get("game_started", False):
            return  # Do nothing if the game is not started yet
        
        result = check(data["message"])  # Process message using check function
        emit("message", {"name": session["name"], "message": result}, room=room)  # Send processed result

def start_timer(room):
    for i in range(10, 0, -1):  # 10-second countdown
        socketio.emit("update_timer", {"time": i}, room=room)
        time.sleep(1)
    
    secret_number = msg()  # Generate a random 6-digit number
    rooms[room]["game_started"] = True  # Mark game as started
    socketio.emit("game_start", {"message": f"Game Started! Your secret code: {secret_number}"}, room=room)

    
def check(message):
    # Implement your custom game logic here
    if message.isdigit():
        return f"Valid number received: {message}"
    else:
        return "Invalid input! Please enter a number."
if __name__ == "__main__":
    socketio.run(app, debug=True)
