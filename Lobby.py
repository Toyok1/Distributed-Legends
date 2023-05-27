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
        # TODO: add dictionary of getUid for lobbyId and List of this player

    def SendPrivateInfo(self, request: lobby_auth.PrivateInfo, context):
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
        return lobby_auth.Empty_Lobby()

    def StartedStream(self, request, context):
        lastindex = 0
        while True:
            while len(self.start_stream) > lastindex:
                n = self.start_stream[lastindex]
                lastindex += 1
                yield n

    def StartGame(self, request: lobby_auth.PrivateInfo, context):
        self.start_stream.append(lobby_auth.StartedBool(name="game started", mesage=player.tranformFullListIntoJSON(self.listUser)))
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
