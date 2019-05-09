# microcontroller side of the app

import comm
import random
import ustruct as struct
import utime as time
import gc
from ucollections import deque
from machine import Pin, I2C
#from esp_ import ads1x15, max6675, zmpt
#import ads1x15
import max6675
import zmpt
import ssd1306


network_conn = comm.NetworkConn('conf.json')
socket = comm.SocketServer(network_conn.conf)
socket_nb = comm.SocketServerNB(network_conn.conf)
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=4000000)
print(' i2c devices: ', i2c.scan())
disp = ssd1306.SSD1306_I2C(128, 64, i2c)


def test_send(cycles=3):
    stop = False
    network_conn.connect2()
    socket.start()
    socket.listen()
    i = 0.0
    while stop is False:
        data = [
            i,
            random.random()*20+180,
            random.random()*15+30,
            random.random()*50+100,
        ]
        i += 0.5
        try:
            socket.socket_send(data)
        except OSError:
            socket.close()
            print('reconnecting socket')
            socket.start()
            socket.listen()
        time.sleep(0.5)


def test_nb_socket(random_data=False):
    """
    test function for non blocking server socket
    automatically reconnects after client disconnect
    stores data in queue
    :return:
    """
    network_conn.connect2()
    socket_nb.start()
    zmpt1 = zmpt.ZMPT101B(i2c, samples=172, use_irq=False, use_ad1115=True)
    max1 = max6675.MAX6675([21, 22])
    time_start = time.ticks_ms()
    i = 0
    queue1 = deque((), 2000)
    while True:
        # get data into data list and send them to queue
        # generate some random data
        if random_data is True:
            data = [
                i,
                random.random() * 20 + 180,
                random.random() * 15 + 30,
                random.random() * 50 + 100,
            ]
            i += 1.0
        # read actual data from sensors
        else:
            time1 = time.ticks_ms()
            time_ = (time1 - time_start) / 1000
            # uef_ = zmpt1.true_rms(zmpt1.get_meas())[0]
            uef_ = zmpt1.average_rms(zmpt1.get_meas())[0]
            T1_ = max1.read_temp(21)
            T2_ = max1.read_temp(22)
            data = [
                time_,
                uef_,
                T1_,
                T2_,
            ]
            display(time_, uef_, T1_, T2_, 'roasting')

            measurement_time = (time.ticks_ms() - time1) / 1000
            print(' measurement time: ', measurement_time)
        queue1.append(data)
        print('queue length: ', len(queue1))

        # send data to client, if connected
        if socket_nb.client_socket is None:
            socket_nb.check_clients()
        if socket_nb.client_socket is not None:
            while len(queue1) > 1:
                try:
                    # TODO: some queue elements gets lost when sending fails not more than 9
                    # probably when cs is closed and buffer is not empty
                    socket_nb.socket_send(queue1.popleft())
                except AttributeError:
                    print('client not connected')
                except OSError:
                    # TODO_: client socket close should be enough, while server is still listening - needs testing
                    socket_nb.client_close()
                    # socket_nb.close()
                    # socket_nb.start()
        gc.collect()
        print('free memory', gc.mem_free())
        time.sleep(1)


def display(time, Uef, T1, T2, message):
    disp.fill(0)
    disp.text(str(message), 0, 0)
    disp.text(time_to_str(time), 0, 10)
    disp.text(str(round(Uef)), 0, 20)
    disp.text(str(T1), 0, 30)
    disp.text(str(T2), 64, 30)
    disp.show()


def time_to_str(time):
    minutes_ = str(round(time) % 60)
    if len(minutes_) < 2:
        minutes_ = '0' + minutes_
    return str(round(time)//60) + ':' + minutes_


if __name__ == '__main__':
    time_to_str(101)
