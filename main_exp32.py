# microcontroller side of the app

import comm
import random
import ustruct as struct
import utime as time


network_conn = comm.NetworkConn('conf.json')
socket = comm.SocketServer(network_conn)


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

