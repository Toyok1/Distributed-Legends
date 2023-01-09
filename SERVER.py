import grpc
import time

from concurrent import futures

import chat_pb2
import chat_pb2_grpc

class ChatServer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = []

    def Connect(self, request, context):
        print(f"{request.name} has connected")
        self.clients.append(request.name)
        return chat_pb2.ConnectResponse(message=f"Welcome, {request.name}!")

    def Disconnect(self, request, context):
        print(f"{request.name} has disconnected")
        self.clients.remove(request.name)
        return chat_pb2.DisconnectResponse(message=f"Goodbye, {request.name}!")

    def SendMessage(self, request, context):
        print(f"{request.name}: {request.message}")
        for client in self.clients:
            if client != request.name:
                yield chat_pb2.SendMessageResponse(name=request.name, message=request.message)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()