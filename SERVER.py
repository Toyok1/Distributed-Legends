import grpc
import time

from concurrent import futures

import chat_pb2
import chat_pb2_grpc

class ChatServer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
<<<<<<< Updated upstream
        self.clients = []
=======
        # List with all the chat history
        self.chats = []
        self.hp = []
        self.turns = []
        self.listUser = [] #  every element is a dictionary with  {"name":  username,  "ip": user public ip , "ping_time": timestamp of last pingpong , "role": Bool}
        self.fernet = Fernet(key)   
        threading.Thread(target=self.__clean_user_list, daemon=True).start()
        self.activeMap = chat.Map()
        self.activeMap.board = ""
        self.isStartedGame = False
>>>>>>> Stashed changes

    def Connect(self, request, context):
        print(f"{request.name} has connected")
        self.clients.append(request.name)
        return chat_pb2.ConnectResponse(message=f"Welcome, {request.name}!")

<<<<<<< Updated upstream
    def Disconnect(self, request, context):
        print(f"{request.name} has disconnected")
        self.clients.remove(request.name)
        return chat_pb2.DisconnectResponse(message=f"Goodbye, {request.name}!")
=======
    def  __updateUserList(self, req_ip):
        for  utente  in  self.listUser:
            if  utente["ip"]  ==  req_ip: 
                utente["ping_time"]  =  time.time() 
    
    '''def __createBoard(self):
        self.activeMap.length = random.randint(40,90)
        self.activeMap.board =  str(random.choices(range(0,  8), k = self.activeMap.length))'''

    def __distributeHealth(self):
        random.choice(self.listUser)["role"] = True
        for user in self.listUser:
            if user["role"]:
                self.hp.append({"ip": user["ip"], "hp": 100, "user": user["name"]}) #TODO tweak values
            else:
                self.hp.append({"ip": user["ip"], "hp": 50, "user": user["name"]}) #TODO tweak values
        
        length = len(self.hp)

        values = []
        values2 = []
        for d in self.hp:
                values.append(d["user"])
        for d in self.hp:
                values2.append(d["hp"])

        board = str(values) + str(values2)
        mmmap = chat.Map()
        mmmap.length = length
        mmmap.board = board
        self.activeMap = mmmap
    
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

    def SendHealth(self, request: chat.Health, context):
        new_h = {"ip": self.fernet.decrypt(request.ip).decode(), "hp": request.hp}
        self.hp.append(new_h)
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
                n = chat.Health()
                n.ip = self.fernet.encrypt(self.hp[lastindex]["ip"].encode())
                n.hp = self.hp[lastindex]["hp"]
                lastindex += 1
                yield n
>>>>>>> Stashed changes

    def SendMessage(self, request, context):
        print(f"{request.name}: {request.message}")
        for client in self.clients:
            if client != request.name:
                yield chat_pb2.SendMessageResponse(name=request.name, message=request.message)

<<<<<<< Updated upstream
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServer(), server)
    server.add_insecure_port("[::]:50051")
=======
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
        
        new_user  =  {"name":  user,  "ip":  decMessage,  "ping_time":  time.time(), "role": False}
        if len(self.listUser) == 0:
            self.turns.append(request)
        self.listUser.append(new_user)
        return chat.Empty()  # something needs to be returned required by protobuf language, we just return empty msg

    def SendPing(self, request: chat.Ping, context):
        """ Fulfills SendPing RPC defined in ping.proto """
        self.__updateUserList(self.fernet.decrypt(request.ip).decode()) 
        return chat.Pong(message="Thanks, friend!")
    
    def EndTurn(self, request: chat.PrivateInfo, context):
        ipLast = self.fernet.decrypt(request.ip).decode()
        userLast = request.user
        ipNext = self.listUser[0]["ip"] #if i can't find the ip we default to the first person in the list
        userNext = self.listUser[0]["ip"]

        for i in range(0,len(self.listUser)):
            #if self.listUser[i]["ip"] == ipLast:
            if userLast == self.listUser[i]["name"]:
                ipNext = self.listUser[(i+1)%len(self.listUser)]["ip"]
                userNext = self.listUser[(i+1)%len(self.listUser)]["name"]
        r = chat.PrivateInfo() #create the return message, encrypt the ip and send it in broadcast to everyone.
        r.ip = self.fernet.encrypt(ipNext.encode()) #TODO: create the methods to recieve the broadcast
        r.user = userNext
        self.turns.append(r)

        return chat.Empty()

    def TurnStream(self, request_iterator,context):
        lastindex = 0
        while True:
            while len(self.turns) > lastindex:
                n = self.turns[lastindex]
                lastindex += 1
                yield n
                
    def GetActiveMap(self, request_iterator, context):
        """ Create game board and send to client, if map is none client resend request"""
        return self.activeMap

    
    def StartGame(self, request: chat.PrivateInfo, context):
        print('StartGame', self.listUser)
        ip = self.fernet.decrypt(request.ip).decode()
        #if self.listUser[0]["ip"] == ip:    #TODO quando si testa su macchine diverse usare l'ip
        if self.listUser[0]["name"] == request.user:
            print("L'host è onnipotente")
            self.isStartedGame = True
            self.__distributeHealth()
            #self.__createBoard()
        return self.activeMap
    
    def FinishGame(self, request_iterator, context):
        self.isStartedGame = False
        #self.activeMap.board = None
        n = chat.Note()
        n.message = "OK" 
        return n

if __name__ == '__main__':
    port = 11912  # a random port for the server to run on
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))  # create a gRPC server
    rpc.add_ChatServerServicer_to_server(ChatServer(), server)  # register the server to gRPC
    # gRPC basically manages all the threading and server responding logic, which is perfect!
    print('Starting server. Listening...')
    server.add_insecure_port('[::]:' + str(port))
>>>>>>> Stashed changes
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()