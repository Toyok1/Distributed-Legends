import threading
import os
from requests import get
from cryptography.fernet import Fernet
import time
import random

import grpc
import chat_pb2 as chat
import chat_pb2_grpc as rpc

port = 11912 # decide if we have to change this port
key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='

class PostOffice:

    def __init__(self, address: str):
        self.ip = get('https://api.ipify.org').content.decode('utf8')
        self.fernet = Fernet(key)
        self.encIp = self.fernet.encrypt(self.ip.encode())
        
        channel = grpc.insecure_channel(address + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)

    def Listen_for_PingPong(self):
        while True:
            ping = chat.Ping()  # create protobug message (called Ping)
            ping.ip = self.encIp
            pong = self.conn.SendPing(ping)
            time.sleep(5)
            if pong.message != "Thanks, friend!":
                raise Exception("Disconnect to the server!")

    def Subscribe(self, user):
        self.privateInfo = chat.PrivateInfo()  # create protobug message (called Note)
        self.privateInfo.ip = self.encIp
        self.privateInfo.user = user
        self.conn.SendPrivateInfo(self.privateInfo)  # send the Note to the server


    def StartGame(self):
        return self.conn.StartGame(self.privateInfo)

    def HealthStream(self):
        return self.conn.HealthStream(chat.Empty())

    def BlockStream(self):
        return self.conn.BlockStream(chat.Empty())

    def ActionStream(self):
        return self.conn.ActionStream(chat.Empty())

    def TurnStream(self):
        return self.conn.TurnStream(chat.Empty())

    def EndTurn(self):
        self.conn.EndTurn(self.privateInfo)

    def SendAction(self, user: str, actionType: int):
        n = chat.Action()
        n.ip_sender = self.encIp
        n.ip_reciever = self.fernet.encrypt(user.encode())
        
        match actionType:
            case 0: # attack
                n.action_type = 0
                n.amount = -10 + random.randint(-5,5) #TODO range of damage
            case 1 : # heal
                n.action_type = 1
                n.amount = 8 + random.randint(-5,5) #TODO range of damage
            case 2: # block
                n.action_type = 2
                n.amount = 10 #TODO range of damage
            case _: # TODO check how do you wont insert like default
                pass
        
        self.conn.SendAction(n)

    def SendBlock(self, actionType: int, victimUser: str = '', victimIp: str = '', action_amount: int = None):
        b = chat.Block()
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
        
        self.conn.SendBlock(b)

    def SendHealth(self, victimUser: str = '', victimIp: str = '', victimHp: int = None, action_amount: int = None):
        m = chat.Health()
        m.ip =  self.fernet.encrypt(victimIp.encode())
        m.hp = int(victimHp) + action_amount
        m.user = victimUser
        self.conn.SendHealth(m)
