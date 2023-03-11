import grpc
import time
import random
import threading
from concurrent import futures
import uuid
from GRPCClientHelper import player

import chat_pb2 as chat
import chat_pb2_grpc as rpc

from cryptography.fernet import Fernet

port = 11912  # decide if we have to change this port
key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='


class ChatServer(rpc.ChatServerServicer):
    def __init__(self):
        self.clients = []
        # List with all the chat history
        self.chats = []
        self.actions = []
        self.hp = []
        self.listBlock = []
        self.turns = []
        self.listUser = []  # every element is a Player
        self.fernet = Fernet(key)

        threading.Thread(target=self.__clean_user_list, daemon=True).start()

        self.initialList = chat.InitialList()
        self.initialList.json_str = ""
        self.isStartedGame = False

    def __updateUserList(self, req_ip, req_id):
        for usr in self.listUser:
            if usr.getIp() == req_ip and usr.getUid() == req_id:
                # print("pinged", usr)
                usr.setPingTime(time.time())

    def __clean_user_list(self):
        # il tempo lo calcola il server
        while True:
            # print("Player List", self.listUser)
            for user in self.listUser:
                if (int(time.time()) - int(user.getPingTime())) > 5:
                    self.listUser.remove(user)
            time.sleep(2.5)

    '''def __createBoard(self):
        self.activeMap.length = random.randint(40,90)
        self.activeMap.board =  str(random.choices(range(0,  8), k = self.activeMap.length))'''

    def __distributeHealth(self):
        self.listUser[random.randint(0, len(self.listUser))].setUsertype(1)
        for user in self.listUser:
            # print(user)
            if user.getUsertype() == 1:
                # self.hp.append({"ip": user["ip"], "hp": 100, "block": 0, "user": user["user"], "player_type": 1}) #TODO tweak values
                user.setHp(100)
            else:
                # self.hp.append({"ip": user["ip"], "hp": 50, "block": 0, "user": user["user"], "player_type": 0}) #TODO tweak values
                user.setUsertype(2)
                user.setHp(50)

        '''values = []
        values2 = []
        values3 = []
        values4 = []
        for d in self.hp:
            values.append(d["user"])
            values2.append(d["hp"])
            values3.append(d["player_type"])
            values4.append(d["ip"])

        name_hp = str(values) + str(values2)
        mmmap = chat.InitialList()
        mmmap.length = length
        mmmap.name_hp = name_hp
        mmmap.player_type = str(values3)
        mmmap.ip = str(values4)'''

        mmmap = chat.InitialList()
        mmmap.length = len(self.listUser)
        mmmap.json_str = player.tranformFullListIntoJSON(self.listUser)
        print(mmmap)
        self.initialList = mmmap

    # The stream which will be used to send new messages to clients
    def ChatStream(self, request_iterator, context):
        """
        This is a response-stream type call. This means the server can keep sending messages
        Every client opens this connection and waits for server to send new messages
        :param request_iterator:
        :param context:
        :return:
        """
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
        print("[{}] {}".format(request.name, request.message))
        # Add it to the chat history
        self.chats.append(request)
        # something needs to be returned required by protobuf language, we just return empty msg
        return chat.Empty()

    def SendHealth(self, request: chat.Health, context):
        # new_h = {"ip": self.fernet.decrypt(request.ip).decode(), "hp": request.hp, "user": str(request.user)}
        self.hp.append(request)
        # print(new_h)
        return chat.Empty()

    def SendBlock(self, request: chat.Block, context):
        # new_h = {"ip": self.fernet.decrypt(request.ip).decode(), "hp": request.hp, "user": str(request.user)}
        self.listBlock.append(request)
        print(request)
        # print(new_h)
        return chat.Empty()

    def SendAction(self, request: chat.Action, context):
        # new_a = {"ip_sender": self.fernet.decrypt(request.ip_sender).decode(), "ip_reciever": self.fernet.decrypt(request.ip_reciever).decode(), "amount": int(request.amount)}
        self.actions.append(request)
        # manage the fact that people are attacking you
        return chat.Empty()

    def HealthStream(self, request_iterator, context):
        """
        This is a response-stream type call. This means the server can keep sending messages
        Every client opens this connection and waits for server to send new messages
        :param request_iterator:
        :param context:
        :return:
        """
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.hp) > lastindex:
                n = self.hp[lastindex]
                print(self.hp)
                lastindex += 1
                yield n

    def BlockStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.listBlock) > lastindex:
                '''n = chat.Block()
                n.ip = self.fernet.encrypt(self.blockList[lastindex]["ip"].encode())
                n.block = self.blockList[lastindex]["block"]
                n.user = self.blockList[lastindex]["user"]'''
                n = self.listBlock[lastindex]
                # print(n)
                lastindex += 1
                yield n

    def ActionStream(self, request_iterator, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.actions) > lastindex:
                n = self.actions[lastindex]
                lastindex += 1
                yield n

    def SendPrivateInfo(self, request: chat.PrivateInfo, context):
        """
        This method is called when a clients sends a PrivateInfo to the server.
        :param request:
        :param context:
        :return:
        """
        encMessage = request.ip
        user = request.user
        decMessage = self.fernet.decrypt(encMessage).decode()
        u_id = request.u_id
        user_type = request.user_type
        # new_user  =  {"user":  user,  "ip":  decMessage,  "ping_time":  time.time(), "player_type": 0}

        new_user = player.Player(
            ip=decMessage, unique_id=u_id, username=user, user_type=user_type, ping_time=time.time())
        if len(self.listUser) == 0:
            b = chat.PlayerMessage()
            b.json_str = player.transformIntoJSON(new_user)
            self.turns.append(b)
        self.listUser.append(new_user)
        # something needs to be returned required by protobuf language, we just return empty msg
        return chat.Empty()

    def SendPing(self, request: chat.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(
            request.ip).decode(), request.id)
        return chat.Pong(message="Thanks, friend!")

    def EndTurn(self, request: chat.PlayerMessage, context):
        '''ipLast = self.fernet.decrypt(request.ip).decode()
        userLast = request.user
        ipNext = self.listUser[0].getIp() #if i can't find the ip we default to the first person in the list
        userNext = self.listUser[0].getIp()'''
        userLast = player.transformFromJSON(request.json_str)

        for i in range(0, len(self.listUser)):
            # if self.listUser[i]["ip"] == ipLast:
            if userLast.getUid() == self.listUser[i].getUid():
                '''ipNext = self.listUser[(i+1)%len(self.listUser)]["ip"]
                userNext = self.listUser[(i+1)%len(self.listUser)]["user"]'''
                userNext = self.listUser[(i+1) % len(self.listUser)]
        # create the return message, encrypt the ip and send it in broadcast to everyone.
        r = chat.PlayerMessage()
        '''r.ip = self.fernet.encrypt(ipNext.encode()) #TODO: create the methods to recieve the broadcast
        r.user = userNext'''
        r.json_str = player.transformIntoJSON(userNext)
        self.turns.append(r)

        return chat.Empty()

    def TurnStream(self, request_iterator, context):
        lastindex = 0
        while True:
            while len(self.turns) > lastindex:
                n = self.turns[lastindex]
                print(n)
                lastindex += 1
                yield n

    def GetInitialList(self, request_iterator, context):
        """ Create game board and send to client, if map is none client resend request"""
        return self.initialList

    def ReturnStarted(self, request_iterator, context):
        b = chat.StartedBool()
        b.started = self.isStartedGame
        return b

    def StartGame(self, request: chat.PrivateInfo, context):
        print('StartGame', self.listUser)
        ip = self.fernet.decrypt(request.ip).decode()
        # if self.listUser[0]["ip"] == ip:    #TODO quando si testa su macchine diverse usare l'ip
        '''n = chat.PlayerMessage()
        n.json_str = player.transformIntoJSON(self.listUser[0])'''
        if self.listUser[0].getUsername() == request.user:
            print("L'host è onnipotente")
            self.isStartedGame = True
            self.__distributeHealth()
            # self.__createBoard()
        # self.turns.append(n)
        return self.initialList

    def FinishGame(self, request_iterator, context):
        self.isStartedGame = False
        # self.initialList.name_hp = None
        n = chat.Note()
        n.message = "OK"
        return n


if __name__ == '__main__':
    port = 11912  # a random port for the server to run on
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=10))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(
        ChatServer(), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
