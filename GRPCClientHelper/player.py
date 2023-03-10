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

    #ip, u_id, username, user_type, hp, block, ping_time

    def __init__(self, ip: str, unique_id: str, username: str, ping_time: float):
        self.ip = ip #decoded ip
        self.u_id = unique_id #uniqe id (to be used when testing locally and just because it's cool)
        self.username = username
        self.user_type = None # 1 = monster, 2 = knight, 3 = priest, 4 = mage TODO: make them match
        self.hp = 1
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
        return self.hp
    
    def setBlock(self, block):
        self.block = block
    
    def getBlock(self):
        return self.block
    
    def setPingTime(self, ping_time: float):
        self.ping_time = ping_time
    
    def getPingTime(self):
        return self.ping_time
    
    def __repr__(self):
        #ip, u_id, username, user_type, hp, block, ping_time
        return f"Player ip : {self.ip} u_id : {self.u_id} username : {self.username} user_type : {self.user_type} hp : {self.hp} block : {self.block}"

    def __str__(self):
        #ip, u_id, username, user_type, hp, block, ping_time
        return f"Player ip : {self.ip} u_id : {self.u_id} username : {self.username} user_type : {self.user_type} hp : {self.hp} block : {self.block}"
    



def transformIntoJSON(theplayertotransform: Player): #ip input decoded
    '''print(type(theplayertotransform), "THIS IS PL")
    print(theplayertotransform, "AND THIS IS ITS VALUE")'''
    obj = {
            "ip": theplayertotransform.getIp(),
            "u_id": theplayertotransform.getUid(),
            "username": theplayertotransform.getUsername(),
            "user_type": theplayertotransform.getUsertype(),
            "hp": theplayertotransform.getHp(),
            "block": theplayertotransform.getBlock(),
            "ping_time" : theplayertotransform.getPingTime()
        }
    return json.dumps(obj)

def transformFromJSON(json_str): #ip output decoded
    ret = None
    if json_str != "":
        obj = json.loads(json_str)
        ret = Player(obj["ip"], obj["u_id"], obj["username"], obj["ping_time"])
        ret.setUsertype(obj["user_type"])
        ret.setHp(obj["hp"])
        ret.setBlock(obj["block"])
    return ret

def tranformFullListIntoJSON(array):
    final_str = ""
    for i in array:
        #print("PLEASE PRINT", i)
        final_str += transformIntoJSON(i) + "#"
    final_str = final_str[:-1]
    #print(final_str, "final_str")
    return final_str

def transformFullListFromJSON(string_json):
    array = string_json.split("#")
    ret_array = []
    for i in array:
        ret_array.append(transformFromJSON(i))
    #print(ret_array, "ret_array")
    return ret_array