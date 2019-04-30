# microcontroller side of the app

import comm
import random
import ustruct as struct
import utime as time
import gc
from ucollections import deque


network_conn = comm.NetworkConn('conf.json')
socket = comm.SocketServer(network_conn.conf)
socket_nb = comm.SocketServerNB(network_conn.conf)


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


def test_nb_socket():
    """
    test function for non blocking server socket
    automatically reconnects after client disconnect
    :return:
    """
    network_conn.connect2()
    socket_nb.start()
    i = 0
    queue1 = deque((), 2000)
    while True:
        data = [
            i,
            random.random() * 20 + 180,
            random.random() * 15 + 30,
            random.random() * 50 + 100,
        ]
        i += 0.5

        queue1.append(data)
        print('queue length: ', len(queue1))

        if socket_nb.client_socket is None:
            socket_nb.check_clients()
        if socket_nb.client_socket is not None:
            while len(queue1) > 1:
                try:
                    # TODO: some queue elements gets lost when sending fails not more than 9
                    # probably when cs is closed an buffer is not empty
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


if __name__ == '__main__':
    test_nb_socket()