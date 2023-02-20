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
        self.myHp = 1
        self.myBlock = 0
        self.myPlayerType = 0
        self.username = u
        self.map = chat.InitialList()
        self.map.length = 0
        self.listHealth = [] # [{"ip": ip, "hp": hp, "block": block, "user": user},{},{},{}]
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
        threading.Thread(target=self.__listen_for_actions, daemon=True).start()
        threading.Thread(target=self.__listen_for_block, daemon=True).start()
        threading.Thread(target=self.__diagnose, daemon=True).start()

        if self.p.user != 'a': # host TODO change this line to be "not the host" (probably easiest when we launch both programs from the same place)
            while self.map.length == 0:
                resp = self.conn.GetActiveMap(chat.Empty())
                if resp.board != "":
                    self.map = resp
                    self.cleanInitialList(self.map)
                    time.sleep(2)

        self.window.mainloop()        

    def __diagnose(self):
        while True:
            print("-------- START DIAGNOSTIC ---------")
            print(self.username," - HP: ", self.myHp," - Block: ", self.myBlock)
            for item in self.listHealth:
                print(item)
            print("-------- END DIAGNOSTIC ---------")
            time.sleep(10)
        
    def __listen_for_pingpong(self):
        while True:
            p = chat.Ping()  # create protobug message (called Ping)
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

            '''print("------")  
            print(health, "HEALTH")'''

            for  utente  in  self.listHealth:
                #if  utente["ip"]  ==  req_ip: 
                if  utente["user"]  ==  health.user:
                    utente["hp"]  =  health.hp
                if utente["user"] == self.username:
                    self.myHp = health.hp
    
    def __listen_for_block(self):
        for block in self.conn.BlockStream(chat.Empty()):
            req_ip = self.fernet.decrypt(block.ip).decode()
            block_amount = block.block
            block_user = block.user

            '''print("------")  
            print(block, "BLOCK")'''

            for utente in self.listHealth:
                 #if  utente["ip"]  ==  req_ip: 
                if  utente["user"]  ==  block_user:
                    utente["block"]  =  block_amount
                #if  utente["ip"]  ==  self.ip == req_ip:
                if utente["user"] == self.username:
                    self.myBlock = block_amount
        


    def __listen_for_actions(self):
        for action in self.conn.ActionStream(chat.Empty()):
            action_ip_sender = self.fernet.decrypt(action.ip_sender).decode()
            action_ip_reciever = self.fernet.decrypt(action.ip_reciever).decode()
            action_amount = action.amount
            action_type = action.action_type
            mode = ""

            match action_type:
                case 0:
                    mode = "attacks"
                case 1:
                    mode = "heals"
                case 2:
                    mode = "blocks"
                case _:
                    mode = "does something" #default

            #print_message = "User "

            for user in self.listHealth: #TODO: find a way to have this work in testing, maybe switch to username based recognition
                if user["ip"] == action_ip_sender:
                    actor = user
                if user["ip"] == action_ip_reciever:
                    victim = user
            
            addendum = (" " + victim["user"]) if action_type != 2 else ""
            #print_message = print_message + actor["user"] +" "+ mode + addendum + " for " + str(abs(action_amount)) + " points!"

            print_message_array = ["User",actor["user"],mode,addendum,"for",str(abs(action_amount)),"points!"]
            print_message = " ".join(print_message_array)

            print("--- MESSAGE ---")
            print(print_message)
            print("--- MESSAGE ---")

            if victim["block"] > 0 and action_type == 0: #if the victim can block an attack he will do that before getting his hp hit
                action_amount = action_amount + int(victim["block"])
                action_amount = 0 if action_amount > 0 else action_amount
                b = chat.Block()
                b.ip =  self.fernet.encrypt(victim["ip"].encode())
                b.block = 0
                b.user = victim["user"]
                self.conn.SendBlock(b)
            
            if action_type < 2:
                m = chat.Health()
                m.ip =  self.fernet.encrypt(victim["ip"].encode())
                m.hp = int(victim["hp"]) + action_amount
                m.user = victim["user"]
                self.conn.SendHealth(m)
            else:
                b = chat.Block()
                b.ip =  self.fernet.encrypt(user["ip"].encode())
                b.block = action_amount
                b.user = user["user"]
                self.conn.SendBlock(b)

    def __listen_for_turns(self):
        time.sleep(0.5) #some wait time before running to ensure that the ui gets created in time 
        for turn in self.conn.TurnStream(chat.Empty()):
            if turn.user == self.username: #for testing use this line
            #if self.fernet.decrypt(turn.ip).decode() == self.ip:   
                print("Mio turno: " + self.username)
                self.turn_button["state"] = "normal"
                #if miei hp <= 0 endturn + interfaccia "you died"
                if self.myHp <= 0:
                    if self.myPlayerType == True:
                        print("THE MONSTER IS DEAD! The game will end shortly.")
                        #end the game right here
                    else:
                        print("YOU ARE DEAD! Wait for one of your allies to revive you.")
                        self.send_end_turn()
                #TODO start the turn 

    #TODO: implement a one action per turn thing

    def send_end_turn(self):
        info = chat.PrivateInfo()
        info.ip = self.fernet.encrypt(self.ip.encode())
        info.user = self.username
        print("Ending my turn: " + self.username)
        self.turn_button["state"] = "disabled"
        '''n = chat.Health()
        n.ip = info.ip
        n.hp = random.randint(-10, 10)
        n.user = self.username
        self.conn.SendHealth(n)'''
        #print(self.listHealth)
        self.conn.EndTurn(info)

    def attack(self):
        # attack people that are not your same class or friends 
        for user in self.listHealth:
            if user["player_type"] != self.myPlayerType: #i can attack my enemies only
                n = chat.Action()
                n.ip_sender = self.fernet.encrypt(self.ip.encode())
                n.ip_reciever = self.fernet.encrypt(user["ip"].encode())
                n.action_type = 0
                n.amount = -10 + random.randint(-5,5) #TODO range of damage
                self.conn.SendAction(n)
    
    def heal(self):
        for user in self.listHealth:
            if user["player_type"] == self.myPlayerType: #i will heal my friends only
                h = chat.Action()
                h.ip_sender = self.fernet.encrypt(self.ip.encode())
                h.ip_reciever = self.fernet.encrypt(user["ip"].encode())
                h.action_type = 1
                h.amount = 8 + random.randint(-5,5) #TODO range of damage
                self.conn.SendAction(h)
    
    def block(self):
        for user in self.listHealth:
            if user["user"] == self.username: #i will block for myself only
                b = chat.Action()
                b.ip_sender = self.fernet.encrypt(self.ip.encode())
                b.ip_reciever = self.fernet.encrypt(user["ip"].encode())
                b.action_type = 2
                b.amount = 10 #TODO range of damage
                self.conn.SendAction(b)



    def cleanInitialList(self, mess):
        string = mess.board
        rows = string.split("][")  # split the string by the '][' delimiter
        array = []
        for row in rows:
            #print(row, " ROW")
            row = row.strip("[]")  # remove the square brackets from the row string
            values = [str(x).strip().strip("'") for x in row.split(",")]  # split the row string by the ',' delimiter and convert the values to integers
            array.append(values)
         
        array_ip = mess.ip.strip("[]").strip("''").split(",") #["enc_ip","enc_ip"]
        array_role = mess.player_type.strip("[]").strip().strip("''").split(",") #[T,F,T]

        self.listHealth.extend([{"ip":array_ip[i].strip().strip("'"), "hp":array[1][i], "block": 0,
                                  "user":array[0][i], "player_type": int(array_role[i].strip())} for i in range(0,len(array[0]))])
        self.genMyRole()
        #print(self.listHealth)

    def genMyRole(self):
        for user in self.listHealth:
            if user["user"] == self.username: #TODO change to ip
                self.myPlayerType = user["player_type"]

    def send_message(self, event):
        """
        This method is called when user enters something into the textbox
        """
        message = self.entry_message.get()  # retrieve message from the UI
        if message != '':
            if message == '1': # fake starting
                mess = self.conn.StartGame(self.p)
                self.cleanInitialList(mess)
            
            n = chat.Note()  # create protobug message (called Note)
            n.name = self.username  # set the username
            n.message = message  # set the actual message of the note
            #print("S[{}] {}".format(n.name, n.message))  # debugging statement
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
        self.attack_button = Button(self.window, text = "ATTACK!", command = self.attack)
        self.attack_button.pack()
        self.heal_button = Button(self.window, text = "HEAL!", command = self.heal)
        self.heal_button.pack()
        self.block_button = Button(self.window, text = "BLOCK!", command = self.block)
        self.block_button.pack()
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