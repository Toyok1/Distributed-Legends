import grpc
import time
import threading
from concurrent import futures
from GRPCClientHelper import player
import os

import chat_pb2 as chat
import chat_pb2_grpc as rpc

import signal

from cryptography.fernet import Fernet
from requests import get
from GRPCClientHelper.config import port, key


class PeerChatServer(rpc.ChatServerServicer):
    def __init__(self, pId, address, Uid):
        server = grpc.server(futures.ThreadPoolExecutor(
            max_workers=100))  # create a gRPC server
        rpc.add_ChatServerServicer_to_server(
            self, server)  # register the server to gRPC
        # gRPC basically manages all the threading and server responding logic, which is perfect!
        print('Starting server. Listening...')
        server.add_insecure_port('[::]:' + str(1000))
        server.start()
        self.finish = []
        self.peers_connections = []
        self.myUid = Uid
        self.peers_actions = []
        # List with all the chat history
        self.actions = []
        self.hp = []
        self.attack = []
        self.listBlock = []
        self.turns = []
        # player.transformFullListFromJSON(str_list_user)
        self.listUser = []
        self.fernet = Fernet(key)
        self.processId = pId
        self.LAST_USER_TURN = None
        self.isStartedGame = False
        self.TERMINATE = None
        print("connecting to lobby")
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)

        for started in self.conn.StartedStream(chat.Empty()):
            if started.name == "game started":
                self.listUser = player.transformFullListFromJSON(
                    started.message)
                break
        print("out the for loop")
        channel.close()

        req_ip = [u.getIp() for u in self.listUser if u.getId() != self.myUid]
        req_id = [u.getId() for u in self.listUser if u.getId() != self.myUid]
        # time.sleep(20)
        self.__connect_to_peers(req_ip, req_id)

        # threading.Thread(target=self.__clean_user_list, daemon=True).start()
        '''
        threading.Thread(target=self.__keep_alive, daemon=True).start()
        '''

    def Subscribe(self):
        self.conn.SendPrivateInfo(self.privateInfo)

    def __connect_to_peers(self, req_ip: list, req_id: list):
        print("connecting to peers")
        # time.sleep(2)
        for i in range(len(req_ip)):
            if req_ip[i] != get('https://api.ipify.org').text:
                # print("connecting to peer", req_ip[i])
                channel = grpc.insecure_channel(req_ip[i]+":"+str(1000))
                stub = rpc.ChatServerStub(channel)
                self.peers_connections.append(stub)
                # print("connected to peer", req_ip[i])
                self.__updateUserList(req_ip[i], req_id[i])
                # TODO start pinging the peers

        # print("connected to all peers")
        for i in range(len(self.peers_connections)):
            threading.Thread(target=self.__listen_for_action_stream, args=(
                self.peers[i],), daemon=True).start()
        print(self.peers_connections)

    def __listen_for_action_stream(self, peer):
        print("listening for action stream")
        for action in peer.ActionStream(chat.Empty()):
            print("action received from peer", action)
            n = action
            pl = player.transformFromJSON(n.reciever)
            am = n.amount
            action_type = n.action_type
            for p in self.listUser:
                if p.getUid() == pl.getUid():
                    if action_type == 0:
                        p.takeDamage(am)
                    elif action_type == 1:
                        p.heal(am)
                    elif action_type == 2:
                        p.block(am)
                    else:
                        print("OPS! Error with the actions.")
            self.peers_actions.append(action)

    def __updateUserList(self, req_ip, req_id):
        for usr in self.listUser:
            if usr.getIp() == req_ip and usr.getUid() == req_id:
                # #print("pinged", usr)
                usr.setPingTime(time.time())
    '''
    def __keep_alive(self):
        while True:
            time.sleep(180)  # TODO change number of seconds of inactivity
            if len(self.listUser) == 0:
                os.kill(self.processId, signal.SIGTERM)
    '''
    # TO ADAPT TO p2p architecture

    def __clean_user_list(self):
        # if a user (hero) is more than 10 seconds from its last ping we count it as dead and, if it is its turn we skip it and we go to the next user.
        while True:
            if self.isStartedGame:
                # print("Player List", self.listUser)
                for user in self.listUser:
                    if float(time.time()) - float(user.getPingTime()) > 10.0:
                        # print("lost ping with ", user)
                        # if it's the turn user, pick another
                        if user.getUid() == self.LAST_USER_TURN.getUid():  # disconnected while it's my turn
                            # add a turn message for the next guy
                            # print("IT WAS MY TURN")
                            for i in range(0, len(self.listUser)):
                                if self.LAST_USER_TURN.getUid() == self.listUser[i].getUid():
                                    userNext = self.listUser[(
                                        i+1) % len(self.listUser)]
                                    n = chat.PlayerMessage()
                                    n.json_str = player.transformIntoJSON(
                                        userNext)
                                    # TODO get this to work
                                    self.turns.append(n)
                        self.listUser.remove(user)
                if len(self.listUser) == 1:
                    # print("length userList == 1")
                    n = chat.EndNote()
                    # only two messages that should ever be displayed
                    n.MonsterWin = "YOU CAN RULE THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                    # only two messages that should ever be displayed
                    n.HeroesWin = "YOU SAVED THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                    n.MonsterDefeat = "How did you get here?"
                    n.HeroesDefeat = "Looking for easter eggs?"
                    n.fin = True if self.listUser[0].getUsertype(
                    ) == 1 else False
                    self.finish.append(n)
                    self.isStartedGame = False
                    self.TERMINATE = True
                    break

                    # list of all types of users. If there is no monter the heroes win by default.
                if not 1 in [int(u.getUsertype()) for u in self.listUser]:
                    # print("NO MONSTERS")
                    n = chat.EndNote()
                    n.MonsterWin = "Noone expects the spanish inquisition!"
                    # the only message to ever be displayed
                    n.HeroesWin = "YOU SAVED THE WORLD BECAUSE THE MONSTER DISCONNECTED"
                    n.MonsterDefeat = "How did you get here?"
                    n.HeroesDefeat = "Looking for easter eggs?"
                    n.fin = False
                    self.finish.append(n)
                    self.isStartedGame = False
                    self.TERMINATE = True
                    break

            time.sleep(2.5)

    '''
    def __distributeHealth(self):
        for user in self.listUser:
            if user.getUsertype() == 1:
                user.setHp(100)
            else:
                user.setHp(50)
    '''

    def SendAction(self, send: player.Player, recieve: player.Player, actionType: int):
        n = chat.Action()
        n.sender = ""
        n.reciever = ""

        for p in self.listUser:
            if p.getUid() == send.getUid():
                n.sender = player.transformIntoJSON(p)
                usr = p
            if p.getUid() == recieve.getUid():
                n.reciever = player.transformIntoJSON(p)

        if usr.getUsertype() == 0:
            # knight
            values = {"attack": 8, "heal": 8, "block": 10}
        elif usr.getUsertype() == 1:
            # monster - does more damage, heals more and blocks more based on how many enemies he has. 1vs1 he is slightly better at most things but worse at one thing
            values = {"attack": 9 + 2 * (len(self.listUser)-2), "heal": 9 + 2 * (
                len(self.listUser)-2), "block": 9 + 2 * (len(self.listUser)-2)}
        elif usr.getUsertype() == 2:
            # priest
            values = {"attack": 8, "heal": 10, "block": 8}
        elif usr.getUsertype() == 3:
            # mage
            values = {"attack": 10, "heal": 8, "block": 8}
        else:
            # default
            values = {"attack": 0, "heal": 0, "block": 0}

        if actionType == 0:
            n.action_type = 0
            n.amount = values["attack"] + \
                3  # TODO range of damage
        elif actionType == 1:
            n.action_type = 1
            n.amount = values["heal"] + \
                3  # TODO range of damage
        elif actionType == 2:
            n.action_type = 2
            n.amount = values["block"]  # TODO range of damage
        else:
            n.action_type = 2
            n.amount = 0

        self.actions.append(n)
        self.peers_actions.append(n)
        print("action added ", n)
        return chat.Empty()

    def ActionStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.actions) > lastindex:
                n = self.actions[lastindex]
                lastindex += 1
                self.turn_actions.append(n)
                # #print("Yielding action = ", n)
                yield n

    def SendPing(self, request: chat.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(
            request.ip).decode(), request.id)
        return chat.Pong(message="Thanks, friend!" if self.TERMINATE != True else "SET_FINISHED", list_players=player.tranformFullListIntoJSON(self.listUser))

    def EndTurn(self, request: chat.PlayerMessage, context):
        # #print("end turn")
        userLast = player.transformFromJSON(request.json_str)

        for i in range(0, len(self.listUser)):
            # if self.listUser[i]["ip"] == ipLast:
            if userLast.getUid() == self.listUser[i].getUid():
                userNext = self.listUser[(i+1) % len(self.listUser)]
        # create the return message, encrypt the ip and send it in broadcast to everyone.
        for p in self.listUser:
            if p.getUid() == userNext.getUid():
                self.LAST_USER_TURN = p
        # print("prossimo turno: ", userNext.getUsername())
        r = chat.PlayerMessage()
        r.json_str = player.transformIntoJSON(userNext)
        self.turns.append(r)

        return chat.Empty()

    def TurnStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.turns) > lastindex:
                n = self.turns[lastindex]
                # #print(n)
                lastindex += 1
                yield n

    def FinishGame(self, request_iterator, context):
        # #print("FinishGame called")
        self.isStartedGame = False
        n = chat.EndNote()
        n.MonsterWin = "YOU CAN RULE THE WORLD"
        n.HeroesWin = "YOU SAVED THE WORLD"
        n.MonsterDefeat = "THE HEROES PREVENTED YOU FROM TAKING OVER THE WORLD"
        n.HeroesDefeat = "YOU FAILED TO SAVE THE WORLD"
        n.fin = request_iterator.fin
        self.finish.append(n)
        return chat.Empty()

    def FinishStream(self, request_iterator, context):
        # #print("FinishStream called")

        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.finish) > lastindex:
                n = self.finish[lastindex]
                # #print(n)
                lastindex += 1
                yield n


if __name__ == '__main__':
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1000))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(PeerChatServer(
        os.getpid()), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    # print("Connect here: ", get('https://api.ipify.org').content.decode('utf8'))
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
