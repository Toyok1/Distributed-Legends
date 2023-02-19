import threading

from tkinter import *
from tkinter import simpledialog

import grpc
import time
import random

import chat_pb2 as chat
import chat_pb2_grpc as rpc

from requests import get
from cryptography.fernet import Fernet

#address = 'localhost'
port = 11912 # decide if we have to change this port
key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='

class Client:

    def __init__(self, u: str, a: str, window):
        # the frame to put ui components on
        self.window = window
        self.username = u
        self.map = chat.Map()
        self.map.length = 0
        self.listHealth = []
        #self.map.length = 0
        self.myTurn = False

        self.ip = get('https://api.ipify.org').content.decode('utf8')
        self.fernet = Fernet(key)
        encMessage = self.fernet.encrypt(self.ip.encode())
        
        # create a gRPC channel + stub
        channel = grpc.insecure_channel(a + ':' + str(port))
        self.conn = rpc.ChatServerStub(channel)

        threading.Thread(target=self.__listen_for_pingpong, daemon=True).start()
        
           
        self.p = chat.PrivateInfo()  # create protobug message (called Note)
        self.p.ip = encMessage
        self.p.user = u
        self.conn.SendPrivateInfo(self.p)  # send the Note to the server
        self.__setup_ui()

        threading.Thread(target=self.__listen_for_turns, daemon=True).start()
        threading.Thread(target=self.__listen_for_health, daemon=True).start()

        if self.p.user != 'a': # host TODO change this line to be "not the host" (probably easiest when we launch both programs from the same place)
            while self.map.length == 0:
                resp = self.conn.GetActiveMap(chat.Empty())
                if resp.board != "":
                    self.map = resp
                    self.cleanMap(self.map)
                    time.sleep(2)

        self.window.mainloop()
        
        
    def __listen_for_pingpong(self):
        while True:
            p = chat.Ping()  # create protobug message (called Note)
            p.ip = self.fernet.encrypt(self.ip.encode())
            pong = self.conn.SendPing(p)
            time.sleep(5)
            #pong.message None chiudi gioco


    def __listen_for_health(self):
        """
        This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
        when waiting for new messages
        """
        for health in self.conn.HealthStream(chat.Empty()): # this line will wait for new messages from the server!
            req_ip = self.fernet.decrypt(health.ip).decode()  
            print("R[{}] {}".format(health.user, health.hp)) 
            for  utente  in  self.listHealth:
                #if  utente["ip"]  ==  req_ip: 
                if  utente["name"]  ==  health.user:
                    utente["hp"]  =  health.hp

    def __listen_for_turns(self):
        time.sleep(0.5) #some wait time before running to ensure that the ui gets created in time 
        for turn in self.conn.TurnStream(chat.Empty()):
            if turn.user == self.username: #for testing use this line
            #if self.fernet.decrypt(turn.ip).decode() == self.ip:   
                print("Mio turno: " + self.username)
                self.turn_button["state"] = "normal"
                #TODO start the turn

    def send_end_turn(self):
        info = chat.PrivateInfo()
        info.ip = self.fernet.encrypt(self.ip.encode())
        info.user = self.username
        print("Ending my turn: " + self.username)
        self.turn_button["state"] = "disabled"
        n = chat.Health()
        n.ip = info.ip
        n.hp = random.randint(0, 100)
        n.user = self.username
        self.conn.SendHealth(n)
        print(self.listHealth)
        self.conn.EndTurn(info)

    def cleanMap(self, mess):
        string = mess.board
        rows = string.split("][")  # split the string by the '][' delimiter
        array = []
        for row in rows:
            row = row.strip("[]")  # remove the square brackets from the row string
            values = [str(x) for x in row.split(",")]  # split the row string by the ',' delimiter and convert the values to integers
            array.append(values)
            
        self.listHealth.extend([{"ip":self.ip, "hp":array[1][i], "user":array[0][i]} for i in range(0,len(array[0]))])

    def send_message(self, event):
        """
        This method is called when user enters something into the textbox
        """
        message = self.entry_message.get()  # retrieve message from the UI
        if message != '':
            if message == '1': # fake starting
                mess = self.conn.StartGame(self.p)
                self.cleanMap(mess)
            
            n = chat.Note()  # create protobug message (called Note)
            n.name = self.username  # set the username
            n.message = message  # set the actual message of the note
            print("S[{}] {}".format(n.name, n.message))  # debugging statement
            self.conn.SendNote(n)  # send the Note to the server

    def __setup_ui(self):
        self.chat_list = Text()
        self.chat_list.pack(side=TOP)
        self.lbl_username = Label(self.window, text=self.username)
        self.lbl_username.pack(side=LEFT)
        self.entry_message = Entry(self.window, bd=5)
        self.entry_message.bind('<Return>', self.send_message)
        self.entry_message.focus()
        self.entry_message.pack(side=BOTTOM)
        self.turn_button = Button(self.window, text = "End Turn", command = self.send_end_turn)
        self.turn_button.pack()
        self.turn_button["state"] = "disabled"


if __name__ == '__main__':
    root = Tk()  # I just used a very simple Tk window for the chat UI, this can be replaced by anything
    frame = Frame(root, width=300, height=300)
    frame.pack()
    root.withdraw()
    username = None
    while username is None:
        # retrieve a username so we can distinguish all the different clients
        username = simpledialog.askstring("Username", "What's your username?", parent=root)
    address = "localhost" #None
    #while address is None:
        # retrieve a username so we can distinguish all the different clients
    #    address = simpledialog.askstring("Game's address", "What's the address?", parent=root)
    root.deiconify()  # don't remember why this was needed anymore...
    c = Client(username, address, frame)  # this starts a client and thus a thread which keeps connection to server open