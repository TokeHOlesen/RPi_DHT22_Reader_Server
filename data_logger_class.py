
from datetime import date, datetime
from pathlib import Path
import csv
import os
import sqlite3


class DataLogger:
    def __init__(self, file_path):
        self.db_file_path = Path(file_path)
        self.initialize()
    
    def initialize(self):
        if not self.db_file_path.is_file():
            print("Warning: the database file does not exist.\nAttempting to create a new database file... ", end="")
            try:
                with open(self.db_file_path, "wb") as _:
                    pass
                print("Successful.")
            except OSError:
                print("Failed.")
                exit('Error: cannot create file "sql_db.db".')
        try:
            self.connection = sqlite3.connect(self.db_file_path)
            self.cursor = self.connection.cursor()
            self.cursor.execute("PRAGMA journal_mode=WAL;")
            self.cursor.execute("PRAGMA synchronous=FULL;")
            self.create_db_table()
        except sqlite3.OperationalError:
            exit("Error: database file exists but doesn't contain a valid table.")

    def create_db_table(self):
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS hum_temp (
            id INTEGER PRIMARY KEY,
            datetime TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
            );"""
        )
        
    def log_data(self, temp, hum):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connection:
            self.cursor.execute(
                "INSERT INTO hum_temp (datetime, temperature, humidity) "
                "VALUES (?, ?, ?);",
                (current_datetime, temp, hum)
            )

    def close(self):
        self.cursor.close()
        self.connection.close()
        