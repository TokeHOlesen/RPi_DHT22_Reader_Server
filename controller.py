import adafruit_dht
import board
import sys
import struct
from time import sleep
from gpiozero import Button, LED
from threading import Event, Lock, Thread
from os import replace

from constants import *
from data_logger_class import DataLogger
from shift_register_class import ShiftRegister


def main():
    controller = Controller()
    sensor_thread = Thread(target=controller.sensor_thread, daemon=True)
    circuit_thread = Thread(target=controller.circuit_thread, daemon=True)
    logging_thread = Thread(target=controller.logging_thread, daemon=True)
    shutdown_monitor_thread = Thread(target=controller.monitor_shutdown, daemon=True)
    sensor_thread.start()
    circuit_thread.start()
    logging_thread.start()
    shutdown_monitor_thread.start()
    sensor_thread.join()
    circuit_thread.join()
    logging_thread.join()
    shutdown_monitor_thread.join()


class Controller:
    def __init__(self):
        # Initializes the DHT22 sensor
        self.dht22 = adafruit_dht.DHT22(board.D23)
        
        # A dictionary to be shared with the flask thread
        self.data = {
            "temperature": None,
            "humidity": None
        }
        
        # A thread lock to prevent race conditions
        self.lock = Lock()

        # Initializes the 75HC95N shift register
        self.shift_reg = ShiftRegister(vcc_pin=VCC_PIN,
                                srclr_pin=SRCLR_PIN,
                                srclk_pin=SRCLK_PIN,
                                rclk_pin=RCLK_PIN,
                                ds_pin=DS_PIN)

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

        # 0 for temperature, 1 for humidity, 2 for no leds
        self.display_mode = 0

        # When True, sensors readings will be taken and data will be logged
        self.read_sensor = False
        
        # When True, the program will end
        self.shutdown_event = Event()

        self.update_on_off_leds()
    
    def update_on_off_leds(self):
        """Turns the On/Off LEDs on or off depending on whether sensor readings are currently being taken."""
        if self.read_sensor:
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
        """Runs when the On/Off button is pressed. Clears the shift register and toggles read_sensor."""
        self.shift_reg.clear_input()
        self.shift_reg.update_output()
        self.read_sensor = not self.read_sensor
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
        
    def cleanup(self):
        self.shift_reg.clear_input()
        self.shift_reg.update_output()
        
        self.on_off_button.close()
        self.cycle_button.close()
        self.on_led.close()
        self.off_led.close()
        

    def sensor_thread(self):
        while not self.shutdown_event.is_set():
            if self.read_sensor:
                try:
                    temp = self.dht22.temperature
                    hum = self.dht22.humidity
                    
                    if temp is not None and hum is not None:
                        print(f"Temp: {temp}, humidity: {hum}")
                            
                        with self.lock:
                            self.data["temperature"] = temp
                            self.data["humidity"] = hum
                                 
                except Exception as e:
                    print(str(e))
                with open(RAM_TEMP_FILE_PATH, "wb") as ram_file:
                    ram_file.write(struct.pack("ff", temp, hum))
                replace(RAM_TEMP_FILE_PATH, RAM_FILE_PATH)
            sleep(LOG_FREQUENCY)
    
    def logging_thread(self):
        # Initializes the SQL data logger
        self.data_logger = DataLogger(SQL_FILE_PATH)
        while not self.shutdown_event.is_set():
            with self.lock:
                temp = self.data["temperature"]
                hum = self.data["humidity"]
            if temp is not None and hum is not None:
                self.data_logger.log_data(temp, hum)
            sleep(10)
        self.data_logger.close()
    
    def circuit_thread(self):
        while not self.shutdown_event.is_set():
            with self.lock:
                temp = self.data["temperature"]
                hum = self.data["humidity"]
            
            if self.read_sensor:
                if temp is not None and hum is not None:
                    match self.display_mode:
                        case 0:
                            self.update_bit_leds(self.get_bits(int(temp)))
                        case 1:
                            self.update_bit_leds(self.get_bits(int(hum)))
                        case 2:
                            self.shift_reg.clear_input()
                            self.shift_reg.update_output()
            
            sleep(LOG_FREQUENCY)

    def monitor_shutdown(self):
        self.shutdown_event.wait()
        self.cleanup()
        sys.exit()


if __name__ == "__main__":
    main()
    