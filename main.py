from flask import Flask, jsonify, render_template, request
import time
import datetime
import sqlite3
import struct
import os

from constants import *


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
    

def get_data_from_sql(hours):
    now = datetime.datetime.now()
    time_threshold = now - datetime.timedelta(hours=hours)
    
    date_time_threshold = time_threshold.strftime("%Y-%m-%d %H:%M:%S")

    connection = sqlite3.connect(SQL_FILE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT datetime, temperature, humidity 
        FROM hum_temp 
        WHERE datetime >= ? 
        ORDER BY datetime DESC
    """, (date_time_threshold,))

    rows = cursor.fetchall()

    data = [
        {
            "datetime": row[0],
            "temperature": row[1],
            "humidity": row[2]
        }
        for row in rows
    ]

    connection.close()
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/latest")
def latest():
    return jsonify(read_sensor_data())


@app.route("/history")
def history():
    hours = int(request.args.get('hours'))
    return jsonify(get_data_from_sql(hours))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
