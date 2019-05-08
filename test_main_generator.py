import socket
import selectors
import time
from collections import deque
from random import random
import struct


class SocketServerNB():
    def __init__(self, debug=False):
        self.ipaddr = '127.0.0.1'
        # self.sdata = socket_data()
        # self.duty0 = 10
        # self.duty1 = 10
        # self.conn = conn
        self.last_conn_check = 0
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.debug = debug

    def start(self, timeout=None):
        self.timeout = timeout
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        print('binding server socket...')
        self.server_socket.bind((self.ipaddr, 8003))
        print('listening...')
        self.server_socket.listen(5)

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)

    def close(self):
        print('closing socket server')
        self.sel.unregister(self.server_socket)
        self.server_socket.close()
        self.server_socket = None
        self.client_socket = None

    def check_clients(self):
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

    def socket_send(self, data, format='>f'):  # format='>dddd'):
        if self.debug is True:
            print('socket sending ...')
        encoded_data = struct.pack(format, *data)
        if self.debug is True:
            print(' data: ', data,)  # '; encoded data :', encoded_data)
        bytes_sent = self.client_socket.send(encoded_data)
        if self.debug is True:
            print('  bytes sent: ', bytes_sent)


def main():
    socket_nb = SocketServerNB(debug=True)  # {'ipaddr': '192.168.0.6'})
    socket_nb.start(timeout=1)

    queue1 = deque((), 2000)
    i = 0
    while True:
        data = [
            i,
            random() * 50 + 150,
            random() * 20 + 80,
            random() * 15 + 60,
        ]
        i += 1
        print('data: ', data)
        queue1.append(data)

        if socket_nb.client_socket is None:
            socket_nb.check_clients()
        if socket_nb.client_socket is not None:
            while len(queue1) > 1:
                try:
                    # TODO: some queue elements gets lost when sending fails not more than 9
                    # probably when cs is closed and buffer is not empty
                    socket_nb.socket_send(queue1.popleft(), format='>ffff')
                except AttributeError:
                    print('client not connected')
                except OSError:
                    # TODO_: client socket close should be enough, while server is still listening - needs testing
                    socket_nb.client_close()
                    # socket_nb.close()
                    # socket_nb.start()

        time.sleep(1)