import grpc
import socket
import threading
import os
from functools import partial
import time
import random
from GRPCClientHelper import player
from GRPCClientHelper.config import portAuth, portGame, key

from requests import get
from cryptography.fernet import Fernet

import clientController_pb2 as clientController
import clientController_pb2_grpc as clientController_rpc

import lobby_auth_pb2 as lobby_auth
import lobby_auth_pb2_grpc as lobby_auth_rpc

class PostOffice:

    def __init__(self, address: str, user, u_id, id_lobby, user_type):
        self.ip = self._get_local_ip() #get('https://api.ipify.org').content.decode('utf8')
        self.fernet = Fernet(key)
        self.encIp = self.fernet.encrypt(self.ip.encode())
        self.actionList = []

        
        channel = grpc.insecure_channel(address + ':' + str(portAuth))
        self.conn_auth = lobby_auth_rpc.LobbyAuthServerStub(channel)
        
        #my local server for streaming action end turns
        local_channel = grpc.insecure_channel('localhost' + ':' + str(portGame))
        self.conn_my_local_service = clientController_rpc.ClientControllerStub(local_channel)
        
        self.conn_enemies = []        
        self.privateInfo = lobby_auth.PrivateInfo()
        self.privateInfo.ip = self.encIp
        self.privateInfo.user = user
        self.privateInfo.u_id = u_id
        self.privateInfo.user_type = user_type
        self.privateInfo.id_lobby = id_lobby
        
        self.players = []
        self.heroesList = []
        self.myPlayer = None
        self.old_players = []
        self.disconnected_players = []
        self.isFinished = False

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('192.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    def __create_ping(self, sl_time, my_id):
        ping = clientController.Ping()  # create protobug message (called Ping)
        ping.ip = self.encIp
        ping.id = my_id
        pong = self.conn_auth.SendPing(ping)
        time.sleep(sl_time)
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
        self.players = player.transformFullListFromJSON(self.conn_auth.SendPrivateInfo(self.privateInfo).list)

    def SendEndTurn(self):
        mess_et = clientController.PlayerMessage()
        # #print(last_turn, "last_turn")
        mess_et.json_str = player.transformIntoJSON(last_turn)
        self.conn_my_local_service.EndTurn(mess_et)
    
    def CheckStarted(self):
        return self.conn_auth.ReturnStarted(clientController.Empty())

    def StartGame(self):
        self.players = player.transformFullListFromJSON(self.conn_auth.GetPlayerList(self.privateInfo).list)
        print('NewList', self.players)
        self.__set_user_list()
        
        # avviare le connessioni con grpc ai giocatori presenti in players tramite il campo ip
        for p in [x for x in self.players if x.getUid() != self.myPlayer.getUid()]:
            channel = grpc.insecure_channel(p.getIp() + ':' + str(portGame))
            self.conn_enemies.append(clientController_rpc.ClientControllerStub(channel))
        
        # testing manual comunication write
        #self._send_tmp_attack()

        # testing manual comunication read
        for enemy in self.conn_enemies:
            callback = partial(self._listen_enemy_action_stream, enemy)
            threading.Thread(target= callback, daemon=True).start()
        
        #TODO: toglie il player dalla lobby del server dopo 60 secondi
        callback = partial(self.conn_auth.StartGame, self.privateInfo)
        threading.Timer(15, callback).start()
        return 

    #testing
    '''def _send_tmp_attack(self):
        n = clientController.Action()
        n.sender = 'pippo attacca'
        n.reciever = 'pluto prende'
        n.amount = 5
        n.action_type = 1
        self.conn_my_local_service.SendAction(n)
        print('azione scritta correttamente')'''
    #testing
    def _listen_enemy_action_stream(self, enemy):
        print('inizio a leggere gli attacchi')
        for action in enemy.ActionStream(clientController.Empty()):
            print('enemy', action)
            self.actionList.append(action)
        

    def ActionStream(self):
        return self.conn_my_local_service.ActionStream(clientController.Empty())

    def TurnStream(self):
        return self.conn_my_local_service.TurnStream(clientController.Empty())

    def SendAction(self, send: player.Player, recieve: player.Player, actionType: int):
        n = clientController.Action()
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
                random.randint(-5, 5) 
        elif actionType == 1:
            n.action_type = 1
            n.amount = values["heal"] + \
                random.randint(-5, 5) 
        elif actionType == 2:
            n.action_type = 2
            n.amount = values["block"] 
        else:
            n.action_type = 2
            n.amount = 0

        # #print(n)
        self.conn_my_local_service.SendAction(n)

    def SendFinishGame(self, f):
        n = clientController.FinishedBool()
        n.fin = f
        self.conn_my_local_service.FinishGame(n)

    def FinishStream(self):
        return self.conn_my_local_service.FinishStream(clientController.Empty())

    #TODO: connettersi agli altri player dopo lautenticazione
    '''
    def __connect_to_peers(self, req_ip: list, req_id: list):
        print("connecting to peers")
        # time.sleep(2)
        for i in range(len(req_ip)):
            if req_ip[i] != get('https://api.ipify.org').text:
                # print("connecting to peer", req_ip[i])
                channel = grpc.insecure_channel(req_ip[i]+":"+str(8080))
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
    '''