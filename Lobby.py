import os
import signal
import grpc
import time
from concurrent import futures
import threading

from cryptography.fernet import Fernet
from requests import get

from GRPCClientHelper import player
from GRPCClientHelper.config import portAuth, key

import lobby_auth_pb2 as lobby_auth
import lobby_auth_pb2_grpc as lobby_auth_rpc


class Lobby(lobby_auth_rpc.LobbyAuthServer):
    def __init__(self, pId):
        self.pId = pId
        self.fernet = Fernet(key)
        self.listUser = []
        self.start_stream = []
        self.list_of_lobby = []

    def _get_lobby(self, lobby_id):
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                return lobby
        return None

    def _get_players_by_lobby_id(self, lobby_id):
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                return lobby['listPlayers']
        return None
    
    def _get_player_by_lobby_id(self, player_id, lobby_id):
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                for player in lobby['listPlayers']:
                    if player.getUid() == player_id:
                        return player
        return None

    def _add_player_to_lobby(self, lobby_id, player):
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                lobby['listPlayers'].append(player)
                return True
        return False

    def _remove_player_from_list(self, lobby_id, player):
        lobby_remove = None
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                print('---listPlayers', lobby['listPlayers'])
                lobby['listPlayers'].remove(player)
                if len(lobby['listPlayers']) == 0:
                    lobby_remove = lobby
        if lobby_remove is not None:
            self.list_of_lobby.remove(lobby_remove)
    
    def _get_my_lobby_by_player_id(self, player_id):
        for lobby in self.list_of_lobby:
            for player in lobby['listPlayers']:
                if player['unique_id'] == player_id:
                    return lobby
        return None

    def _get_player_ip(self, player_ip):
        encMessage = player_ip
        return self.fernet.decrypt(encMessage).decode()

    # controlla se esiste la lobby con id_lobby == request.id_lobby e se esiste aggiungi il nuovo player altrimenti aggiungi a list_of_lobby un nuovo oggetto con id_lobby = equest.id_lobby e aggiungi il new_user alla corrispettiva lista listplayer
    def SendPrivateInfo(self, request: lobby_auth.PrivateInfo, context):
        ip = self._get_player_ip(request.ip)
        user = request.user
        u_id = request.u_id
        user_type = request.user_type
        new_user = player.Player(ip=ip, unique_id=u_id, username=user, user_type=user_type, ping_time=time.time())
        if self._get_lobby(request.id_lobby) == None:
            self.list_of_lobby.append({'id_lobby': request.id_lobby,'listPlayers':[new_user]})
        else:
            self._add_player_to_lobby(request.id_lobby,new_user)
        print(self.list_of_lobby)
        
        list = lobby_auth.PlayersList()
        list.list = player.transformFullListIntoJSON(self._get_players_by_lobby_id(request.id_lobby) if self._get_players_by_lobby_id(request.id_lobby) != None else [])
        return list

    def StartGame(self, request: lobby_auth.PrivateInfo, context):
        playerObj = self._get_player_by_lobby_id(request.u_id, request.id_lobby) 
        print('player', playerObj, 'id_lobby', request.id_lobby, 'lobbys', self.list_of_lobby)       
        self._remove_player_from_list(request.id_lobby, playerObj)
        print('player 2', playerObj, 'id_lobby 2', request.id_lobby, 'lobbys 2', self.list_of_lobby)       
        return lobby_auth.Empty_Lobby()

    def GetPlayerList(self, request: lobby_auth.PrivateInfo, context):
        myLobby = self._get_players_by_lobby_id(request.id_lobby)
        list = lobby_auth.PlayersList()
        list.list = player.transformFullListIntoJSON(myLobby)
        return list
    
if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
    lobby_auth_rpc.add_LobbyAuthServerServicer_to_server(Lobby(os.getpid()), server)
    server.add_insecure_port('[::]:' + str(portAuth))
    server.start()
    print('Lobby started. Listening...')
    #print("Connect here: ", get('https://api.ipify.org').content.decode('utf8'))
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
