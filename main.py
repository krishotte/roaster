# roast tool main v05 - basic socket communication
# 4 actual data fields
# automatically updated monitor screen
# file management class, data management classes, serial data get class
# functional start, stop button, proper enable/disable buttons
# pagelayout main screen
# added graph display functionality, automatic time axis adjustment
# TODO: restart time counter through the socket command
import serial
#import serial.tools.list_ports
import time
import random
import datetime
import math
import socket
import struct

from kivy.app import App

from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.pagelayout import PageLayout
from kivy.uix.scrollview import ScrollView
from kivy.garden.graph import Graph, MeshLinePlot

from kivy.properties import StringProperty
from kivy.clock import Clock


class DataGenRandom:                            #data generator class
    def __init__(self):
        self.str1 = ''
        self.i = 0

    def get(self):                              #generates and returns data string
        self.str1 = str(self.i) + ';' + str(random.randint(200,240) + round(random.random(),1)) + ';' 
        self.str1 += str(round(random.random()*210,1)) + ';' + str(round(random.random()*200,1))  + '\n'
        self.i += 0.5
        return self.str1

    def start(self):
        pass

    def check(self):                            #checks available bytes in port
        return 24


class DataGenLinear:                            #linear data generator class
    def __init__(self):
        self.str1 = ''
        self.i = 0
        self.T1 = 18
        self.T2 = 20

    def get(self):                              #generates and returns data string
        self.str1 = str(self.i) + ';' + str(random.randint(200,240) + round(random.random(),1)) + ';' 
        self.str1 += str(round(self.T1 + random.random(),1)) + ';' + str(round(self.T2 + random.random(),1))  + '\n'
        self.i += 1
        self.T1 += 0.168
        self.T2 += 0.2
        return self.str1

    def start(self):
        pass

    def check(self):                            #checks available bytes in port
        return 24


class DataGetSerial:                            #data Serial class
    def __init__(self):
        self.str1 = ''
        port = list(serial.tools.list_ports.comports())[0]     #lists serial port 
        self.S1 = serial.Serial("COM11", 9600)              #port.device - COM port name
        print(port.device)

    def start(self):                            #starts measurement
        self.S1.write('s'.encode())             #sends start 's' string
        started = False
        while started == False:
            if self.check() < 24:               #repeatedly sends 's' string when meas did not start
                self.S1.write('s'.encode())
            try:
                line = self.S1.readline().decode()
            except ValueError:
                #line = "0;0;0;0"
                pass
            print('bytes at port: ' + str(self.check()) + '; garbage: ' + line)     #diagnostic line
            if line == 's\r\n':                 #checks arduino response - should get 's\r\n'
                started = True                  #measurement started

    def stop(self):                             #currently not used
        self.S1.write('e')

    def get(self):                              #reads data/line from serial port
        try:
            str2 = self.S1.readline().decode() #.rstrip('\r\n') + '\n' #removes \r from string i.e. empty line in file
        except ValueError:
            #str2 = "0;0;0;0"
            pass
        print(str2)        #diagnostic line
        return str2

    def check(self):                            #checks available bytes in port
        return self.S1.in_waiting


class DataGetESP32:
    def __init__(self, ipaddr='127.0.0.1', output_str=True):
        self.ipaddr = ipaddr
        self.output_str = output_str
        self.i = 0
        self.T1 = 20
        self.T2 = 20
        self.str1 = ''  # f'{self.i};0;{self.T1};{self.T2}'
        self.start_time = None
        self.socket = None

    def get(self):
        """
        handles data communication with data source
        :return: data in string
        # TODO_: returned data to be replaced with list
        """
        try:
            # TODO_: GUI is unrensponsive when waiting for data on socket
            # could be eliminated by lowering socket.settimeout
            # TODO_: when socket.recv times out return empty data - need to be handled in main update method
            data = self.socket.recv(16)
        except (socket.timeout, ConnectionResetError):
            # TODO_: split socket.timeout - to get responsiveness in GUI
            print(' socket timeout')
            str1 = ''  # '0;0;0;0\n'
            data1 = []
        except ConnectionResetError:
            print(' unable to connect')
            str1 = ''  # '0;0;0;0\n'
            data1 = []
            try:
                self.reconnect()
            except ConnectionRefusedError:
                print(' server socket not available')
        else:
            try:
                # time(seconds), U_ef(volts), T1(deg C), T2(deg C)
                decoded_data = struct.unpack('>ffff', data)
                print(' received data:', decoded_data)
                str1 = str(round(decoded_data[0], 0)) + ';' + str(round(decoded_data[1], 1)) + ';'
                str1 += str(round(decoded_data[2], 1)) + ';' + str(round(decoded_data[3], 1)) + '\n'
                data1 = list(decoded_data)
            except struct.error:
                str1 = ''  # '0;0;0;0\n'
                data1 = []
                try:
                    self.reconnect()
                except ConnectionRefusedError:
                    print(' server socket not available')
            print(' str1: ', str1)
        if self.output_str is True:
            return str1
        else:
            return data1

    def start(self):
        # TODO_: replace hardcoded IP
        # socket.timeout - 0.2 to get responsive GUI, possibly even lower
        self.start_time = datetime.datetime.utcnow()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.2)
        self.socket.connect((self.ipaddr, 8003))

    def stop(self):
        self.socket.close()
        self.socket = None

    def reconnect(self):
        self.stop()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.2)
        try:
            self.socket.connect((self.ipaddr, 8003))
        except socket.timeout:
            print(' reconnecting, but timed out')

    def check(self):
        return 24


class RawData:
    """
    contains raw string data
    # TODO: while using struct raw string data should be deprecated
    """
    def __init__(self):
        self.Raw = ""

    def add(self, str1):
        self.Raw = str1 + self.Raw

    def getRaw(self):                           #gets all data
        return self.Raw

    def getRawFirst(self, rows):                #gets requested number of rows
        lines = self.Raw.splitlines()
        length = len(lines)
        str1 = ''
        if length > rows:
            length = rows
        for i in range(length):
            str1 += lines[i] + '\n'
        return str1


class DataPoint:
    """
    contains single data point
    """
    def __init__(self):
        self.time = 0
        self.Uef = 0
        self.T1 = 0
        self.T2 = 0
        self.Pwr = 0

    def add(self, str1):
        strgs = str1.split(';')
        self.time = float(strgs[0])
        self.Uef = float(strgs[1])
        self.T1 = float(strgs[2])
        self.T2 = float(strgs[3])
        self.Pwr = self.Uef ** 2 / 41.5

    def gettime(self):
        return self.time

    def gettimestr(self):                       #formats time for proper time display mm:ss
        str1 = str(int(self.time//60)) + ':' + str(format(int(round(self.time%60, 0)), '02d'))
        return str1

    def getUef(self):
        return self.Uef

    def getT1(self):
        return self.T1

    def getT2(self):
        return self.T2

    def getPwr(self):
        return self.Pwr


class DataTuplesList:
    """
    contains data in lists of tuples (time, data)
    suitable for kivy.garden.graph
    # TODO_: in add method add possibility to insert list of data instead of string
    """
    def __init__(self, input_str=True):
        self.Uef = []
        self.T1 = []
        self.T2 = []
        self.input_str = input_str

    def add(self, data):
        if self.input_str is True:
            strgs = data.split(';')
            self.Uef.append((float(strgs[0])/60,float(strgs[1])))
            self.T1.append((float(strgs[0])/60,float(strgs[2])))
            self.T2.append((float(strgs[0])/60,float(strgs[3])))
        else:
            self.Uef.append((data[0]/60, data[1]))
            self.T1.append((data[0]/60, data[2]))
            self.T2.append((data[0]/60, data[3]))

    def getUef(self, last_point=False):
        if last_point is False:
            return self.Uef
        else:
            return self.Uef[-1][1]

    def getT1(self, last_point=False):
        if last_point is False:
            return self.T1
        else:
            return self.T1[-1][1]

    def getT2(self, last_point=False):
        if last_point is False:
            return self.T2
        else:
            return self.T2[-1][1]

    def getPwr(self):
        return self.getUef(last_point=True) ** 2 / 41.5

    def gettimestr(self):
        last_time = self.Uef[-1][0] * 60  # time in seconds
        print(' last time: ', last_time)
        str1 = str(int(last_time//60)) + ':' + str(format(int(round(last_time%60, 0)), '02d'))
        return str1

    def get_last_time(self):
        # returns time in minutes
        return self.getUef()[-1][0]

    def clear(self):
        self.Uef = []
        self.T1 = []
        self.T2 = []


class MinuteDelta:
    """
    holds change in temperature for last minute
    """
    def __init__(self):
        self.actDelta = float('NaN')
        self.Deltas = []

    def update(self, DTList):                   #updates actDelta value
        i = -1                                  #searches from the end of the list backwards
        lasttime = DTList.T2[i][0]
        ok = False
        if lasttime > 1:                        #searches only when measurement started more than minute ago
            while ok == False and abs(i) < len(DTList.T2):                  #searches for actual minute delta
                if (lasttime - DTList.T2[i][0]) >= 1:                       #calculates time delta - when > 1 stops search
                    ok = True
                    self.actDelta = DTList.T2[-1][1] - DTList.T2[i][1]      #calculates value delta
                else:
                    i -= 1
        #print('delta: ' + str(self.actDelta) + ' tlast: ' + str(DTList.T2[-1][1]) + ' tback: ' + str(DTList.T2[i][1]))      #diagnostic print

    def getAct(self):                           #gets actual delta value - outputs float as string
        if math.isnan(self.actDelta) is False:
            return str(round(self.actDelta, 1))
        else:
            return ''

    def clear(self):
        self.actDelta = float('NaN')


class FileWrp:
    """
    file management class
    """
    def __init__(self):
        self.now1 = datetime.datetime.now()
        self.ffname = ''

    def create(self, fname):                    #creates csv file including its head
        self.now1 = datetime.datetime.now()
        self.ffname = 'D:\\Personal\\programovanie\\python\\roastooldata\\' + self.now1.strftime("%Y-%m-%d-%H-%M-%S_") + fname +".csv"
        self.file = open(self.ffname, "a")
        self.file.write(self.now1.strftime("%Y-%m-%d-%H-%M-%S;") + fname + '\n')
        self.file.write("time;Uef;T1;T2\n")
        self.file.close()

    def write(self, str1):                      #writes data to csv file
        self.file = open(self.ffname, "a")
        self.file.write(str1)
        self.file.close()

    def close(self):                            #currently not used
        self.file.close()


class STWidget(BoxLayout):
    """
    main widget class
    # TODO: add __init__
    """
    strtodisplay = StringProperty()

    def __init__(self):
        super().__init__()
        # dGet = DataGenLinear()
        # dGet = DataGetSerial()
        self.dGet = DataGetESP32(ipaddr='192.168.0.6', output_str=False)

        self.file1 = FileWrp()
        self.raw_data = RawData()
        self.last_point = DataPoint()
        self.graph_data = DataTuplesList(input_str=False)
        self.deltas = MinuteDelta()

    def open(self):
        """
        initializes graph
        # TODO: could be moved to __init__
        """
        self.plotT1 = MeshLinePlot(color=[1, 0.2, 0.2, 1])
        self.plotT2 = MeshLinePlot(color=[1, 0.7, 0.2, 1])
        self.plotUef = MeshLinePlot(color=[0.6, 1, 0.2, 1])
        self.plotT1.points = []
        self.plotT2.points = []
        self.plotUef.points = []
        self.ids.graph.add_plot(self.plotT1)
        self.ids.graph.add_plot(self.plotT2)
        self.ids.graph.add_plot(self.plotUef)
     
    def update_textbox(self, *args):
        """
        updates display
        :param args: needed for Clock.schedule
        """
        # TODO: replace bytes available byt try, except clause - new update_gui method
        S1bytes = self.dGet.check()
        if S1bytes >= 24:                           # greatly improves GUI responsiveness
            strg = self.dGet.get()                  #gets string data from data generator object (e.g. serial port)
            self.raw_data.add(strg)                  #adds get data do RawData object
            a1 = self.raw_data.getRawFirst(20)       #gets data to display from RawData object
            self.strtodisplay = a1                  #displays selected data in label
            self.last_point.add(strg)                   #adds data to DataPoint object
            self.graph_data.add(strg)                  #adds data to DataTuplesList object
            self.deltas.update(self.graph_data)             #updates deltas object
            self.ids.time.text = str(self.last_point.gettimestr())
            self.ids.Uef.text = str(int(round(self.last_point.getUef(), 0)))
            self.ids.Pwr.text = str(int(round(self.last_point.getPwr(), 0)))
            self.ids.T1.text = str(round(self.last_point.getT1(), 1))
            self.ids.T2.text = str(round(self.last_point.getT2(), 1))
            self.ids.dT2.text = self.deltas.getAct() #str(round(self.deltas.getAct(),1))
            self.file1.write(strg)
            self.plotT1.points = self.graph_data.getT1()               #data to diplay - list of tuples - points
            self.plotT2.points = self.graph_data.getT2()
            self.plotUef.points = self.graph_data.getUef()
            tmax = self.last_point.gettime()/60                         #data max time in minutes
            tdisp = 15                                              #graph plot length in minutes
            if tmax <= tdisp:
                self.ids.graph.xmax = tdisp
                self.ids.graph.xmin = 0
            else:
                self.ids.graph.xmax = tmax//1 + 1                   #sets time axis max
                self.ids.graph.xmin = tmax//1 - tdisp + 1           #sets time axis min

    def update_gui(self, *args):
        data = self.dGet.get()

        if len(data) > 0:
            print(' data: ', data)
            self.graph_data.add(data)
            self.plotT1.points = self.graph_data.getT1()
            self.plotT2.points = self.graph_data.getT2()
            self.plotUef.points = self.graph_data.getUef()

            self.ids.time.text = str(self.graph_data.gettimestr())
            self.ids.Uef.text = str(int(round(self.graph_data.getUef(last_point=True), 0)))
            self.ids.Pwr.text = str(int(round(self.graph_data.getPwr(), 0)))
            self.ids.T1.text = str(round(self.graph_data.getT1(last_point=True), 1))
            self.ids.T2.text = str(round(self.graph_data.getT2(last_point=True), 1))

            tmax = self.graph_data.get_last_time()  # data max time in minutes
            tdisp = 15  # graph plot length in minutes
            if tmax <= tdisp:
                self.ids.graph.xmax = tdisp
                self.ids.graph.xmin = 0
            else:
                self.ids.graph.xmax = tmax // 1 + 1  # sets time axis max
                self.ids.graph.xmin = tmax // 1 - tdisp + 1  # sets time axis min

            # write data to file
            self.file1.write(f'{data[0]};{data[1]};{data[2]};{data[3]}\n')
        """
        try:

        except:
            raise
        """

    def start(self):
        """
        creates new file, its header
        starts getting data and recording
        :return:
        """
        self.graph_data.clear()                                     #clears DataTuplesList object
        self.deltas.clear()                                         #clears MinuteDelta object
        self.ids.startb.disabled = True                             #disables start button
        self.file1.create(self.ids.sample.text)                     #creates data file - todo - move 1 line downwards
        self.dGet.start()                                           #starts daq
        self.event = Clock.schedule_interval(self.update_gui, 0.5)
        self.ids.stopb.disabled = False                             #enables stop button
        print("start")

    def stop(self):
        """
        stops data recording
        """
        self.ids.stopb.disabled = True
        Clock.unschedule(self.event)
        self.ids.startb.disabled = False
        self.dGet.stop()
        print("stop")


class RoasttoolApp(App):
    def build(self):
        r_widg = STWidget()
        r_widg.open()                           #creates plots in graph
        return r_widg


if __name__ == "__main__":
    RoasttoolApp().run()
