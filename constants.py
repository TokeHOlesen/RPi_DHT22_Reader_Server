# How often the data is read from the sensors, in seconds
UPDATE_FREQUENCY = 1
# How often to read and log data, in seconds
LOG_FREQUENCY = 60
# If this many consecutive readings are identical, forces a restart (sensor is most likely stuck)
WATCHDOG_THRESHOLD = 15

# If True, starts in active mode (takes readings, updates database, green LED on)
DEFAULT_START_MODE = True
# Which display mode to use after boot (0 for temperature, 1 for humidity, 2 for off)
DEFAULT_DISPLAY_MODE = 2

# GPIO pins
ON_OFF_BTN_PIN = 2
CYCLE_BUTTON_PIN = 21
ON_LED_PIN = 27
OFF_LED_PIN = 17

# Shift register GPIO pins
VCC_PIN = 4
SRCLR_PIN = 3
SRCLK_PIN = 24
RCLK_PIN = 16
DS_PIN = 20

# Path to the SQLite database file that contains sensor readings
SQL_FILE_PATH = "./sql_db.db"
RAM_FILE_PATH = "/dev/shm/temphum"
RAM_TEMP_FILE_PATH = "/dev/shm/temphum.tmp"
