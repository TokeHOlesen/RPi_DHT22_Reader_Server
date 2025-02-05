from flask import Flask, jsonify, render_template
import time
from datetime import datetime
import sqlite3
import struct
import os

import constants


app = Flask(__name__)


def read_sensor_data():
    """
    Reads the sensor data from the ram file and returns a dict with the obtained values.
    If the file is more than 5 seconds old or doesn't exist, the dict values returned are None.
    """
    try:
        with open(RAM_FILE_PATH, "rb") as ram_file:
            temperature, humidity = struct.unpack("ff", ram_file.read(8))

        file_timestamp = os.path.getmtime(RAM_FILE_PATH)
        current_timestamp = time.time()
        if current_timestamp - file_timestamp < 5:
            return {"temp": f"{temperature:.1f}°C", "hum": f"{humidity:.1f}%"}
        else:
            return {"temp": None, "hum": None}

    except FileNotFoundError:
        return {"temp": None, "hum": None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/latest")
def latest():
    return jsonify(read_sensor_data())


if __name__ == "__main__":
    app.run(debug=True)
