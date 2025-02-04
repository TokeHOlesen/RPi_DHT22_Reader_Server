from flask import Flask, jsonify, render_template
import time
from datetime import datetime
import sqlite3


app = Flask(__name__)


def get_latest_entry():
    conn = sqlite3.connect("sql_db.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, time, temperature, humidity FROM temp_hum ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        latest_date, latest_time, temperature, humidity = row
        latest_entry_time_str = f"{latest_date} {latest_time}"
        latest_entry_time = datetime.strptime(latest_entry_time_str, "%Y-%m-%d %H:%M:%S")
        latest_entry_unix = latest_entry_time.timestamp()
        current_time = time.time()
        if current_time - latest_entry_unix > 5:
            return {"temp": None, "hum": None}
        return {"temp": f"{temperature:.1f}°C", "hum": f"{humidity:.1f}%"}
    return {"temp": None, "hum": None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/latest")
def latest():
    return jsonify(get_latest_entry())


if __name__ == "__main__":
    app.run(debug=True)
