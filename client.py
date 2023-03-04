import threading
import os
from PIL import ImageTk, Image 

from GRPCClientHelper import helper

import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk

import time
import random
import re
from cryptography.fernet import Fernet


key = b'ZhDach4lH7NbH-Gy9EfN2e2HNrWRfbBFD8zeCTBgdEA='

pg_type = ["knight", "mage", "archer", "monster"]
cancel_id = None
aniThreadPointer = []
class Client:

    def __init__(self, user: str, serverAddress: str, window):
        # the frame to put ui components on
        self.GAME_STARTED = False
        self.window = window
        self.myHp = 99.9
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
            self.entry_message.config(text=print_message)
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
        #self.__after_action()

    def attack(self):
        # attack people that are not your same class or friends 
        self.lockButtons()
        self.state="attack"
        #self.__after_action()
        for user in self.listHealth:
            if user["player_type"] != self.myPlayerType: #i can attack my enemies only
                self.myPostOffice.SendAction(user["ip"], actionType = 0)

    def heal(self):
        self.lockButtons()
        self.state="protect"
        #self.__after_action()
        for user in self.listHealth:
            if user["player_type"] == self.myPlayerType: #i will heal my friends only
                self.myPostOffice.SendAction(user["ip"], actionType = 1)

    def block(self):
        self.state="protect"
        #self.__after_action()
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
            self.imgs.append(ImageTk.PhotoImage(file=path+i))
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
            ms_delay = 250 #1000// len(self.imgs)  # Show all frames in 1000 ms.
            cancel_id = root.after(
            ms_delay, self.update_label_image, animation, self.imgs, ms_delay, 0)
    
    def enable_animation_thread(self, animation):
        global cancel_id
        global aniThreadPointer
        if cancel_id is None:
            t = threading.Thread(target=self.enable_animation, args=(animation,),daemon=True) #create thread
            t.start()
            aniThreadPointer.append(t)

    def cancel_animation(self):
        global cancel_id
        global aniThreadPointer
        if cancel_id is not None:  # Animation started?
            self.window.after_cancel(cancel_id)
            while aniThreadPointer != []:   #kill all threads     
                ttmp = aniThreadPointer.pop()
                ttmp.join()
            cancel_id = None


    def __setup_ui(self):
        #self.window.resizable(False,False)
        self.master_frame = tk.Frame(self.window)
        self.master_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.master_frame.columnconfigure(0, weight=1, minsize=960) #16:10
        self.master_frame.rowconfigure(0, weight=1, minsize=420)
        self.master_frame.rowconfigure(1, weight=1, minsize=180)

        self.background_frame = tk.Frame(self.master_frame, borderwidth=1)
        self.background_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.background_frame.columnconfigure([0, 1], weight=1, minsize=480)
        self.background_frame.rowconfigure(0, weight=1, minsize=420)

        # HEROES SETUP
        self.heroes_frame = tk.Frame(self.background_frame, borderwidth=1, bg="brown", padx=10, pady=10)
        self.heroes_frame.grid(row=0, column=0, sticky=tk.NSEW)

        for i in range(2):
            self.heroes_frame.columnconfigure(i, weight=1)
        for j in range(3):
            self.heroes_frame.rowconfigure(j, weight=1)

        self.loadImgs()
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background='green')

        self.hero1 = tk.Label(self.heroes_frame, image=self.imgs[0])
        self.hero1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        #@self.enable_animation_thread(self.label1)
        self.hero1_username = tk.Label(self.heroes_frame, text=self.username)
        self.hero1_username.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)
        hero1_health = ttk.Progressbar(self.heroes_frame, style="Horizontal.TProgressbar", orient='horizontal', variable=self.myHp, mode='determinate')
        hero1_health.step(99.9)
        hero1_health.grid(row=0, column=0, padx=5, pady=5, sticky=tk.S)

        ''' at this point we need to declare different labels and we can even fill them later when other people join but for right now as a proof of concept i'll use the knight'''
        self.hero2 = tk.Label(self.heroes_frame, image=self.imgs[0])
        self.hero2.grid(row=2, column=0, padx=5, pady=5, sticky=tk.NSEW)
        #self.enable_animation_thread(self.label2)
        self.hero2_username = tk.Label(self.heroes_frame, text=self.username)
        self.hero2_username.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N)
        hero2_health = ttk.Progressbar(self.heroes_frame, orient='horizontal', variable=self.myHp, mode='determinate')
        hero2_health.step(99.9)
        hero2_health.grid(row=2, column=0, padx=5, pady=5, sticky=tk.S)

        self.hero3 = tk.Label(self.heroes_frame, image=self.imgs[0])
        self.hero3.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        #self.enable_animation_thread(self.label3)
        self.hero3_username = tk.Label(self.heroes_frame, text=self.username)
        self.hero3_username.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        hero3_health = ttk.Progressbar(self.heroes_frame, orient='horizontal', variable=self.myHp, mode='determinate')
        hero3_health.step(99.9)
        hero3_health.grid(row=1, column=1, padx=5, pady=5, sticky=tk.S)

        # MONSTER SETUP
        self.monster_frame = tk.Frame(self.background_frame, borderwidth=1, bg="orange", padx=5, pady=5)
        self.monster_frame.grid(row=0, column=1, sticky=tk.NSEW)
                
        image = Image.open("./src/monster/1.png")
        photo = ImageTk.PhotoImage(image)
        
        self.monster = tk.Label(self.monster_frame, image=photo)
        self.monster.image = photo # keep a reference!
        self.monster.pack()
        self.monster_label = tk.Label(self.monster_frame, text="PDOR FIGLIO DI KMER")
        self.monster_label.pack()

        self.controls_frame = tk.Frame(self.master_frame, borderwidth=1)
        self.controls_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self.controls_frame.columnconfigure(0, weight=1, minsize=288)
        self.controls_frame.columnconfigure(1, weight=2, minsize=672) 
        self.controls_frame.rowconfigure(0, weight=1, minsize=180)

        # BUTTONS SETUP
        self.buttons_frame = tk.Frame(self.controls_frame, borderwidth=1, bg="yellow")
        self.buttons_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.buttons_frame.columnconfigure([0, 1], weight=1, minsize=144)
        self.buttons_frame.rowconfigure([0, 1], weight=1, minsize=90)

        self.attack_button = tk.Button(self.buttons_frame, text = "ATTACK", command = self.attack)
        self.attack_button.grid(row=0, column=0, sticky=tk.NSEW)
        self.heal_button = tk.Button(self.buttons_frame, text = "HEAL", command = self.heal)
        self.heal_button.grid(row=0, column=1, sticky=tk.NSEW)
        self.block_button = tk.Button(self.buttons_frame, text = "BLOCK", command = self.block)
        self.block_button.grid(row=1, column=0, sticky=tk.NSEW)
        self.turn_button = tk.Button(self.buttons_frame, text = "END TURN", command = self.send_end_turn)
        self.turn_button.grid(row=1, column=1, sticky=tk.NSEW)
        self.turn_button["state"] = "disabled"
        self.lockButtons()

        # TEXT MESSAGE SETUP
        self.text_frame = tk.Frame(master=self.controls_frame, borderwidth=1, bg="blue")
        self.text_frame.grid(row=0, column=1, sticky=tk.SE)
        self.text_frame.columnconfigure(0, weight=1, minsize=672)
        self.text_frame.rowconfigure(0, weight=1, minsize=180)

        self.entry_message = tk.Label(self.text_frame, bd=5)
        #self.entry_message.bind('<Return>', self.send_message)
        #self.entry_message.focus()
        self.entry_message.config(text="Welcome to the game!")
        self.entry_message.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        self.start_button = tk.Button(self.monster_frame, text = "Start Game", command = self.send_start_game)
        self.start_button.pack()
    
    def __after_action(self):
        self.loadImgs()
        self.cancel_animation()
        self.enable_animation_thread(self.label1)
        self.enable_animation_thread(self.label2)
        self.enable_animation_thread(self.label3)


if __name__ == '__main__':
    root = tk.Tk()
    root.resizable(False,False)
    root.title("RPGCombat")
    root.iconbitmap("./src/icon/icon.ico")
    frame = tk.Frame(root, width=300, height=300)
    frame.pack()
    root.withdraw() # Hides the window
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
        
    root.deiconify()  # Makes the window visible again
    c = Client(username, serverAddress, frame)  # this starts a client and thus a thread which keeps connection to server open