import ads1x15
from machine import Pin, I2C, ADC
from comm import SocketServer, NetworkConn
import ustruct as struct
import utime
from math import sqrt
from ucollections import deque

# i2c = I2C(scl=Pin(18), sda=Pin(19), freq=400000)


class ZMPT101B:
    def __init__(self, i2c, use_irq=True, samples=34, use_ad1115=False):
        self.samples = samples
        self.use_irq = use_irq
        self.use_ad1115 = use_ad1115
        self.ads1115 = ads1x15.ADS1115(i2c, gain=0)
        self.data_queue = deque((), self.samples)
        if use_irq is True:
            self.irq_pin = Pin(35, Pin.IN)
            self.irq_pin.irq(self.irq_handler, Pin.IRQ_FALLING)

        if use_ad1115 is False:
            self.internal_adc = ADC(Pin(32))
            self.internal_adc.atten(ADC.ATTN_11DB)
            self.internal_adc.width(ADC.WIDTH_12BIT)

    def irq_handler(self, pin):
        self.data_queue.append(self.ads1115.raw_to_v(self.ads1115.alert_read()))
        if len(self.data_queue) >= self.samples:
            self.ads1115.set_conv()  # stops continuous conversion mode

    def get_meas(self):
        meas = []

        if self.use_ad1115 is True:
            if self.use_irq is True:
                while bool(self.data_queue) is True:
                    self.data_queue.popleft()

                queue_full = False

                while queue_full is False:
                    # print('checking queue: ', len(self.data_queue))
                    if len(self.data_queue) >= self.samples:
                        queue_full = True
                        print(' queue full: ', queue_full)
                    utime.sleep_ms(40)
                # TODO: read from queue
            else:
                self.ads1115.conversion_start(rate=7)

                zmpt_start = utime.ticks_ms()
                for i in range(self.samples):
                    time_1 = utime.ticks_us()
                    meas.append(self.ads1115.raw_to_v(self.ads1115.alert_read()))
                    time_2 = utime.ticks_us()
                    utime.sleep_us(1163 - (time_2 - time_1))
                zmpt_stop = utime.ticks_ms()
                print(' last cycle time: ', time_2 - time_1)
                print(' zmpt meas time: ', zmpt_stop - zmpt_start)
        else:
            while bool(self.data_queue) is True:
                self.data_queue.popleft()

            adc_start = utime.ticks_ms()
            for i in range(self.samples):
                time_3 = utime.ticks_us()
                self.data_queue.append(self.internal_adc.read())
                time_4 = utime.ticks_us()
                utime.sleep_us(200 - (time_4 - time_3))
            adc_stop = utime.ticks_ms()
            print(' last cycle time: ', time_4 - time_3)
            print(' internal adc meas time: ', adc_stop - adc_start, ' ms')

            for i in range(self.samples):
                raw_meas = self.data_queue.popleft()
                meas.append(3.6 / 4096 * raw_meas)
        """
        while queue_full is False:
            # print('checking queue: ', len(self.data_queue))
            if len(self.data_queue) >= self.samples:
                queue_full = True
                print(' queue full: ', queue_full)
            utime.sleep_ms(40)
        """
        """
        for i in range(samples):
            # meas.append(self.ads1115.raw_to_v(self.ads1115.read(rate=7)))
            # meas.append(self.ads1115.raw_to_v(self.ads1115.read_rev()))
            meas.append(self.ads1115.raw_to_v(self.ads1115.alert_read()))
            utime.sleep_ms(1)
        """
        # for i in range(len(self.data_queue)):
        #     meas.append(self.data_queue.popleft())
        return meas

    def U_ef(self, data, multiplier=443):
        mean = (max(data) + min(data)) / 2
        sum_squared = 0
        sum_squared_raw = 0
        for each in data:
            sum_squared += ((each - mean) * multiplier) ** 2
            sum_squared_raw += (each - mean) ** 2
        rms = sqrt(sum_squared / len(data))
        rms_raw = sqrt(sum_squared_raw / len(data))
        print(' rms: ', rms, ' mean: ', mean, ' rms_raw: ', rms_raw)
        return [rms, mean, rms_raw]


def test_conti():
    i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
    zm = ZMPT101B(i2c, use_irq=False, samples=200)
    # net = NetworkConn('conf.json')
    # net.connect2()
    # ssock = SocketServer(net.conf)  # {'ipaddr': '192.168.0.6'})
    # ssock.start()
    # ssock.listen()

    while True:
        data = zm.get_meas()
        pdata = zm.U_ef(data)
        print('data: ', data)
        #for each in data:
        #    ssock.client_socket.send(struct.pack('>f', each))

        utime.sleep(2)
