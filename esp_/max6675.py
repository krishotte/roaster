from machine import Pin, SPI
import ustruct as struct
import utime as time


class MAX6675:
    def __init__(self, ctrl_pins):
        self.ctrl_pins = {}
        for each in ctrl_pins:
            if each not in [18, 19, 23]:
                pin_ = {each: Pin(each, Pin.OUT, value=1)}
                # self.ctrl_pins.update(each=Pin(each, Pin.OUT, value=1))
                self.ctrl_pins.update(pin_)
            else:
                print('conflicting pin setup: ', each)
        self.hspi = SPI(2, 1000000, sck=Pin(19), mosi=Pin(23), miso=Pin(18), firstbit=SPI.MSB, phase=1)

        # ctrl_pin1 = Pin(22, Pin.OUT, value=1)
        # hspi = SPI(2, 1000000, sck=Pin(19), mosi=Pin(23), miso=Pin(18), firstbit=SPI.MSB, phase=1)

    def read_bytes(self, ctrl_pin):
        """
        reads raw bytes from sensor over the SPI bus
        :return: bytes string - 2 bytes
        """
        try:
            '''
            ctrl_pin1.value(0)
            time.sleep_ms(2)
            ctrl_pin1.value(1)
            time.sleep_ms(220)
            ctrl_pin1.value(0)
            temp = hspi.read(2)
            ctrl_pin1.value(1)
            '''
            pin_ = self.ctrl_pins[ctrl_pin]
            pin_.value(0)
            time.sleep_ms(2)
            pin_.value(1)
            time.sleep_ms(220)
            pin_.value(0)
            temp = self.hspi.read(2)
            pin_.value(1)
        except KeyError:
            print('requested pin not defined')
            temp = None
        return temp

    def read_bits(self, ctrl_pin):
        """
        diagnostic function
        :return:
        """
        bytes_ = self.read_bytes(ctrl_pin)
        int_ = struct.unpack('>H', bytes_)[0]
        bits_ = '{0:016b}'.format(int_)
        print('bytes: ', bytes_, ' bits: ', bits_)
        print('sensor connected: ', '{0:016b}'.format(int_ & 0x04), 'raw value: ', '{0:016b}'.format(int_ >> 3))
        print('celsius: ', (int_ >> 3) * 0.25)
        return bits_

    def read_temp(self, ctrl_pin):
        """
        reads temperature in deg celsius
        :return: temperature in deg celsius
        """
        bytes_ = self.read_bytes(ctrl_pin)
        int_ = struct.unpack('>H', bytes_)[0]
        if int_ & 0x04 > 1:
            temp_celsius = -1
        else:
            temp_celsius = (int_ >> 3) * 0.25
        return temp_celsius

    def read_bits_c(self, ctrl_pin):
        """
        infinite diagnostic read cycle
        :return:
        """
        while True:
            self.read_bits(ctrl_pin)
            time.sleep(1)
