import adafruit_dht
import board
import sys
import struct
from time import sleep, time
from gpiozero import Button, LED
from threading import Event, Lock, Thread
from os import replace, _exit

from constants import *
from data_logger_class import DataLogger
from shift_register_class import ShiftRegister


def main():
    controller = Controller()

    threads = [
        Thread(target=controller.sensor_thread, daemon=True),
        Thread(target=controller.led_controller_thread, daemon=True),
        Thread(target=controller.logging_thread, daemon=True),
        Thread(target=controller.monitor_shutdown_thread, daemon=True),
        Thread(target=controller.watchdog_thread, daemon=True),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


class Controller:
    """Controls the circuit and all its elements."""

    def __init__(self):
        # Initializes the DHT22 sensor
        self.dht22 = adafruit_dht.DHT22(board.D23)

        # A dictionary to be shared with the flask thread
        self.data = {"temperature": None, "humidity": None}

        # A thread lock to prevent race conditions
        self.lock = Lock()

        # Initializes the 75HC95N shift register
        self.shift_reg = ShiftRegister(
            vcc_pin=VCC_PIN,
            srclr_pin=SRCLR_PIN,
            srclk_pin=SRCLK_PIN,
            rclk_pin=RCLK_PIN,
            ds_pin=DS_PIN,
        )

        # Turns on and resets the shift register
        self.shift_reg.power_on()
        self.shift_reg.clear_input()
        self.shift_reg.update_output()

        # Initializes the On/Off button and the On/Off LEDs
        self.on_off_button = Button(ON_OFF_BTN_PIN, bounce_time=0.15, hold_time=3)
        # Initializes the button used to cycle through display modes
        self.cycle_button = Button(CYCLE_BUTTON_PIN, bounce_time=0.15)

        self.off_led = LED(OFF_LED_PIN)
        self.on_led = LED(ON_LED_PIN)

        # Assigns functions to be called when the buttons are pressed
        self.on_off_button.when_pressed = self.on_off_button_press_event
        self.on_off_button.when_held = self.shutdown
        self.cycle_button.when_pressed = self.cycle_button_press_event

        # When True, the program will end
        self.shutdown_event = Event()

        # 0 for temperature, 1 for humidity, 2 for no LEDs
        self.display_mode = DEFAULT_DISPLAY_MODE

        # When True, sensor readings will be taken and data will be logged
        self.active = DEFAULT_START_MODE

        # Holds 15 most recent readings in a list of tuples (temp, hum)
        self.last_readings = []

        self.update_on_off_leds()

    def update_on_off_leds(self):
        """Turns the On/Off LEDs on or off depending on whether sensor readings are currently being taken."""
        if self.active:
            self.on_led.on()
            self.off_led.off()
        else:
            self.on_led.off()
            self.off_led.on()

    def get_bits(self, number):
        """Takes an integer, converts it into binary and returns a list containing the first 8 bits."""
        bits = []
        for i in range(8):
            bits.append(number >> i & 1)
        return bits

    def on_off_button_press_event(self):
        """Runs when the On/Off button is pressed. Clears the shift register and toggles active."""
        self.shift_reg.clear_input()
        self.shift_reg.update_output()
        self.active = not self.active
        self.update_on_off_leds()

    def cycle_button_press_event(self):
        """Cycles through display modes."""
        self.display_mode = (self.display_mode + 1) % 3

    def update_bit_leds(self, bits):
        """Loads a list of 8 bits into the shift register."""
        for bit in bits:
            self.shift_reg.load_bit(bit)
        self.shift_reg.update_output()

    def get_sensor_data(self):
        with self.lock:
            return self.data.copy()

    def shutdown(self):
        self.shutdown_event.set()
    
    def save_to_ram_file(self, temp, hum):
        """Saves the readings as a struct (2 floats) into a RAM file in /dev/shm"""
        try:
            # Saves into a temp file first, then replaces the main file with the temp file, to avoid race conditions
            with open(RAM_TEMP_FILE_PATH, "wb") as ram_file:
                ram_file.write(struct.pack("ff", temp, hum))
            replace(RAM_TEMP_FILE_PATH, RAM_FILE_PATH)
        except Exception as e:
            print(f"File write error: {e}")

    def cleanup(self):
        """On shutdown, clears inputs and outputs and turns off LEDs"""
        self.shift_reg.clear_input()
        self.shift_reg.update_output()

        self.on_off_button.close()
        self.cycle_button.close()
        self.on_led.close()
        self.off_led.close()

    def sensor_thread(self):
        """
        Reads data from the sensor, saves it to self.data, writes it to a RAM file,
        and stores the last 15 readings for watchdog monitoring.
        If the sensor read fails, it reuses the last successful values or writes NaN.
        """
        last_temp = None
        last_hum = None

        while not self.shutdown_event.is_set():
            if self.active:
                temp, hum = None, None

                try:
                    temp = self.dht22.temperature
                    hum = self.dht22.humidity

                    if temp is not None and hum is not None:
                        last_temp, last_hum = temp, hum
                        with self.lock:
                            self.data["temperature"] = temp
                            self.data["humidity"] = hum
                            # Records the readings to make sure the sensor isn't stuck
                            self.last_readings.append((temp, hum))
                            if len(self.last_readings) > WATCHDOG_THRESHOLD:
                                self.last_readings.pop(0)

                except Exception as e:
                    print(f"Sensor error: {str(e)}")

                # Use last known good values if the sensor read failed, otherwise NaN
                temp = (
                    temp
                    if temp is not None
                    else (last_temp if last_temp is not None else float("nan"))
                )
                hum = (
                    hum
                    if hum is not None
                    else (last_hum if last_hum is not None else float("nan"))
                )

                # Save data to a RAM file for the HTTP server
                self.save_to_ram_file(temp, hum)

            sleep(UPDATE_FREQUENCY)

    def logging_thread(self):
        """Reads data from self.data and logs it in a sqlite3 database"""
        self.data_logger = DataLogger(SQL_FILE_PATH)
        while not self.shutdown_event.is_set():
            if self.active:
                with self.lock:
                    temp = self.data["temperature"]
                    hum = self.data["humidity"]
                if temp is not None and hum is not None:
                    self.data_logger.log_data(temp, hum)
                for _ in range(LOG_FREQUENCY):
                    if self.shutdown_event.is_set():
                        break
                    sleep(1)
        # When shutdown_event is set, closes the database connection
        self.data_logger.close()

    def led_controller_thread(self):
        """Lights up the LEDs to show sensor readings in binary"""
        while not self.shutdown_event.is_set():
            with self.lock:
                temp = self.data["temperature"]
                hum = self.data["humidity"]

            if self.active:
                if temp is not None and hum is not None:
                    match self.display_mode:
                        case 0:
                            self.update_bit_leds(self.get_bits(int(temp)))
                        case 1:
                            self.update_bit_leds(self.get_bits(int(hum)))
                        case 2:
                            self.shift_reg.clear_input()
                            self.shift_reg.update_output()

            sleep(UPDATE_FREQUENCY)

    def watchdog_thread(self):
        """
        Monitors the last sensor readings. If all readings are identical, closes the process, forcing a restart.
        The number of readings checked is defined in the constant WATCHDOG_THRESHOLD.
        """
        while not self.shutdown_event.is_set():
            with self.lock:
                if len(self.last_readings) >= WATCHDOG_THRESHOLD:
                    first_reading = self.last_readings[0]
                    # Checks if all readings are the same: compares both temp ([0]) and hum ([1])
                    all_readings_are_identical = all(
                        reading[0] == first_reading[0]
                        and reading[1] == first_reading[1]
                        for reading in self.last_readings
                    )
                    if all_readings_are_identical:
                        print(
                            f"Watchdog: Last {WATCHDOG_THRESHOLD} readings are identical, forcing a restart."
                        )
                        _exit(1)
            sleep(5)
    
    def monitor_shutdown_thread(self):
        """Cleans up and closes the program when shutdown_event is set"""
        self.shutdown_event.wait()
        self.cleanup()
        sys.exit()


if __name__ == "__main__":
    main()
