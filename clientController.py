import grpc
import time
import threading
from concurrent import futures
from GRPCClientHelper import player
import os
import clientController_pb2 as clientController
import clientController_pb2_grpc as rpc
import signal
from cryptography.fernet import Fernet
from requests import get
from GRPCClientHelper.config import port, key


class ClientController(rpc.ClientControllerServicer):
    def __init__(self, pId):
        self.clients = []
        self.actions = []
        self.hp = []
        self.attack = []
        self.listBlock = []
        self.listUser = []
        self.fernet = Fernet(key)
        self.processId = pId
        self.TERMINATE = None

        threading.Thread(target=self.__clean_user_list, daemon=True).start()
        threading.Thread(target=self.__keep_alive, daemon=True).start()

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
            if self.isStartedGame:
                # print("Player List", self.listUser)
                for user in self.listUser:
                    if float(time.time()) - float(user.getPingTime()) > 10.0:
                        # print("lost ping with ", user)
                        # if it's the turn user, pick another
                        if user.getUid() == self.LAST_USER_TURN.getUid():  # disconnected while it's my turn
                            # add a turn message for the next guy
                            # print("IT WAS MY TURN")
                            for i in range(0, len(self.listUser)):
                                if self.LAST_USER_TURN.getUid() == self.listUser[i].getUid():
                                    userNext = self.listUser[(
                                        i+1) % len(self.listUser)]
                                    n = clientController.PlayerMessage()
                                    n.json_str = player.transformIntoJSON(
                                        userNext)
                                    # TODO get this to work
                                    self.turns.append(n)
                        self.listUser.remove(user)
                if len(self.listUser) == 1:
                    # print("length userList == 1")
                    n = clientController.EndNote()
                    # only two messages that should ever be displayed
                    n.MonsterWin = "YOU CAN RULE THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                    # only two messages that should ever be displayed
                    n.HeroesWin = "YOU SAVED THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                    n.MonsterDefeat = "How did you get here?"
                    n.HeroesDefeat = "Looking for easter eggs?"
                    n.fin = True if self.listUser[0].getUsertype(
                    ) == 1 else False
                    self.finish.append(n)
                    self.isStartedGame = False
                    self.TERMINATE = True
                    break

                    # list of all types of users. If there is no monter the heroes win by default.
                if not 1 in [int(u.getUsertype()) for u in self.listUser]:
                    # print("NO MONSTERS")
                    n = clientController.EndNote()
                    n.MonsterWin = "Noone expects the spanish inquisition!"
                    # the only message to ever be displayed
                    n.HeroesWin = "YOU SAVED THE WORLD BECAUSE THE MONSTER DISCONNECTED"
                    n.MonsterDefeat = "How did you get here?"
                    n.HeroesDefeat = "Looking for easter eggs?"
                    n.fin = False
                    self.finish.append(n)
                    self.isStartedGame = False
                    self.TERMINATE = True
                    break

            time.sleep(2.5)

    def __distributeHealth(self):
        for user in self.listUser:
            if user.getUsertype() == 1:
                user.setHp(100)
            else:
                user.setHp(50)
                
    def SendAction(self, request: clientController.Action, context):
        n = request
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
        self.actions.append(request)
        return clientController.Empty()

    def ActionStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.actions) > lastindex:
                n = self.actions[lastindex]
                lastindex += 1
                # #print("Yielding action = ", n)

                yield n

    def SendPrivateInfo(self, request: clientController.PrivateInfo, context):
        encMessage = request.ip
        user = request.user
        decMessage = self.fernet.decrypt(encMessage).decode()
        u_id = request.u_id
        user_type = request.user_type
        new_user = player.Player(
            ip=decMessage, unique_id=u_id, username=user, user_type=user_type, ping_time=time.time())

        if user_type == 1:
            self.HOST = new_user
        if len(self.listUser) == 0:
            b = clientController.PlayerMessage()
            b.json_str = player.transformIntoJSON(new_user)
            self.turns.append(b)
            self.LAST_USER_TURN = new_user
        if len(self.listUser) < 4 and not new_user in self.listUser and self.isStartedGame == False:
            self.listUser.append(new_user)
        else:
            print("User already in the game or game already started")
        # #print(self.listUser)
        # something needs to be returned required by protobuf language, we just return empty msg
        return clientController.Empty()

    def SendPing(self, request: clientController.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(
            request.ip).decode(), request.id)
        return clientController.Pong(message="Thanks, friend!" if self.TERMINATE != True else "SET_FINISHED", list_players=player.tranformFullListIntoJSON(self.listUser))

    def FinishGame(self, request_iterator, context):
        # #print("FinishGame called")
        self.isStartedGame = False
        n = clientController.EndNote()
        n.MonsterWin = "YOU CAN RULE THE WORLD"
        n.HeroesWin = "YOU SAVED THE WORLD"
        n.MonsterDefeat = "THE HEROES PREVENTED YOU FROM TAKING OVER THE WORLD"
        n.HeroesDefeat = "YOU FAILED TO SAVE THE WORLD"
        n.fin = request_iterator.fin
        self.finish.append(n)
        return clientController.Empty()

    def FinishStream(self, request_iterator, context):
        # #print("FinishStream called")

        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.finish) > lastindex:
                n = self.finish[lastindex]
                # #print(n)
                lastindex += 1
                yield n


if __name__ == '__main__':
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1000))  
    rpc.add_ClientControllerServicer_to_server(ClientController(
        os.getpid()), server)  
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)