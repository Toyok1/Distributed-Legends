import os
import signal
import grpc
import time
from concurrent import futures

from cryptography.fernet import Fernet
from requests import get

from GRPCClientHelper import player
from GRPCClientHelper.config import port, key

import lobby_auth_pb2 as lobby_auth
import lobby_auth_pb2_grpc as lobby_auth_rpc


class Lobby(lobby_auth_rpc.LobbyAuthServer):
    def __init__(self, pId):
        self.pId = pId
        self.fernet = Fernet(key)
        self.listUser = []
        self.start_stream = []
        
        self.list_of_lobby = []
        
        self.list_of_lobby.append({'id_lobby': 3,'listPlayers':[{'ip':'127.0.0.1', 'unique_id':12, 'username':'Davide', 'user_type': 2, 'ping_time':'32443453534'}]})
        
        print(self.list_of_lobby)
        
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

    def _add_player_to_lobby(self, lobby_id,player):
        for lobby in self.list_of_lobby:
            if lobby['id_lobby'] == lobby_id:
                lobby['listPlayers'].append(player)
                return True
        return False

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
        if _get_lobby(request.id_lobby) == None:
            self.list_of_lobby.append({'id_lobby': request.id_lobby,'listPlayers':[new_user]})
        else:
            self._add_player_to_lobby(request.id_lobby,new_user)
        return lobby_auth.Empty_Lobby()

    '''def SendPrivateInfo(self, request: lobby_auth.PrivateInfo, context):
        encMessage = request.ip
        user = request.user
        decMessage = self.fernet.decrypt(encMessage).decode()
        u_id = request.u_id
        user_type = request.user_type
        new_user = player.Player(ip=decMessage, unique_id=u_id, username=user, user_type=user_type, ping_time=time.time())
        
        if user_type == 1:
            self.HOST = new_user
        if len(self.listUser) < 4 and not new_user in self.listUser:
            self.listUser.append(new_user)
        else:
            print("User already in the game or game already started")
        print("Player", self.listUser)
        # self.text_area.config(text='\n'.join([name.getUsername() for name in self.listUser]))
        return lobby_auth.Empty_Lobby()'''

    def StartedStream(self, request, context):
        lastindex = 0
        while True:
            while len(self.start_stream) > lastindex:
                n = self.start_stream[lastindex]
                lastindex += 1
                yield n

    def StartGame(self, request: lobby_auth.PrivateInfo, context):
        #myLobby = list(filter(lambda lobby: self.list_of_lobby['id_lobby'] == request.id_lobby, self.list_of_lobby))
        myLobby = self._get_players_by_lobby_id(request.id_lobby)
        print(myLobby)
        self.start_stream.append(lobby_auth.StartedBool(name="game started", mesage=player.tranformFullListIntoJSON(myLobby)))
        time.sleep(10)
        os.kill(self.pId, signal.SIGTERM)
        return lobby_auth.Empty_Lobby()


if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
    lobby_auth_rpc.add_LobbyAuthServerServicer_to_server(Lobby(os.getpid()), server)
    server.add_insecure_port('[::]:' + str(port))
    print('Lobby started. Listening...')
    server.start()
    print("Connect here: ", get('https://api.ipify.org').content.decode('utf8'))
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
