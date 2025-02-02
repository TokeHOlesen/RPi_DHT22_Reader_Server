from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from controller import controller
from threading import Thread


def main():
    thread = Thread(target=read_sensor_data, daemon=True)
    thread.start()
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)


app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")


def read_sensor_data():
    while True:
        data = controller.get_sensor_data()
        socketio.emit("sensor_update", data)
        socketio.sleep(1)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    main()
