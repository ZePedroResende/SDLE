import socket
import threading
import json
import datetime
from threading import Timer
from requests import get


class peer:
    def __init__(self, port):
        self.host = self._get_host()
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def _get_host(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def bind(self):
        server_address = (self.host, self.port)
        self.socket.bind(server_address)

    def connect(self):
        server_address = (self.host, self.port)
        self.socket.connect(server_address)

    def listen(self, timeline, server, nickname, vector_clock):
        self.socket.listen(1)

        while self.running:
            print('waiting for a connection')
            connection, client_address = self.socket.accept()
            manager = threading.Thread(
                target=process_request,
                args=(connection, client_address,
                      timeline, server, nickname, vector_clock))
            manager.start()

    def stop(self):
        self.running = False
        socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM).connect((self.host, self.port))
        self.socket.close()

    # send a message to the other peer
    def send(self, msg, timeline=None):
        try:
            self.socket.sendall(msg.encode('utf-8'))

            data = self.socket.recv(256)
            print('received "%s"' % data.decode('utf-8'))
            if not data.decode('utf-8') == 'ACK':
                info = json.loads(data)
                if info['type'] == 'timeline':
                    record_messages(data, timeline)
        finally:
            print('closing socket')
            self.socket.close()


def process_request(conn, client_add, timeline, server, nick, vector_clock):
    try:
        print('conn from', client_add)
        while True:
            data = conn.recv(1024)
            if data:
                print('received "%s"' % data.decode('utf-8'))
                result = process_message(data, timeline,
                                         server, nick, vector_clock)
                conn.sendall(result)
            else:
                break
    finally:
        conn.close()

def exitfunc(timeline, msg):
    timeline.remove(msg)

def process_message(data, timeline, server, nickname, vector_clock):
    info = json.loads(data)
    if info['type'] == 'simple':
        js = {'id': info['id'], 'message': info['msg'], 'datetime': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
        timeline.append(js)
        Timer(10, exitfunc, [timeline, js]).start()
        update_vector_clock(server, 1, info['id'], vector_clock)
        return 'ACK'.encode('utf-8')
    elif info['type'] == 'timeline':
        list = get_messages(info['id'], timeline, int(info['n']))
        di = {'type': 'timeline', 'list': json.dumps(list)}
        update_vector_clock(server, len(list), info['id'], vector_clock)
        res = json.dumps(di)
        return res.encode('utf-8')


def update_vector_clock(server, n, id, vector_clock):
    try:
        vector_clock[id] += n
    except Exception:
        vector_clock[id] = n


def get_messages(id, timeline, n):
    list = []
    for m in timeline:
        if m['id'] == id:
            list.append(m)
    print(list)
    print(list[-n:])
    return list[-n:]


def record_messages(data, timeline):
    info = json.loads(data)
    list = json.loads(info['list'])
    for m in list:
        timeline.append({'id': m['id'], 'message': m['message']})
