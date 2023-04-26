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

from GRPCClientHelper.config import port, key, sentinel_list


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

    def __create_ping(self, sl_time, my_id):
        ping = chat.Ping()  # create protobug message (called Ping)
        ping.ip = self.encIp
        ping.id = my_id
        pong = self.conn.SendPing(ping)
        time.sleep(sl_time)
        # print(pong.list_players, "server response")
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
        global sentinel_list
        while True:
            pong = self.__create_ping(2.5, my_id)
            self.__set_user_list()
            sentinel_list = True
            # print(self.players)
            '''self.myPostOffice.ManualUpdateList(
                self.myPostOffice.myPlayer.getUid())'''
            if pong.message != "Thanks, friend!":
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

    def HealingStream(self):
        return self.conn.HealingStream(chat.Empty())

    def AttackStream(self):
        return self.conn.AttackStream(chat.Empty())

    def BlockStream(self):
        return self.conn.BlockStream(chat.Empty())

    def ActionStream(self):
        return self.conn.ActionStream(chat.Empty())

    def TurnStream(self):
        return self.conn.TurnStream(chat.Empty())

    def EndTurn(self, last_turn: player.Player):
        mess_et = chat.PlayerMessage()
        print(last_turn, "last_turn")
        mess_et.json_str = player.transformIntoJSON(last_turn)
        self.conn.EndTurn(mess_et)

    def SendAction(self, send: str, recieve: str, actionType: int):
        n = chat.Action()
        n.sender = player.transformIntoJSON(send)
        n.reciever = player.transformIntoJSON(recieve)

        match actionType:
            case 0:  # attack
                n.action_type = 0
                n.amount = 10 + random.randint(-5, 5)  # TODO range of damage
            case 1:  # heal
                n.action_type = 1
                n.amount = 8 + random.randint(-5, 5)  # TODO range of damage
            case 2:  # block
                n.action_type = 2
                n.amount = 10  # TODO range of damage
            case _:  # TODO check how do you wont insert like default
                pass

        self.conn.SendAction(n)

    def SendBlock(self, user: player.Player, amount: int):
        '''b = chat.Block()
        b.ip =  self.fernet.encrypt(victimIp.encode())

        match actionType:
            case 0 :
                b.block = 0
                b.user = victimUser
            case 1:
                b.block = action_amount
                b.user = self.privateInfo.user
            case _:
                pass

        self.conn.SendBlock(b)'''
        b = chat.Block()
        b.json_str = player.transformIntoJSON(user)
        b.block = amount
        self.conn.SendBlock(b)

    def SendHealing(self, user: player.Player, amount: int = None):
        m = chat.Healing()
        m.json_str = player.transformIntoJSON(user)
        m.hp = amount
        self.conn.SendHealing(m)

    def SendAttack(self, user: player.Player, amount: int = None):
        m = chat.Attack()
        m.json_str = player.transformIntoJSON(user)
        m.attack = amount
        self.conn.SendAttack(m)

    def SendFinishGame(self):
        self.conn.FinishGame(chat.Empty())

    def FinishStream(self):
        return self.conn.FinishStream(chat.Empty())
