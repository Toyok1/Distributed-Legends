import grpc
import time
import threading
from concurrent import futures
from GRPCClientHelper import player
import os

import chat_pb2 as chat
import chat_pb2_grpc as rpc

import signal

from cryptography.fernet import Fernet
from requests import get
from GRPCClientHelper.config import port, key


class ChatServer(rpc.ChatServerServicer):
    def __init__(self, pId):
        self.finish = []
        self.clients = []
        # List with all the chat history
        self.chats = []
        self.actions = []
        self.hp = []
        self.attack = []
        self.listBlock = []
        self.turns = []
        self.listUser = []  # every element is a Player
        self.fernet = Fernet(key)
        self.processId = pId
        self.LAST_USER_TURN = None
        self.isStartedGame = False

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
        # if a user (hero) is more than 5 seconds from its last ping we count it as dead and, if it is its turn we skip it and we go to the next user.
        while True:
            if self.isStartedGame:
                # #print("Player List", self.listUser)
                for user in self.listUser:
                    if float(time.time()) - float(user.getPingTime()) > 10.0:
                        # print("lost ping with ", user.getUsername(), " time ", float(time.time()) - float(user.getPingTime()))
                        # if it's the turn user, pick another
                        if len(self.listUser) == 1:
                            n = chat.EndNote()
                            # only two messages that should ever be displayed
                            n.MonsterWin = "YOU CAN RULE THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                            # only two messages that should ever be displayed
                            n.HeroesWin = "YOU SAVED THE WORLD BECAUSE EVERYONE ELSE DISCONNECTED"
                            n.MonsterDefeat = "How did you get here?"
                            n.HeroesDefeat = "Looking for easter eggs?"
                            n.fin = True if self.listUser[0].getUsertype(
                            ) == 1 else False
                            self.finish.append(n)
                            break

                        # list of all types of users. If there is no monter the heroes win by default.
                        if not 1 in [int(u.getUsertype()) for u in self.listUser]:
                            n = chat.EndNote()
                            n.MonsterWin = "Noone expects the spanish inquisition!"
                            # the only message to ever be displayed
                            n.HeroesWin = "YOU SAVED THE WORLD BECAUSE THE MONSTER DISCONNECTED"
                            n.MonsterDefeat = "How did you get here?"
                            n.HeroesDefeat = "Looking for easter eggs?"
                            n.fin = False
                            self.finish.append(n)
                            break

                        if user.getUid() == self.LAST_USER_TURN.getUid():  # disconnected while it's my turn
                            # add a turn message for the next guy
                            for i in range(0, len(self.listUser)):
                                if self.LAST_USER_TURN.getUid() == self.listUser[i].getUid():
                                    userNext = self.listUser[(
                                        i+1) % len(self.listUser)]
                                    n = chat.PlayerMessage()
                                    n.json_str = player.transformIntoJSON(
                                        userNext)
                                    # TODO get this to work
                                    self.EndTurn(n, None)
                        # self.listUser.remove(user)
            time.sleep(2.5)

    def __distributeHealth(self):
        for user in self.listUser:
            if user.getUsertype() == 1:
                user.setHp(100)
            else:
                user.setHp(50)

    # The stream which will be used to send new messages to clients
    def ChatStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.chats) > lastindex:
                n = self.chats[lastindex]
                lastindex += 1
                yield n

    def SendNote(self, request: chat.Note, context):
        # this is only for the server console
        # print("[{}] {}".format(request.name, request.message))
        # Add it to the chat history
        self.chats.append(request)
        # something needs to be returned required by protobuf language, we just return empty msg
        return chat.Empty()

    def SendAction(self, request: chat.Action, context):
        # new_a = {"ip_sender": self.fernet.decrypt(request.ip_sender).decode(), "ip_reciever": self.fernet.decrypt(request.ip_reciever).decode(), "amount": int(request.amount)}
        self.actions.append(request)
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
        # print("New Action = ", request)
        # manage the fact that people are attacking you
        return chat.Empty()

    def ActionStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.actions) > lastindex:
                n = self.actions[lastindex]
                lastindex += 1
                # print("Yielding action = ", n)

                yield n

    def SendPrivateInfo(self, request: chat.PrivateInfo, context):
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
            b = chat.PlayerMessage()
            b.json_str = player.transformIntoJSON(new_user)
            self.turns.append(b)
            self.LAST_USER_TURN = new_user
        self.listUser.append(new_user)
        # print(self.listUser)
        # something needs to be returned required by protobuf language, we just return empty msg
        return chat.Empty()

    def SendPing(self, request: chat.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(
            request.ip).decode(), request.id)
        return chat.Pong(message="Thanks, friend!", list_players=player.tranformFullListIntoJSON(self.listUser))

    def EndTurn(self, request: chat.PlayerMessage, context):
        # print("end turn")
        userLast = player.transformFromJSON(request.json_str)
        self.LAST_USER_TURN = userLast
        for i in range(0, len(self.listUser)):
            # if self.listUser[i]["ip"] == ipLast:
            if userLast.getUid() == self.listUser[i].getUid():
                userNext = self.listUser[(i+1) % len(self.listUser)]
        # create the return message, encrypt the ip and send it in broadcast to everyone.
        # print("prossimo turno: ", userNext.getUsername())
        r = chat.PlayerMessage()
        r.json_str = player.transformIntoJSON(userNext)
        self.turns.append(r)

        return chat.Empty()

    def TurnStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.turns) > lastindex:
                n = self.turns[lastindex]
                # print(n)
                lastindex += 1
                yield n

    def ReturnStarted(self, request_iterator, context):
        b = chat.StartedBool()
        b.started = self.isStartedGame
        return b

    def StartGame(self, request: chat.PrivateInfo, context):
        # print('StartGame ', self.listUser)
        if self.HOST.getUsername() == request.user:
            # print("L'host è onnipotente")
            self.isStartedGame = True
            self.__distributeHealth()
        return chat.Empty()

    def FinishGame(self, request_iterator, context):
        # print("FinishGame called")
        self.isStartedGame = False
        n = chat.EndNote()
        n.MonsterWin = "YOU CAN RULE THE WORLD"
        n.HeroesWin = "YOU SAVED THE WORLD"
        n.MonsterDefeat = "THE HEROES PREVENTED YOU FROM TAKING OVER THE WORLD"
        n.HeroesDefeat = "YOU FAILED TO SAVE THE WORLD"
        n.fin = request_iterator.fin
        self.finish.append(n)
        return chat.Empty()

    def FinishStream(self, request_iterator, context):
        # print("FinishStream called")

        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.finish) > lastindex:
                n = self.finish[lastindex]
                # print(n)
                lastindex += 1
                yield n


if __name__ == '__main__':
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1000))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(
        os.getpid()), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    print("Connect here: ", get('https://api.ipify.org').content.decode('utf8'))
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
