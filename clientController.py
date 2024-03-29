from concurrent import futures
import grpc
import os
import signal
import time
import threading

from cryptography.fernet import Fernet
from requests import get

from GRPCClientHelper import player
from GRPCClientHelper.config import portGame, key

import clientController_pb2 as clientController
import clientController_pb2_grpc as rpc


class ClientController(rpc.ClientControllerServicer):
    def __init__(self, pId):
        self.clients = []
        self.actions = []
        self.finish = []
        self.Uid = None
        self.turns = []
        self.attack = []
        self.listBlock = []
        self.listUser = []
        self.terminated = []
        self.fernet = Fernet(key)
        self.processId = pId
        self.TERMINATE = None

        threading.Thread(target=self.__clean_user_list, daemon=True).start()
        # threading.Thread(target=self.__keep_alive, daemon=True).start()

    def __updateUserList(self, req_ip, req_id):
        for usr in self.listUser:
            if usr.getIp() == req_ip and usr.getUid() == req_id:
                # #print("pinged", usr)
                usr.setPingTime(time.time())

    def __keep_alive(self):
        while True:
            time.sleep(180)  # TODO change number of seconds of inactivity
            if len(self.listUser) == 0:
                os.kill(self.processId, signal.SIGTERM)

    def __clean_user_list(self):
        # if a user (hero) is more than 10 seconds from its last ping we count it as dead and, if it is its turn we skip it and we go to the next user.
        while True:
            # print("Player List", self.listUser)
            for user in [x for x in self.listUser if x.getUid() != self.Uid]:
                if float(time.time()) - float(user.getPingTime()) > 10.0:
                    #print("lost ping with ", user)
                    self.listUser.remove(user)
                    #print("NEW LIST ", self.listUser)
                    m = clientController.PlayerMessage()
                    m.json_str = player.transformIntoJSON(user)
                    self.terminated.append(m)
            # DISCONNECTION HANDLER
            if len(self.listUser) == 1:
                # print("length userList == 1")
                n = clientController.EndNote()
                # only two messages that should ever be displayed
                n.fin = self.listUser[0].getUsername()
                self.finish.append(n)
                self.isStartedGame = False
                self.TERMINATE = True
                break

            # list of all types of users. If there is no monster the heroes win by default.
            # NORMAL END GAME HANDLER (ONLY 1 PLAYER WITH MORE THAN 0 HP)
            n = clientController.EndNote()
            time.sleep(2.5)

    def __distributeHealth(self):
        for user in self.listUser:
            if user.getUsertype() == 1:
                user.setHp(100)
            else:
                user.setHp(50)

    def SendAction(self, request: clientController.Action, context):        
        self.actions.append(request)
        return clientController.Empty()

    def RecieveUid(self, request: clientController.PlayerMessage, context):
        self.Uid = request.json_str
        return clientController.Empty()

    def ActionStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.actions) > lastindex:
                n = self.actions[lastindex]
                lastindex += 1
                yield n

    def TerminatedStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.terminated) > lastindex:
                n = self.terminated[lastindex]
                lastindex += 1
                yield n

    def EndTurn(self, request: clientController.PlayerMessage, context):
        self.turns.append(request)
        return clientController.Empty()

    def TurnStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.turns) > lastindex:
                n = self.turns[lastindex]
                lastindex += 1
                yield n

    def SendPing(self, request: clientController.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(
            request.ip).decode(), request.id)
        pong = clientController.Pong()
        pong.message = "Thanks, friend!" if self.TERMINATE != True else "SET_FINISHED"
        pong.u_id_sender = self.Uid

        return pong

    def RecieveList(self, request, context):
        self.listUser = player.transformFullListFromJSON(request.json_str)
        return clientController.Empty()

    def FinishGame(self, request_iterator, context):
        self.isStartedGame = False
        n = clientController.EndNote()
        n.fin = request_iterator.fin
        self.finish.append(n)
        return clientController.Empty()

    def FinishStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.finish) > lastindex:
                n = self.finish[lastindex]
                lastindex += 1
                yield n


if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1000))
    rpc.add_ClientControllerServicer_to_server(
        ClientController(os.getpid()), server)
    print('Starting my clientController. Listening...')
    server.add_insecure_port('[::]:' + str(portGame))
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
