from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from controller import controller
from threading import Lock


app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

thread = None
thread_lock = Lock()

def background_thread():
    while True:
        data = controller.get_sensor_data()
        socketio.emit("sensor_update", data)
        socketio.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)
