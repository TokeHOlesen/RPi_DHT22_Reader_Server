import adafruit_dht
import board

from time import sleep
from gpiozero import Button, LED
from log_data_function import log_data

from shift_register_class import ShiftRegister

# How often to read and log data, in seconds
LOG_FREQUENCY = 1

dht22 = adafruit_dht.DHT22(board.D23)

on_off_button = Button(2, bounce_time=0.15)
temp_humi_button = Button(21)
off_led = LED(17)
on_led = LED(27)

shift_reg = ShiftRegister(vcc_pin=4,
                          srclr_pin=3,
                          srclk_pin=24,
                          rclk_pin=16,
                          ds_pin=20)

shift_reg.power_on()
shift_reg.clear_input()
shift_reg.update_output()

# 0 for no temperature, 1 for humidity, 2 for no leds
display_mode = 0

read_sensor = False

if read_sensor:
    on_led.on()
else:
    off_led.on()


def get_bits(number):
    bits = []
    for i in range(8):
        bits.append(number >> i & 1)
    return bits
    

def on_off_button_press_event():
    global read_sensor, off_led
    shift_reg.clear_input()
    shift_reg.update_output()
    read_sensor = not read_sensor
    if read_sensor:
        off_led.off()
        on_led.on()
    else:
        off_led.on()
        on_led.off()


def temp_humi_button_press_event():
    global display_mode
    display_mode = (display_mode + 1) % 3


def update_bit_leds(bits):    
    for bit in bits:
        shift_reg.load_bit(bit)
    

on_off_button.when_pressed = on_off_button_press_event
temp_humi_button.when_pressed = temp_humi_button_press_event

try:
    while True:
        try:
            if read_sensor:
                temp = dht22.temperature
                hum = dht22.humidity
                print(f"Temp: {temp}, humidity: {hum}")
                log_data(temp, hum)
                
                if display_mode == 0:
                    update_bit_leds(get_bits(int(temp)))
                elif display_mode == 1:
                    update_bit_leds(get_bits(int(hum)))
                elif display_mode == 2:
                    shift_reg.clear_input()
                shift_reg.update_output()

                sleep(LOG_FREQUENCY)
        except Exception as e:
            print(str(e))
except KeyboardInterrupt:
    pass