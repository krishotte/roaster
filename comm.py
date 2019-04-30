# module handles communication with app
# network connection with AP
# socket connection with main app

import os
import socket

if os.__name__ == 'uos':
    import network
    import utime
    import machine
    from m_file import uini
    import uping
    import ustruct as struct
    import uselect
else:
    import struct
    import selectors


if os.__name__ == 'uos':
    # global variables:
    pwm_freq = 5000
    p_sig = machine.PWM(machine.Pin(2), freq=pwm_freq)
    p_sig.duty(100)


class NetworkConn:
    """
    manages network connectivity
    provide configuration file name on init
    """
    def __init__(self, config_file=None):
        self.sta_if = network.WLAN(network.STA_IF)
        print('network is active: ', self.sta_if.active())
        self.sta_if.active(True)
        self.ini = uini()
        self.config_file = config_file

        self.conf = {
            'ssid': 'vlmaba3',
            'passwd': 'pricintorine1320',
            'gateway': '192.168.0.1',
            'ipaddr': '192.168.0.6',
        }
        self.load_config()

    def load_config(self):
        loaded_conf = self.ini.read(self.config_file)
        self.conf.update(loaded_conf)
        print('loaded config: ', self.conf)

    def connect2(self):
        """
        connects to AP
        improved preferred connect method
        """
        self.sta_if.ifconfig((self.conf['ipaddr'],'255.255.255.0', self.conf['gateway'], self.conf['gateway']))
        self.sta_if.connect(self.conf['ssid'], self.conf['passwd'])
        utime.sleep(5)
        print('is connected? (sta_if): ', self.sta_if.isconnected())
        print('ifconfig: ', self.sta_if.ifconfig())
        check_conn = self.check_conn()
        print('network connected: ', check_conn)
        if check_conn is True:
            p_sig.duty(10)
        else:
            p_sig.duty(0)

    def check_conn(self):
        """
        checks network connection by pinging gateway
        uses uping.py
        """
        print('is connected? (sta_if): ', self.sta_if.isconnected)
        try:
            ping_status = uping.ping(self.conf['gateway'])
            if ping_status == (4, 4):
                conn_status = True
                print('ping: connected')
            else:
                conn_status = True
                print('ping: some packets lost')
        except OSError:
            print('ping: not connected')
            conn_status = False
        return conn_status

    def close(self):
        print('disconnecting network...')
        self.sta_if.disconnect()
        print('network connected: ', self.check_conn())
        p_sig.duty(0)


class SocketServer:
    """
    manages socket server
    provide ip address to set and network_conn instance on init
    """
    def __init__(self, conn_conf):
        self.ipaddr = conn_conf['ipaddr']
        # self.sdata = socket_data()
        # self.duty0 = 10
        # self.duty1 = 10
        # self.conn = conn
        self.last_conn_check = 0
        self.server_socket = None
        self.client_socket = None
        self.client_address = None

    def start(self, timeout=None):
        """
        starts socket server,
        waits for incomming connection for timeout (s) period
        """
        self.timeout = timeout
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # self.serversocket.setblocking(False)
        self.server_socket.setblocking(True)
        self.server_socket.settimeout(timeout)
        print('binding server socket...')
        self.server_socket.bind((self.ipaddr, 8003))
        self.server_socket.listen(5)

    def close(self):
        """
        closes socket server
        to begin again, run start method
        """
        print('closing client socket')
        if self.client_socket is not None:
            self.client_socket.close()
            self.client_socket = None
        print('closing socket server')
        self.server_socket.close()
        self.server_socket = None

    def listen(self):
        '''
        waits for incomming connection for timeout (s) period
        '''
        print('listening ...')
        try:
            (self.client_socket, self.client_address) = self.server_socket.accept()
        except OSError as err:
            if err.args[0] == 110:
                print('socket timeout')
            else:
                raise

    def socket_send(self, data, format='>dddd'):
        print('socket sending ...')
        encoded_data = struct.pack(format, *data)
        print(' data: ', data, '; encoded data :', encoded_data)
        bytes_sent = self.client_socket.send(encoded_data)
        print('  bytes sent: ', bytes_sent)

    def socket_recv(self, bytes=32, format='>dddd'):
        print('socket receiving ...')
        bytes_received = self.client_socket.recv(bytes)
        data = struct.unpack(format, bytes_received)
        return data

    def listen_indef(self):
        '''
        waits for incoming connection in indefinite loop
        '''
        counter = 0
        while True:
            counter += 1
            print('counter: ', counter, ', listening...')
            # print('listening ...')
            self.check_comm()
            try:
                (self.client_socket, self.client_address) = self.server_socket.accept()
            except OSError as err:
                if err.args[0] == 110:
                    print('socket timeout')
                else:
                    print(err)
                    raise
            else:
                print('message communicating...')
                # self.exchange_comm()
                # print('client socket closing...')
                # self.client_socket.close()

    def exchange_comm(self):
        '''
        communicates with client
        '''
        cmd1 = 0
        count = 0
        while (cmd1 == 5) or (count < 2):  # count < 1: #(cmd1 != 5) and (count < 5):
            count += 1
            str1 = self.client_socket.recv(32)
            print('count: ', count, 'str1: ', str1)
            try:
                a1 = self.sdata.deconstr(str1)
            except:
                print('Error: incomplete message')
            else:
                cmd1 = a1[0]
                chn = a1[1]
                duties = a1[2]
                '''
                print('str1: ', str1)
                print('a1: ', a1)
                print('cmd: ', cmd1)
                print('chn: ', chn)
                print('duties: ', duties)
                '''
                print('cmd: ', cmd1, ' , chn: ', chn, ' , duties: ', duties)
                if cmd1 == 1:
                    str2 = self.sdata.constr(3, 0, [self.duty0, self.duty1, 0, 0])
                    self.client_socket.send(str2)  # b'0x30x00x00x00xff0xb20x7f0xdd')
                elif cmd1 == 2:
                    self.duty0 = duties[0]
                    self.duty1 = duties[1]
                    p0.duty(self.duty0 * 1023 // 100)
                    p1.duty(self.duty1 * 1023 // 100)
                    str2 = self.sdata.constr(3, 0, [self.duty0, self.duty1, 0, 0])
                    self.client_socket.send(str2)  # b'0x30x00x00x00xdd0xb20x7f0xaa')
                elif cmd1 == 5:
                    print('success')
                    self.client_socket.send(b'0x50x00x00x00x00x00x00x00')

    def check_comm(self):
        '''
        checks network connection by pinging gateway
        reconnects if necessary
        '''
        actual_time = utime.time()
        if (actual_time - self.last_conn_check) > self.timeout * 5:
            print('checking network connection')
            self.last_conn_check = actual_time
            connected = self.conn.check_conn()
            if connected == False:
                # what about running socket connection?
                # will it still be running after network restart?
                self.close()
                print('closing network connection')
                self.conn.close()
                print('establishing network connection...')
                # TODO not tested
                self.conn.connect2()
                self.start()
                self.listen_indef()


class SocketServerNB(SocketServer):
    def start(self, timeout=None):
        self.timeout = timeout
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        print('binding server socket...')
        self.server_socket.bind((self.ipaddr, 8003))
        print('listening...')
        self.server_socket.listen(5)

        if os.__name__ == 'uos':
            self.sel = uselect.poll()
            self.sel.register(self.server_socket, uselect.POLLIN)
        else:
            self.sel = selectors.DefaultSelector()
            self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)

    def close(self):
        print('closing socket server')
        self.sel.unregister(self.server_socket)
        self.server_socket.close()
        self.server_socket = None
        self.client_socket = None

    def check_clients(self):
        if os.__name__ == 'uos':
            events = self.sel.poll(1000)
            print('events: ', events)
            try:
                (self.client_socket, self.client_address) = events[0][0].accept()
                print('client connected :', self.client_address)
            except IndexError:
                print(' no clients connected')
        else:
            events = self.sel.select(timeout=self.timeout)
            try:
                (self.client_socket, self.client_address) = events[0][0].fileobj.accept()
                print('client connected :', self.client_address)
            except IndexError:
                print(' no clients connected')

    def client_close(self):
        print('closing client socket')
        self.client_socket.close()
        self.client_socket = None
