import grpc
import time
import threading
from concurrent import futures
from GRPCClientHelper import player
import os
import tkinter as tk

import chat_pb2 as chat
import chat_pb2_grpc as rpc

import signal

from cryptography.fernet import Fernet
from requests import get
from GRPCClientHelper.config import port, key


class Lobby(rpc.ChatServerServicer):
    def __init__(self, pId):
        self.pId = pId
        self.fernet = Fernet(key)
        # self.window = MainWindow
        # self.setup_ui()
        self.listUser = []
        self.start_stream = []
        # self.window.mainloop()

    def do_nothing(self):
        pass

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
        if len(self.listUser) < 4 and not new_user in self.listUser:
            self.listUser.append(new_user)
        else:
            print("User already in the game or game already started")
        # self.text_area.config(text='\n'.join([name.getUsername() for name in self.listUser]))
        return chat.Empty()

    def StartedStream(self, request, context):
        lastindex = 0
        # For every client a infinite loop starts (in gRPC's own managed thread)
        while True:
            # Check if there are any new messages
            while len(self.start_stream) > lastindex:
                n = self.start_stream[lastindex]
                lastindex += 1
                yield n

    def StartGame(self, request: chat.PrivateInfo, context):
        self.start_game()
        return chat.Empty()

    def start_game(self):
        self.start_stream.append(chat.StartedBool(
            name="game started", mesage=player.tranformFullListIntoJSON(self.listUser)))
        time.sleep(10)
        os.kill(self.pId, signal.SIGTERM)

    def setup_ui(self):
        self.master_frame = tk.Frame(self.window)
        self.master_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.master_frame.columnconfigure(0, weight=1, minsize=300)
        self.master_frame.rowconfigure(0, weight=1, minsize=200)
        self.master_frame.rowconfigure(1, weight=1, minsize=100)
        self.text_frame = tk.Frame(
            self.master_frame, bg="", width=300, height=200)
        # self.text_frame.place(x=0, y=0, width=300, height=200)
        self.text_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.text_area = tk.Label(
            self.text_frame, text="Welcome to the lobby!", bg="white", fg="black")
        self.text_area.grid(row=0, column=0, sticky=tk.NSEW)

        self.button_frame = tk.Frame(
            self.master_frame, bg="", width=300, height=100)
        # self.button_frame.place(x=0, y=0, width=300, height=200)
        self.button_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.button_connect = tk.Button(
            self.button_frame, text="Start Game", command=self.do_nothing)
        self.button_connect.grid(row=0, column=0, sticky=tk.NSEW)
        print("finish_ui_setup")


def on_closing():
    print("Closing")
    os.kill(os.getpid(), signal.SIGTERM)


if __name__ == '__main__':
    '''root = tk.Tk()
    root.resizable(False, False)
    root.geometry("300x300")
    # root.protocol("WM_DELETE_WINDOW", on_closing)

    MainWindow = tk.Frame(root, width=300, height=300)
    MainWindow.pack()'''
    # the workers is like the amount of threads that can be opened at the same time, when there are 10 clients connected
    # then no more clients able to connect to the server.

    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1000))
    rpc.add_ChatServerServicer_to_server(
        Lobby(os.getpid()), server)
    server.add_insecure_port('[::]:' + str(port))
    print('Lobby started1. Listening...')
    server.start()
    print('Lobby started2. Listening...')

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
