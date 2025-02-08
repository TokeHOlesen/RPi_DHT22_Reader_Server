from gpiozero import DigitalOutputDevice


class ShiftRegisterInput(DigitalOutputDevice):
    """A child class of DigitalOutputDevice, adding methods for cycling voltages."""
    def __init__(self, gpio_pin):
        super().__init__(gpio_pin)

    def cycle_low_high(self):
        self.off()
        self.on()

    def cycle_high_low(self):
        self.on()
        self.off()


class ShiftRegister:
    """Used to control a shift register. Facilitates data input and output."""
    def __init__(self, vcc_pin, srclr_pin, srclk_pin, rclk_pin, ds_pin):
        self.vcc = ShiftRegisterInput(vcc_pin)
        self.srclr = ShiftRegisterInput(srclr_pin)
        self.srclk = ShiftRegisterInput(srclk_pin)
        self.rclk = ShiftRegisterInput(rclk_pin)
        self.ds = ShiftRegisterInput(ds_pin)

    def power_on(self):
        self.vcc.on()

    def power_off(self):
        self.vcc.off()

    def load_bit(self, bit):
        if bit:
            self.ds.on()
        else:
            self.ds.off()
        self.srclk.cycle_high_low()

    def clear_input(self):
        self.srclr.cycle_low_high()

    def update_output(self):
        self.rclk.cycle_high_low()
