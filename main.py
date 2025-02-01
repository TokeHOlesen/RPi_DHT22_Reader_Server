import adafruit_dht
import board
from time import sleep
from gpiozero import Button, LED

from constants import *
from log_data_function import log_data
from shift_register_class import ShiftRegister


def main():
    controller = Controller()
    controller.run()


class Controller:
    def __init__(self):
        # Initializes the DHT22 sensor
        self.dht22 = adafruit_dht.DHT22(board.D23)

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
        self.on_off_button = Button(ON_OFF_BTN_PIN, bounce_time=0.15)
        self.off_led = LED(OFF_LED_PIN)
        self.on_led = LED(ON_LED_PIN)

        self.cycle_button = Button(CYCLE_BUTTON_PIN, bounce_time=0.15)
        
        self.on_off_button.when_pressed = self.on_off_button_press_event
        self.cycle_button.when_pressed = self.cycle_button_press_event

        # 0 for no temperature, 1 for humidity, 2 for no leds
        self.display_mode = 0

        self.read_sensor = False

        self.update_on_off_leds()
        
    def update_on_off_leds(self):
        if self.read_sensor:
            self.on_led.on()
            self.off_led.off()
        else:
            self.on_led.off()
            self.off_led.on()

    def get_bits(self, number):
        bits = []
        for i in range(8):
            bits.append(number >> i & 1)
        return bits
        
    def on_off_button_press_event(self):
        self.shift_reg.clear_input()
        self.shift_reg.update_output()
        self.read_sensor = not self.read_sensor
        self.update_on_off_leds()
            
    def cycle_button_press_event(self):
        self.display_mode = (self.display_mode + 1) % 3

    def update_bit_leds(self, bits):    
        for bit in bits:
            self.shift_reg.load_bit(bit)
            
    def run(self):
        while True:
            try:
                if self.read_sensor:
                    temp = self.dht22.temperature
                    hum = self.dht22.humidity
                    print(f"Temp: {temp}, humidity: {hum}")
                    log_data(temp, hum)
                    
                    if self.display_mode == 0:
                        self.update_bit_leds(self.get_bits(int(temp)))
                    elif self.display_mode == 1:
                        self.update_bit_leds(self.get_bits(int(hum)))
                    elif self.display_mode == 2:
                        self.shift_reg.clear_input()
                        
                    self.shift_reg.update_output()
                    sleep(LOG_FREQUENCY)
            except Exception as e:
                print(str(e))
                

if __name__ == "__main__":
    main()
    