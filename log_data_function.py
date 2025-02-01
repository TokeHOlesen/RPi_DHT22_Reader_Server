
from datetime import date, datetime
import csv
import os


def log_data(temp, hum):
    
    field_names = [
        "Time",
        "Temperature",
        "Humidity"
    ]
    
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
    current_date = date.today()
    filename = f"./logs/{current_date}.csv"
    day_log_exists = os.path.exists(filename)
    
    with open(filename, mode='a' if day_log_exists else 'w', newline='', encoding='utf-8-sig') as log_file:
        writer = csv.DictWriter(log_file, fieldnames=field_names, delimiter=";")
    
        if not day_log_exists:
            writer.writeheader()
        
        writer.writerow({
            "Time": timestamp,
            "Temperature": temp,
            "Humidity": hum
        })
