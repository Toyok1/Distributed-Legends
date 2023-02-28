import threading
import os
from PIL import ImageTk, Image 

from GRPCClientHelper import helper

from tkinter import *
from tkinter import simpledialog

import time
import random
import re
from cryptography.fernet import Fernet


key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='

pg_type = ["knight", "mage", "archer", "monster"]
cancel_id = None
class Client:

    def __init__(self, user: str, serverAddress: str, window):
        # the frame to put ui components on
        self.GAME_STARTED = False
        self.window = window
        self.myHp = 1
        self.myBlock = 0
        self.myPlayerType = 0
        self.username = user
        self.listHealth = [] # [{"ip": ip, "hp": hp, "block": block, "user": user},{},{},{}]
        self.myTurn = False
        self.state = "idle"
        
        self.fernet = Fernet(key)
        
        self.myPostOffice = helper.PostOffice(serverAddress)
        self.myPostOffice.Subscribe(user)
        
        try:
            threading.Thread(target=self.myPostOffice.Listen_for_PingPong, daemon=True).start()        
        except:
            self.CloseGame()
        
        self.__setup_ui()

        threading.Thread(target=self.__listen_for_turns, daemon=True).start()
        threading.Thread(target=self.__listen_for_health, daemon=True).start()
        threading.Thread(target=self.__listen_for_actions, daemon=True).start()
        threading.Thread(target=self.__listen_for_block, daemon=True).start()
        threading.Thread(target=self.__diagnose, daemon=True).start()

        #probably the host won't need to run this thread so TODO when we have a way to distinguish them: get rid of it for the host.
        threading.Thread(target=self.__check_for_start, daemon = True).start()

        '''
        if self.p.user != 'a': # host TODO change this line
            while self.map.length == 0:
                self.map = self.conn.GetActiveMap(chat.Empty())
                time.sleep(2)
                print(self.map)
                '''
        self.window.mainloop()

    def __check_for_start(self):
        while not self.GAME_STARTED:
            b = self.myPostOffice.CheckStarted()
            self.GAME_STARTED = b.started
        #self.map = self.conn.GetActiveMap(chat.Empty())
        if self.listHealth == []:
            mess = self.myPostOffice.GetInitialList()
            self.cleanInitialList(mess)
        self.start_button["state"] = "disabled"


    def __diagnose(self):
        while True:
            print("-------- START DIAGNOSTIC ---------")
            print(self.username," - HP: ", self.myHp," - Block: ", self.myBlock)
            for item in self.listHealth:
                print(item)
            print("-------- END DIAGNOSTIC ---------")
            time.sleep(10)
        
    def __listen_for_health(self):
        """
        This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
        when waiting for new messages
        """
        for health in self.myPostOffice.HealthStream(): # this line will wait for new messages from the server!
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
        for block in self.myPostOffice.BlockStream():
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
        for action in self.myPostOffice.ActionStream():
            action_ip_sender = self.fernet.decrypt(action.ip_sender).decode()
            action_ip_reciever = self.fernet.decrypt(action.ip_reciever).decode()
            action_amount = action.amount
            action_type = action.action_type
            mode = ""

            match action_type:
                case 0:
                    mode = "attack"
                case 1:
                    mode = "heal"
                case 2:
                    mode = "block"
                case _:
                    mode = "idle" #default

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
            self.state = mode
            print("--- MESSAGE ---")
            print(print_message)
            print("--- MESSAGE ---")
            print(self.state)

            if victim["block"] > 0 and action_type == 0: #if the victim can block an attack he will do that before getting his hp hit
                action_amount = action_amount + int(victim["block"])
                action_amount = 0 if action_amount > 0 else action_amount
                self.myPostOffice.SendBlock(actionType = 0, victimUser = victim["user"], victimIp = victim["ip"])
            
            if action_type < 2:
                self.myPostOffice.SendHealth(victimUser = victim["user"], victimIp = victim["ip"], victimHp = victim["hp"], action_amount = action_amount)
            else:
                self.myPostOffice.SendBlock(actionType = 1, victimUser = victim["user"], victimIp = victim["ip"], action_amount = action_amount)

    def __listen_for_turns(self):
        time.sleep(0.5) #some wait time before running to ensure that the ui gets created in time 
        for turn in self.myPostOffice.TurnStream():
            if turn.user == self.username: #for testing use this line
            #if self.fernet.decrypt(turn.ip).decode() == self.ip:   
                print("Mio turno: " + self.username)
                self.turn_button["state"] = "normal"
                self.unlockButtons() #unlock the buttons when it's my turn
                #if miei hp <= 0 endturn + interfaccia "you died"
                if self.myHp <= 0:
                    if self.myPlayerType == True:
                        print("THE MONSTER IS DEAD! The game will end shortly.")
                        #end the game right here
                    else:
                        print("YOU ARE DEAD! Wait for one of your allies to revive you.")
                        self.send_end_turn()
                #TODO start the turn 

    def closeGame(self):
        # TODO end game
        pass

    #TODO: implement a one action per turn thing

    def lockButtons(self):
        self.attack_button["state"] = "disabled"
        self.heal_button["state"] = "disabled"
        self.block_button["state"] = "disabled"
    
    def unlockButtons(self):
        self.attack_button["state"] = "normal"
        self.heal_button["state"] = "normal"
        self.block_button["state"] = "normal"

    def send_end_turn(self):
        print("Ending my turn: " + self.username)
        self.turn_button["state"] = "disabled"
        '''n = chat.Health()
        n.ip = info.ip
        n.hp = random.randint(-10, 10)
        n.user = self.username
        self.conn.SendHealth(n)'''
        #print(self.listHealth)
        #self.lockButtons()
        self.state = "idle"
        self.myPostOffice.EndTurn()
        self.__after_action()

    def attack(self):
        # attack people that are not your same class or friends 
        self.lockButtons()
        self.state="attack"
        self.__after_action()
        for user in self.listHealth:
            if user["player_type"] != self.myPlayerType: #i can attack my enemies only
                self.myPostOffice.SendAction(user["ip"], actionType = 0)

    def heal(self):
        self.lockButtons()
        self.state="protect"
        self.__after_action()
        for user in self.listHealth:
            if user["player_type"] == self.myPlayerType: #i will heal my friends only
                self.myPostOffice.SendAction(user["ip"], actionType = 1)

    def block(self):
        self.state="protect"
        self.__after_action()
        self.lockButtons()
        for user in self.listHealth:
            if user["user"] == self.username: #i will block for myself only
                self.myPostOffice.SendAction(user["ip"], actionType = 2)


    def cleanInitialList(self, mess):
        string = mess.name_hp
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
    
    def send_start_game(self):
        #if i'm the user i can start the game  TODO: make it so that only hosts can use this button and maybe delete it after use (?)
        mess = self.myPostOffice.StartGame()
        self.cleanInitialList(mess)

    '''def send_message(self, event):
        """
        This method is called when user enters something into the textbox
        """
        message = self.entry_message.get()  # retrieve message from the UI
        if message != '':
            if message == '1': # fake starting'''
                

    def loadImgs(self):
        global pg_type
        self.imgs = []
        path = "src/"+pg_type[0]+"/"+self.state+"/"
        for i in os.listdir(path):
            self.imgs.append(PhotoImage(file=path+i))
    '''
    def animate(self, label):
        global pg_type
        path = "src/"+pg_type[0]+"/"+self.state+"/"
        i=0
        while True:   
            label.configure(image=self.imgs[i])
            label.update()
            time.sleep(0.2)
            i+=1
            if i == len(os.listdir(path))-1:
                i = 0
    '''    
    def update_label_image(self, label, ani_img, ms_delay, frame_num):
        global cancel_id
        label.configure(image=ani_img[frame_num])
        frame_num = (frame_num+1) % len(ani_img)
        cancel_id = root.after(
            ms_delay, self.update_label_image, label, ani_img, ms_delay, frame_num)
        

    def enable_animation(self, animation):
        global cancel_id
        if cancel_id is None:  # Animation not started?
            ms_delay = 500 #1000// len(self.imgs)  # Show all frames in 1000 ms.
            cancel_id = root.after(
            ms_delay, self.update_label_image, animation, self.imgs, ms_delay, 0)

    def cancel_animation(self):
        global cancel_id
        if cancel_id is not None:  # Animation started?
            self.window.after_cancel(cancel_id)
            cancel_id = None

    def __setup_ui(self):
        self.frame = Frame(self.window)
        self.frame.pack(side=BOTTOM)
        self.loadImgs()
        self.label = Label(self.frame, image=self.imgs[0])
        self.label.pack(side=LEFT)
        self.enable_animation(self.label)

        self.lbl_username = Label(self.window, text=self.username)
        self.lbl_username.pack(side=LEFT)
        '''self.entry_message = Entry(self.window, bd=5)
        self.entry_message.bind('<Return>', self.send_message)
        self.entry_message.focus()
        self.entry_message.pack(side=BOTTOM)'''
        self.start_button = Button(self.window, text = "Start Game", command = self.send_start_game)
        self.start_button.pack()
        self.turn_button = Button(self.window, text = "End Turn", command = self.send_end_turn)
        self.turn_button.pack()
        self.attack_button = Button(self.window, text = "ATTACK", command = self.attack)
        self.attack_button.pack()
        self.heal_button = Button(self.window, text = "HEAL", command = self.heal)
        self.heal_button.pack()
        self.block_button = Button(self.window, text = "BLOCK", command = self.block)
        self.block_button.pack()
        self.turn_button["state"] = "disabled"
        self.lockButtons()
    
    def __after_action(self):
        global pg_type
        self.imgs = []
        print("STATEEEEE--------->" + self.state)
        path = "src/"+pg_type[0]+"/"+self.state+"/"
        for i in os.listdir(path):
            self.imgs.append(PhotoImage(file=path+i))
        self.cancel_animation()
        self.enable_animation(self.label)


if __name__ == '__main__':
    root = Tk()  # I just used a very simple Tk window for the chat UI, this can be replaced by anything
    frame = Frame(root, width=300, height=300)
    frame.pack()
    root.withdraw()
    username = None
    serverAddress = "localhost" #None when we deploy but for testing localhost is fine
    while username is None:
        # retrieve a username so we can distinguish all the different clients
        username = simpledialog.askstring("Username", "What's your username?", parent=root)
    #address = "localhost" #None
    while (serverAddress != "localhost") or (serverAddress is None) :
        # retrieve a username so we can distinguish all the different clients
        serverAddress = simpledialog.askstring("Game's address", "What's the address?", parent=root)
        if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", serverAddress):
            break
        
    root.deiconify()  # don't remember why this was needed anymore...
    c = Client(username, serverAddress, frame)  # this starts a client and thus a thread which keeps connection to server open