import threading
import os
from requests import get
from cryptography.fernet import Fernet
import time
import random

import grpc
import chat_pb2 as chat
import chat_pb2_grpc as rpc
from GRPCClientHelper import player

from GRPCClientHelper.config import port, key


class PostOffice:

    def __init__(self, address: str, user, u_id, user_type):
        self.ip = get('https://api.ipify.org').content.decode('utf8')
        self.fernet = Fernet(key)
        self.encIp = self.fernet.encrypt(self.ip.encode())

        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)
        self.privateInfo = chat.PrivateInfo()  # create protobug message (called Note)
        self.privateInfo.ip = self.encIp
        self.privateInfo.user = user
        self.privateInfo.u_id = u_id
        self.privateInfo.user_type = user_type
        self.players = []
        self.heroesList = []
        self.myPlayer = None
        self.old_players = []
        self.disconnected_players = []
        self.isFinished = False

    def __create_ping(self, sl_time, my_id):
        ping = chat.Ping()  # create protobug message (called Ping)
        ping.ip = self.encIp
        ping.id = my_id
        pong = self.conn.SendPing(ping)
        time.sleep(sl_time)
        # #print(pong.list_players, "server response")
        self.players = player.transformFullListFromJSON(pong.list_players)
        return pong

    def __set_user_list(self):
        for p in self.players:
            if p.getUid() == self.privateInfo.u_id:
                self.myPlayer = p
            self.disconnected_players.extend(list(set(
                self.old_players) - set(self.players)) if len(self.old_players) > len(self.players) else [])
            self.old_players = self.players
            self.heroesList = [u for u in self.players if u.getUsertype() != 1]

    def Listen_for_PingPong(self, my_id):
        while True:
            # low enough the labels become consistent TODO
            pong = self.__create_ping(1, my_id)
            self.__set_user_list()
            if pong.message == "Thanks, friend!":
                pass
            elif pong.message == "SET_FINISHED":
                self.isFinished = True
            else:
                raise Exception("Disconnect to the server!")

    def ManualUpdateList(self, my_id):
        self.__create_ping(0, my_id)
        self.__set_user_list()

    def Subscribe(self):
        # send the Note to the server
        self.conn.SendPrivateInfo(self.privateInfo)

    def CheckStarted(self):
        return self.conn.ReturnStarted(chat.Empty())

    def StartGame(self):
        return self.conn.StartGame(self.privateInfo)

    def ActionStream(self):
        return self.conn.ActionStream(chat.Empty())

    def TurnStream(self):
        return self.conn.TurnStream(chat.Empty())

    def EndTurn(self, last_turn: player.Player):
        mess_et = chat.PlayerMessage()
        # #print(last_turn, "last_turn")
        mess_et.json_str = player.transformIntoJSON(last_turn)
        self.conn.EndTurn(mess_et)

    def SendAction(self, send: player.Player, recieve: player.Player, actionType: int):
        n = chat.Action()
        n.sender = ""
        n.reciever = ""

        for p in self.players:
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
            values = {"attack": 9 + 2 * (len(self.players)-2), "heal": 9 + 2 * (
                len(self.players)-2), "block": 9 + 2 * (len(self.players)-2)}
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
                random.randint(-10, 10)  # TODO range of damage
        elif actionType == 1:
            n.action_type = 1
            n.amount = values["heal"] + \
                random.randint(-10, 10)  # TODO range of damage
        elif actionType == 2:
            n.action_type = 2
            n.amount = values["block"]  # TODO range of damage
        else:
            n.action_type = 2
            n.amount = 0

        # #print(n)
        self.conn.SendAction(n)

    def SendFinishGame(self, f):
        n = chat.FinishedBool()
        n.fin = f
        self.conn.FinishGame(n)

    def FinishStream(self):
        return self.conn.FinishStream(chat.Empty())
