from flask import Flask, render_template
from flask_socketio import SocketIO
from controller import controller
from threading import Thread
from time import sleep
import os
import signal


def main():
    thread = Thread(target=read_sensor_data, daemon=True)
    shutdown_monitor = Thread(target=monitor_shutdown, daemon=True)
    thread.start()
    shutdown_monitor.start()
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)


app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")


# Runs as a thread, continuously reads the sensor data from the controller object
def read_sensor_data():
    while True:
        data = controller.get_sensor_data()
        socketio.emit("sensor_update", data)
        socketio.sleep(1)


# Runs as a thread, watches if shutdown conditions are met and initiates a shutdown routine when yes
def monitor_shutdown():
    controller.shutdown_event.wait()
    sleep(2)
    controller.cleanup()
    # Kills the process using SIGINT, effectively emulating CTRL-C; other methods don't close the dht22 gracefully.
    os.kill(os.getpid(), signal.SIGINT)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    main()
