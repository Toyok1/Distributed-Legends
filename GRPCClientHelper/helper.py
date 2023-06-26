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
        # get('https://api.ipify.org').content.decode('utf8')
        self.ip = get('https://api.ipify.org').content.decode('utf8')
        self.fernet = Fernet(key)
        self.encIp = self.fernet.encrypt(self.ip.encode())
        self.actionList = []
        self.turnList = []

        channel = grpc.insecure_channel(address + ':' + str(portAuth))
        self.conn_auth = lobby_auth_rpc.LobbyAuthServerStub(channel)

        # my local server for streaming action end turns
        local_channel = grpc.insecure_channel(
            'localhost' + ':' + str(portGame))

        self.conn_my_local_service = clientController_rpc.ClientControllerStub(
            local_channel)

        self.conn_enemies = []
        self.privateInfo = lobby_auth.PrivateInfo()
        self.privateInfo.ip = self.encIp
        self.privateInfo.user = user
        self.privateInfo.u_id = u_id
        self.privateInfo.user_type = user_type
        self.privateInfo.id_lobby = id_lobby

        self.players = []
        self.playersCheck = []
        self.heroesList = []
        self.myPlayer = None
        self.old_players = []
        self.disconnected_players = []
        self.isFinished = False

        m = clientController.PlayerMessage()
        m.json_str = str(u_id)
        self.conn_my_local_service.RecieveUid(m)

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

    def __listen_for_terminated(self):
        try:
            for disconnected in self.conn_my_local_service.TerminatedStream(clientController.Empty()):
                target = player.transformFromJSON(disconnected.json_str)
                for p in self.players:
                    if p.getUid() == target.getUid():
                        self.players.remove(p)

        except grpc._channel._Rendezvous as err:
            print(err)

    def __pinging_lobby(self):
        try:
            self.Listen_for_PingPong_Lobby(self.privateInfo.u_id)
        except Exception as e:
            x = e.args[0]
            print(x)  # TODO migliora gestione eccezioni

    def __create_ping(self, sl_time, my_id):
        ping = clientController.Ping()  # create protobug message (called Ping)
        ping.ip = self.encIp
        ping.id = my_id
        pong = self.conn_auth.SendPing(ping)
        time.sleep(sl_time)
        return pong

    def __create_ping_lobby(self, sl_time, my_id):
        ping = lobby_auth.Ping_Lobby()  # create protobug message (called Ping)
        ping.ip = self.encIp
        ping.u_id = my_id
        ping.lobby_id = self.privateInfo.id_lobby
        pong = self.conn_auth.SendPingLobby(ping)
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

    def __ping_peer(self, peer):
        uid_sender = None
        while True:
            try:
                ping = clientController.Ping()
                ping.ip = self.encIp
                ping.id = self.privateInfo.u_id
                pong = peer.SendPing(ping)
                uid_sender = pong.u_id_sender
                time.sleep(2.5)
            except:
                for p in self.players:
                    if p.getUid() == uid_sender:
                        self.disconnected_players.append(p)
                        self.players.remove(p)

    def Listen_for_PingPong_Lobby(self, my_id):
        while True:
            pong = self.__create_ping_lobby(1, my_id)
            self.__set_user_list()
            if pong.message == "Thanks, friend!":
                pass
            else:
                raise Exception("Disconnect from the lobby!")

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
                raise Exception("Disconnect from the game!")

    def ManualUpdateList(self, my_id):
        self.__create_ping(0, my_id)
        self.__set_user_list()

    def Subscribe(self):
        l = self.conn_auth.SendPrivateInfo(self.privateInfo)
        self.players = player.transformFullListFromJSON(l.list)
        self.playersCheck = self.players.copy()
        threading.Thread(target=self.__pinging_lobby, daemon=True).start()

    def SendEndTurn(self):
        mess_et = clientController.PlayerMessage()
        for i in range(len(self.players)):
            if self.players[i].getHp() < 1:
                self.playersCheck.remove(self.players[i])
        index = self.players.index(self.myPlayer)
        next = self.players[(index + 1) % len(self.players)]
        mess_et.json_str = player.transformIntoJSON(next)
        self.conn_my_local_service.EndTurn(mess_et)

    def CheckStarted(self):
        return self.conn_auth.ReturnStarted(clientController.Empty())

    def StartGame(self):
        l = self.conn_auth.GetPlayerList(self.privateInfo)
        self.players = player.transformFullListFromJSON(l.list)
        self.playersCheck = self.players.copy()
        mess = clientController.PlayerMessage()
        mess.json_str = player.transformFullListIntoJSON(self.players)
        self.conn_my_local_service.RecieveList(mess)
        #print('NewList', self.players)
        self.__set_user_list()

        # avviare le connessioni con grpc ai giocatori presenti in players tramite il campo ip
        for p in [x for x in self.players if x.getUid() != self.myPlayer.getUid()]:
            channel = grpc.insecure_channel(p.getIp() + ':' + str(portGame))
            self.conn_enemies.append(
                clientController_rpc.ClientControllerStub(channel))

        for enemy in self.conn_enemies:
            callback = partial(self.__ping_peer, enemy)
            threading.Thread(target=callback, daemon=True).start()

            callback = partial(self._listen_enemy_action_stream, enemy)
            threading.Thread(target=callback, daemon=True).start()

            callback = partial(self._listen_enemy_turn_stream, enemy)
            threading.Thread(target=callback, daemon=True).start()

        threading.Thread(target=self.__listen_for_terminated,
                         daemon=True).start()

        # TODO: toglie il player dalla lobby del server dopo 60 secondi
        callback = partial(self.conn_auth.StartGame, self.privateInfo)
        threading.Timer(15, callback).start()
        if l.id_first == self.privateInfo.u_id:
            mess_et = clientController.PlayerMessage()
            mess_et.json_str = player.transformIntoJSON(self.myPlayer)
            self.conn_my_local_service.EndTurn(mess_et)
            self.turnList.append(mess_et)
        return

    def _listen_enemy_action_stream(self, enemy):
        try:
            for action in enemy.ActionStream(clientController.Empty()):
                self.actionList.append(action)
        except grpc._channel._Rendezvous as err:
            print(err)

    def _listen_enemy_turn_stream(self, enemy):
        try:
            for turn in enemy.TurnStream(clientController.Empty()):
                self.turnList.append(turn)
        except grpc._channel._Rendezvous as err:
            print(err)

    def ActionStream(self):
        return self.conn_my_local_service.ActionStream(clientController.Empty())

    def TurnStream(self):
        return self.conn_my_local_service.TurnStream(clientController.Empty())

    def SendAction(self, send: player.Player, recieve: player.Player, actionType: int, amount: int):
        n = clientController.Action()
        n.sender = ""
        n.reciever = ""
        n.amount = amount
        n.action_type = actionType
        for p in self.players:
            if p.getUid() == send.getUid():
                n.sender = player.transformIntoJSON(p)
                usr = p
            if p.getUid() == recieve.getUid():
                n.reciever = player.transformIntoJSON(p)

        for p in self.players:
            if p.getUid() == recieve.getUid():
                if n.action_type == 0:
                    p.takeDamage(int(n.amount))
                elif n.action_type == 1:
                    p.heal(int(n.amount))
                elif n.action_type == 2:
                    p.obtainBlock(int(n.amount))
                else:
                    print("OPS! Error with the actions.")
        self.conn_my_local_service.SendAction(n)

    def SendFinishGame(self, f):
        n = clientController.EndNote()
        n.fin = f
        self.conn_my_local_service.FinishGame(n)

    def FinishStream(self):
        return self.conn_my_local_service.FinishStream(clientController.Empty())
