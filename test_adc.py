from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
import random
import socket
import struct

kv = '''
#:kivy 1.10.1

<MainV>:
    orientation: 'vertical'
    Label:
        text: 'status'
        size_hint_y: 0.1
        size_y: sp(18)
    Graph:
        size_hint_y: 0.9
        id:graph
        font_size: 12
        xmin: 0
        xmax: 200
        ymin: 0
        ymax: 5
        x_grid_label:True
        y_grid_label:True
        x_grid:True
        y_grid:True
        x_ticks_major: 20
        y_ticks_major: 1
        xlabel: 'point'
        ylabel: 'U'
        padding_x: 20
        canvas.before:
            Color:
                rgba: 0.1, 0.1, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size  
'''

Builder.load_string(kv)


class Comm:
    def __init__(self, ipaddr):
        self.ipaddr = ipaddr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(3)
        # self.socket.connect(('192.168.43.6', 8003))
        self.socket.connect((self.ipaddr, 8003))

    def get_data_point(self):
        try:
            data = self.socket.recv(4)
        except (socket.timeout, ConnectionResetError):
            print(' socket timeout')
            decoded_data = None
            # str1 = '0;0;0;0\n'
            try:
                self.reconnect()
            except ConnectionRefusedError:
                print(' server socket not available')
        else:
            try:
                decoded_data = struct.unpack('>f', data)[0]
                print(' received data:', decoded_data)
                # str1 = str(round(decoded_data[0], 0)) + ';' + str(round(decoded_data[1], 1)) + ';'
                # str1 += str(round(decoded_data[2], 1)) + ';' + str(round(decoded_data[3], 1)) + '\n'
            except struct.error:
                decoded_data = None
                try:
                    self.reconnect()
                except ConnectionRefusedError:
                    print(' server socket not available')
            # print(' str1: ', str1)
        return decoded_data

    def get_sequence(self):
        data_sequence = []
        for i in range(200):
            data_sequence.append(self.get_data_point())
        return data_sequence

    def stop(self):
        self.socket.close()
        self.socket = None

    def reconnect(self):
        self.stop()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        try:
            self.socket.connect((self.ipaddr, 8003))
        except socket.timeout:
            print(' reconnecting, but timed out')


class MainV(BoxLayout):
    def __init__(self):
        super().__init__()
        self.plot1 = MeshLinePlot(color=[1, 0.2, 0.2, 1])
        self.plot1.points = []  # self.generate_random_data()
        self.ids.graph.add_plot(self.plot1)
        self.data_comm = Comm('127.0.0.1')
        self.event1 = Clock.schedule_interval(self.update, 0.3)

    def update(self, *args):
        data = self.data_comm.get_sequence()
        print(' data: ', data)
        graph_data = []
        for i in range(len(data)):
            graph_data.append((i, data[i]))
        self.plot1.points = graph_data

    def generate_random_data(self):
        graph_data = []
        for i in range(200):
            graph_data.append((i, random.random() + 2))
        return graph_data


class TestADC(App):
    def build(self):
        return MainV()


if __name__ == '__main__':
    TestADC().run()
