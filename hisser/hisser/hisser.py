# -*- coding: utf-8 -*-
import logging
import asyncio
import sys
import socket
import random
import builder
import json
import datetime
from threading import Timer
from Msg import Msg
from peer import peer
from threading import Thread
import local_storage
import asyncs
from kademlia.network import Server
from Menu.Menu import Menu
import Menu.Menu as menu
from Menu.Item import Item

DEBUG = False
# -- Global VARS --
queue = asyncio.Queue()
p2p_port = ""
nickname = ""
ip_address = ""
timeline = []
following = []
vector_clock = {}
db_file = 'db'


# handler process IO request
def handle_stdin():
    data = sys.stdin.readline()
    asyncio.ensure_future(queue.put(data)) # Queue.put is a coroutine, so you can't call it directly.


# build the Menu
def build_menu():
    menu = Menu('Menu')
    menu.add_item(Item('1 - Show timeline', show_timeline))
    menu.add_item(Item('2 - Follow username', follow_user))
    menu.add_item(Item('3 - Send message', send_msg))
    menu.add_item(Item('0 - Exit', exit_loop))
    return menu


# get the nickname
def get_nickname():
    nick = input('Nickname: ')
    return nick.replace('\n', '')


# follow a user. After, he can be found in the list "following"
def follow_user():
    user = input('User Nickname: ')
    user_id = user.replace('\n', '')
    asyncio.ensure_future(asyncs.task_follow(user_id, nickname, server, following, ip_address, p2p_port, vector_clock))
    return False


# show own timeline
def show_timeline():
    menu.clear()
    print('_______________ Timeline _______________')
    for m in timeline:
        print(m['id'] + ' - ' + m['message'])
    print('________________________________________')
    input('Press Enter')
    menu.clear()
    return False


def exitfunc(msg):
    timeline.remove(msg)
    
# send message to the followers
def send_msg():
    msg = input('Insert message: ')
    msg = msg.replace('\n','')
    json = {'id': nickname, 'message': msg, 'datetime': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
    timeline.append(json)
    Timer(10, exitfunc, [json]).start()
    print(msg)
    result = builder.simple_msg(msg, nickname)
    asyncio.ensure_future(asyncs.task_send_msg(result, server, nickname, vector_clock))

    return False


# exit app
def exit_loop():
    return True

def start_node(port, BTIp="", BTPort=0):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s\
                                  - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # DEBUG
    if DEBUG:
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    if DEBUG:
        loop.set_debug(True)

    server = Server()
    loop.run_until_complete(server.listen(port))

    # the first peer don't do that
    if BTPort != 0:
        bootstrap_node = (BTIp, int(BTPort))
        loop.run_until_complete(server.bootstrap([bootstrap_node]))

    return (server, loop)

# start peer or not as Bootstrap
def start():
    if len(sys.argv) > 3:
        return start_node(int(sys.argv[1]), sys.argv[3], int(sys.argv[4]))
    else:
        return start_node(int(sys.argv[1]))


# check if the number of args is valid
def check_argv():
    if len(sys.argv) < 3:
        print("Usage: python get.py <port_dht> <port_p2p> [<bootstrap ip> <bootstrap port>]")
        sys.exit(1)


# get timeline to the followings TODO
async def get_timeline():
    for user in following:
        result = await server.get(user['id'])
        result2 = await server.get(nickname)
        if result is not None and result2 is not None:
            userInfo = json.loads(result)
            ownInfo = json.loads(result2)
            random_follower, n = await get_random_updated_follower(user, userInfo, ownInfo)
            if random_follower is not None:
                ask_for_timeline(random_follower[0], random_follower[1], user['id'], n)



# temos de implementar o XOR
async def get_random_updated_follower(user, userInfo, ownInfo):
    print("RANDOM FOLLOWER")
    id = user['id']
    user_followers = userInfo['followers']
    while(user_followers):
        random_follower = random.choice(list(user_followers.keys()))
        random_follower_con = userInfo['followers'][random_follower]
        info = random_follower_con.split()
        print(userInfo['vector_clock'])
        print(vector_clock)
        if userInfo['vector_clock'][id] > vector_clock[id] and random_follower != nickname and asyncs.isOnline(info[0], int(info[1])):
        #if random_follower != nickname and asyncs.isOnline(info[0], int(info[1])):
            print("FOUND")
            return info, int(userInfo['vector_clock'][id]) - vector_clock[id]
        user_followers.pop(random_follower)
    print("FAILED")
    if userInfo['vector_clock'][id] > vector_clock[id]:
        return [user['ip'], user['port']], int(userInfo['vector_clock'][id]) - vector_clock[id]
    else:
        return None, 0

# send a message to a node asking for a specific timeline
def ask_for_timeline(userIp, userPort, TLUser, n):
    msg = builder.timeline_msg(TLUser, vector_clock, n)
    asyncs.send_p2p_msg(userIp, int(userPort), msg, timeline)
    print('ASKING FOR TIMELINE')


# merge all timelines TODO
def merge_timelines():
    print('TODO')


# check a set of vector clocks TODO
def check_vector_clocks():
    print('TODO')


# build a json with user info and put it in the DHT
async def build_user_info():
    exists = await server.get(nickname)                                 #check if user exists in DHT
    if exists is None:
        info = builder.user_info(nickname, ip_address, p2p_port)
        vector_clock[nickname] = 0
        asyncio.ensure_future(server.set(nickname, info))


# Get user real ip
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip



def start_node(port, BTIp="", BTPort=0):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s\
                                  - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # DEBUG
    if DEBUG:
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    if DEBUG:
        loop.set_debug(True)

    server = Server()
    loop.run_until_complete(server.listen(port))

    # the first peer don't do that
    if BTPort != 0:
        bootstrap_node = (BTIp, int(BTPort))
        loop.run_until_complete(server.bootstrap([bootstrap_node]))

    return (server, loop)



def _exec_p2p(connection,server):
    connection.bind()
    connection.listen(timeline, server, nickname, vector_clock)

def start_p2p(nickname, port, server, loop):
    global p2p_port
    p2p_port = port
    connection = peer(port)
    (timeline, following, vector_clock) = local_storage.read_data(db_file+nickname)
    thread = Thread(target=_exec_p2p, args=(connection, server,))
    thread.start()
    return connection

def _start(args):
    global nickname
    if len(args) == 6:
        (server,loop) = start_node(int(args[1]), args[3], int(args[4]))
        nickname = args[5]
    elif len(args) == 4:
        (server,loop) = start_node(int(args[1]))
        nickname = args[3]
    else:
        print("Usage: python hisser.py <port_dht> <port_p2p>\
              [<bootstrap ip> <bootstrap port>] nickname")
        sys.exit(1)
    return (server,loop)

if __name__ == "__main__":
    (server,loop) = _start(sys.argv)
    try :
        (timeline, following, vector_clock) = local_storage.read_data(db_file+nickname)     # TODO rm nickname (it's necessary for to allow tests in the same host 
        msg_to_remove = []

        if timeline:
            for m in timeline:
                d = datetime.datetime.strptime(m['datetime'], '%m/%d/%Y, %H:%M:%S')
                sec = (datetime.datetime.now() - d).total_seconds()
                if sec < 10:
                    Timer(int(10 - sec), exitfunc, [m]).start()
                else:
                    msg_to_remove.append(m)
        
        if msg_to_remove:
            for m in msg_to_remove:
                timeline.remove(m)
        
        connection = start_p2p(nickname,int(sys.argv[2]),server, loop)
        ip_address = connection.host
        loop.add_reader(sys.stdin, handle_stdin)
        asyncio.ensure_future(build_user_info())
        asyncio.ensure_future(get_timeline())

        m = build_menu()
        asyncio.ensure_future(asyncs.task(server, loop, nickname, m, queue))
        loop.run_forever()

    except Exception as e:
        print(e)
    finally:
        print('Good Bye!')
        local_storage.save_data(timeline, following, vector_clock, db_file+nickname)        # TODO rm nickname
        connection.stop()                                                                   # stop thread in "listen mode"
        server.stop()                                                                       # Stop the server with DHT Kademlia
        loop.close()                                                                        # Stop the async loop
        sys.exit(1)
