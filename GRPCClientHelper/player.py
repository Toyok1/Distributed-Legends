'''import threading
import os
import time
import random'''
import json
from cryptography.fernet import Fernet

from GRPCClientHelper import helper

key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='
fernet = Fernet(key)


class Player:

    # ip, u_id, username, user_type, hp, block, ping_time

    def __init__(self, ip: str, unique_id: str, username: str, user_type: int, ping_time: float):
        self.ip = ip  # decoded ip
        # uniqe id (to be used when testing locally and just because it's cool)
        self.u_id = unique_id
        self.username = username
        # 1 = monster, 2 = knight, 3 = priest, 4 = mage TODO: make them match
        self.user_type = user_type
        self.hp = 100 if user_type == 1 else 50
        self.block = 0
        self.ping_time = ping_time

    def setIp(self, ip):
        self.ip = ip

    def getIp(self):
        return self.ip

    def setUid(self, u_id):
        self.u_id = u_id

    def getUid(self):
        return self.u_id

    def setIp(self, username):
        self.username = username

    def getUsername(self):
        return self.username

    def setUsertype(self, user_type):
        self.user_type = user_type

    def getUsertype(self):
        return self.user_type

    def setHp(self, hp):
        self.hp = hp

    def getHp(self):
        return int(self.hp)

    def setBlock(self, block):
        self.block = block

    def getBlock(self):
        return int(self.block)

    def setPingTime(self, ping_time: float):
        self.ping_time = ping_time

    def getPingTime(self):
        return self.ping_time

    def takeDamage(self, amount):  # all >0
        # se ho blocco, devo togliere prima quello, altrimenti prendo danni alla salute.
        print(amount, "AMOUNT")
        print(self.getHp() - amount, "POSSIBLE NEW AMOUNT")
        if self.getBlock() > 0:
            # 20 hp, 10 block , attack 15     ==  15 - 10 > 0
            amount = amount - int(self.getBlock())
            self.setBlock(0 if amount > 0 else abs(amount))
            if amount > 0:
                self.setHp(0 if self.getHp() - amount <
                           0 else self.getHp() - amount)
        else:
            self.setHp(0 if self.getHp() - amount <
                       0 else self.getHp() - amount)

    def heal(self, amount):
        n_h = int(self.getHp()) + int(amount)
        if self.getUsertype() == 1:
            # monster
            if n_h > 100:
                self.setHp(100)
            else:
                self.setHp(n_h)
        else:
            if n_h > 50:
                self.setHp(50)
            else:
                self.setHp(n_h)
            # hero

    def block(self, amount):
        new_b = self.getBlock() + amount
        self.setBlock(new_b)

    def __repr__(self):
        # ip, u_id, username, user_type, hp, block, ping_time
        # return f"Player ip : {self.ip} u_id : {self.u_id} username : {self.username} user_type : {self.user_type} hp : {self.hp} block : {self.block}"
        return f"Player hp : {self.hp} username : {self.username}"

    def __str__(self):
        # ip, u_id, username, user_type, hp, block, ping_time
        # return f"Player ip : {self.ip} u_id : {self.u_id} username : {self.username} user_type : {self.user_type} hp : {self.hp} block : {self.block}"
        return f"Player hp : {self.hp} username : {self.username}"


def transformIntoJSON(theplayertotransform: Player):  # ip input decoded
    obj = {
        "ip": theplayertotransform.getIp(),
        "u_id": theplayertotransform.getUid(),
        "username": theplayertotransform.getUsername(),
        "user_type": theplayertotransform.getUsertype(),
        "hp": theplayertotransform.getHp(),
        "block": theplayertotransform.getBlock(),
        "ping_time": theplayertotransform.getPingTime()
    }
    return json.dumps(obj)


def transformFromJSON(json_str):  # ip output decoded
    ret = None
    if json_str != "":
        obj = json.loads(json_str)
        ret = Player(obj["ip"], obj["u_id"], obj["username"],
                     obj["user_type"], obj["ping_time"])
        ret.setHp(obj["hp"])
        ret.setBlock(obj["block"])
    return ret


def tranformFullListIntoJSON(array):
    final_str = ""
    for i in array:
        # print("PLEASE PRINT", i)
        final_str += transformIntoJSON(i) + "#"
    final_str = final_str[:-1]
    # print(final_str, "final_str")
    return final_str


def transformFullListFromJSON(string_json):
    array = string_json.split("#")
    ret_array = []
    for i in array:
        ret_array.append(transformFromJSON(i))
    # print(ret_array, "ret_array")
    return ret_array
