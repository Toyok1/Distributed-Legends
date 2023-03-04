import threading
import os
from PIL import ImageTk, Image 

from GRPCClientHelper import helper, player

import tkinter as tk
from tkinter import simpledialog

import time
import uuid
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
        self.myPlayer = None #quick reference to my player
        self.otherPlayers = [] #quick reference to everyone but me
        self.players = [] #quick refernce to every player in the game
        self.window = window
        self.myHp = 1
        self.myBlock = 0
        self.myPlayerType = 0
        self.username = user
        #self.listHealth = [] # [{"ip": ip, "hp": hp, "block": block, "user": user},{},{},{}]
        self.myTurn = False
        self.state = "idle"
        self.myUid = str(uuid.uuid4())
        
        self.fernet = Fernet(key)
        
        self.myPostOffice = helper.PostOffice(serverAddress, user, self.myUid)
        self.myPostOffice.Subscribe()
        
        try:
            threading.Thread(target=self.myPostOffice.Listen_for_PingPong, args=(self.myUid,), daemon=True).start()        
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
        if self.players == []:
            mess = self.myPostOffice.GetInitialList()
            self.cleanInitialList(mess)
        self.start_button["state"] = "disabled"


    def __diagnose(self):
        while True:
            if self.myPlayer != None:
                print("-------- START DIAGNOSTIC ---------")
                print(self.myPlayer.getUsername()," - HP: ", self.myPlayer.getHp()," - Block: ", self.myPlayer.getBlock())
                for item in self.players:
                    print(item)
                print("-------- END DIAGNOSTIC ---------")
            time.sleep(10)
        
    def __listen_for_health(self):
        """
        This method will be ran in a separate thread as the main/ui thread, because the for-in call is blocking
        when waiting for new messages
        """
        for health in self.myPostOffice.HealthStream(): # this line will wait for new messages from the server!
            healed = player.transformFromJSON(health.json_str)
            health_amount = health.hp
            '''print("------")  
            print(health, "HEALTH")'''

            for  utente in self.players:
                #if  utente["ip"]  ==  req_ip: 
                if utente.getUid() == healed.getUid():
                    utente.setHp(health_amount)
                '''if utente["user"] == self.username:
                    self.myHp = health.hp'''
    
    def __listen_for_block(self):
        for block in self.myPostOffice.BlockStream():
            blocker = player.transformFromJSON(block.json_str)
            block_amount = block.block

            '''print("------")  
            print(block, "BLOCK")'''

            for utente in self.players:
                #if  utente["ip"]  ==  req_ip: 
                if  utente.getUid()  ==  blocker.getUid(): #TODO change it to ip when not testing
                    utente.setBlock(block_amount)
                #if  utente["ip"]  ==  self.ip == req_ip:
                '''if utente["user"] == self.username:
                    self.myBlock = block_amount'''
        


    def __listen_for_actions(self):
        for action in self.myPostOffice.ActionStream():
            action_sender = player.transformFromJSON(action.sender)
            action_reciever = player.transformFromJSON(action.reciever)
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

            for user in self.players: #TODO: find a way to have this work in testing, maybe switch to username based recognition
                if user.getUid() == action_sender.getUid(): #uid for testing TODO change it to ip
                    actor = user
                if user.getUid() == action_reciever.getUid():
                    victim = user
            
            addendum = (victim.getUsername()) if action_type != 2 else ""
            #print_message = print_message + actor["user"] +" "+ mode + addendum + " for " + str(abs(action_amount)) + " points!"

            print_message_array = ["User",actor.getUsername(),mode,addendum,"for",str(abs(action_amount)),"points!"]
            print_message = " ".join(print_message_array)
            self.entry_message.config(text=print_message)
            self.state = mode
            print("--- MESSAGE ---")
            print(print_message)
            print("--- MESSAGE ---")
            print(self.state)

            if victim.getBlock() > 0 and action_type == 0: #if the victim can block an attack he will do that before getting his hp hit
                action_amount = action_amount + int(victim.getBlock())
                action_amount = 0 if action_amount > 0 else action_amount
                self.myPostOffice.SendBlock(user=victim, amount= action_amount)
            
            if action_type < 2:
                action_amount = victim.getHp() + action_amount
                self.myPostOffice.SendHealth(user=victim, amount= action_amount)
            else:
                self.myPostOffice.SendBlock(user=victim, amount= action_amount)

    def __listen_for_turns(self): 
        #print("TURNSSSSSSSSSSSSSSSSSSSSSS")
        while self.myPlayer is None:
            pass
        for turn in self.myPostOffice.TurnStream():
            what = player.transformFromJSON(turn.json_str)
            #print(what)
            if what.getUsername() == self.myPlayer.getUsername() and what.getUid() == self.myPlayer.getUid(): #for testing use this line
            #if self.fernet.decrypt(turn.ip).decode() == self.ip:   
                print("Mio turno: " + self.myPlayer.getUsername())
                self.turn_button["state"] = "normal"
                self.unlockButtons() #unlock the buttons when it's my turn
                #if miei hp <= 0 endturn + interfaccia "you died"
                if self.myPlayer.getHp() <= 0:
                    if self.myPlayer.getUsertype() == 1: #monster
                        print("THE MONSTER IS DEAD! The game will end shortly.")
                        #end the game right here
                    else:
                        print("YOU ARE DEAD! Wait for one of your allies to revive you.")
                        self.send_end_turn()

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
        print("MYPLAYER INSIDE SEND_END_TURN", self.myPlayer)
        self.myPostOffice.EndTurn(self.myPlayer)
        #self.__after_action()

    def attack(self):
        # attack people that are not your same class or friends 
        self.lockButtons()
        self.state="attack"
        #self.__after_action()
        for user in self.players:
            if user.getUsertype() != self.myPlayerType: #i can attack my enemies only
                self.myPostOffice.SendAction(self.myPlayer, user, actionType = 0)

    def heal(self):
        self.lockButtons()
        self.state="protect"
        #self.__after_action()
        for user in self.players:
            if user.getUsertype() == self.myPlayerType: #i will heal my friends only
                self.myPostOffice.SendAction(self.myPlayer, user, actionType = 1)

    def block(self):
        self.state="protect"
        #self.__after_action()
        self.lockButtons()
        for user in self.players:
            if user.getUsername() == self.myPlayer.getUsername(): #i will block for myself only
                self.myPostOffice.SendAction(self.myPlayer, user, actionType = 2)


    def cleanInitialList(self, mess):
        '''string = mess.name_hp
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
        #print(self.listHealth)'''
        print(mess)
        self.players = player.transformFullListFromJSON(mess.json_str)
        print(self.players)
        for u in self.players:
            if u.getUsername() == self.username:
                self.myPlayer = u
                self.myPlayerType = u.getUsertype()
            else:
                self.otherPlayers.append(u)

        '''if self.players[-1].getUid() == self.myPlayer.getUid():
            self.send_end_turn()'''

    '''def genMyRole(self):
        for user in self.listHealth:
            if user["user"] == self.username: #TODO change to ip
                self.myPlayerType = user["player_type"]'''
    
    def send_start_game(self):
        #if i'm the host i can start the game  TODO: make it so that only hosts can use this button and maybe delete it after use (?)
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
        self.master_frame.pack(side=tk.BOTTOM)
        self.master_frame.columnconfigure(0, weight=1, minsize=960) #16:10
        self.master_frame.rowconfigure(0, weight=1, minsize=420)
        self.master_frame.rowconfigure(1, weight=1, minsize=180)

        self.background_frame = tk.Frame(master=self.master_frame, borderwidth=1, bg="red", padx=0, pady=0)
        self.background_frame.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)

        self.background_frame.columnconfigure(0, weight=1, minsize=480)
        self.background_frame.columnconfigure(1, weight=1, minsize=480) 
        self.background_frame.rowconfigure(0, weight=1, minsize=420)

        self.heroes_frame = tk.Frame(master=self.background_frame, borderwidth=1, bg="green", padx=5, pady=5)
        self.heroes_frame.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.monster_frame = tk.Frame(master=self.background_frame, borderwidth=1, bg="orange", padx=5, pady=5)
        self.monster_frame.grid(row=0, column=1, padx=0, pady=0, sticky=tk.NSEW)

        self.controls_frame = tk.Frame(master=self.master_frame, borderwidth=1, padx=0, pady=0)
        self.controls_frame.grid(row=1, column=0, padx=0, pady=0, sticky=tk.NSEW)

        self.controls_frame.columnconfigure(0, weight=1, minsize=288)
        self.controls_frame.columnconfigure(1, weight=2, minsize=672) 
        self.controls_frame.rowconfigure(0, weight=1, minsize=180)
        
        self.buttons_frame = tk.Frame(master=self.controls_frame, borderwidth=1, bg="yellow", padx=0, pady=0)
        self.buttons_frame.grid(row=0, column=0, padx=0, pady=0, sticky=tk.SW)
        self.text_frame = tk.Frame(master=self.controls_frame, borderwidth=1, bg="blue", padx=0, pady=0)
        self.text_frame.grid(row=0, column=1, padx=0, pady=0, sticky=tk.SE)

        #for x,y in range(2),range(3):
        self.heroes_frame.columnconfigure(0, weight=1)
        self.heroes_frame.columnconfigure(1, weight=1)
        self.heroes_frame.rowconfigure(0, weight=1)
        self.heroes_frame.rowconfigure(1, weight=1)
        self.heroes_frame.rowconfigure(2, weight=1)

        self.hero1_frame = tk.Frame(master=self.heroes_frame, borderwidth=1, padx=5, pady=5,bg="green")
        self.hero2_frame = tk.Frame(master=self.heroes_frame, borderwidth=1, padx=5, pady=5,bg="green")
        self.hero3_frame = tk.Frame(master=self.heroes_frame, borderwidth=1, padx=5, pady=5,bg="green")
        self.hero1_frame.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.hero2_frame.grid(row=1, column=1, padx=0, pady=0, sticky=tk.NSEW)
        self.hero3_frame.grid(row=2, column=0, padx=0, pady=0, sticky=tk.NSEW)

        self.loadImgs()
        self.label1 = tk.Label(self.hero1_frame, image=self.imgs[0])
        self.label1.pack()
        #@self.enable_animation_thread(self.label1)

        self.lbl_username1 = tk.Label(self.hero1_frame, text=self.username)
        self.lbl_username1.pack()

        ''' at this point we need to declare different labels and we can even fill them later when other people join but for right now as a proof of concept i'll use the knight'''
        self.label2 = tk.Label(self.hero2_frame, image=self.imgs[0])
        self.label2.pack()
        #self.enable_animation_thread(self.label2)

        self.lbl_username2 = tk.Label(self.hero2_frame, text=self.username)
        self.lbl_username2.pack()

        self.label3 = tk.Label(self.hero3_frame, image=self.imgs[0])
        self.label3.pack()
        #self.enable_animation_thread(self.label3)

        self.lbl_username3 = tk.Label(self.hero3_frame, text=self.username)
        self.lbl_username3.pack()

        
        image = Image.open("./src/monster/1.png")
        photo = ImageTk.PhotoImage(image)
        
        self.label4 = tk.Label(self.monster_frame, image=photo)
        self.label4.image = photo # keep a reference!
        self.label4.pack()

        '''self.label4 = tk.Label(self.monster_frame, image=ph)
        
        self.label4.pack()
        #self.label4.image=ph'''
        
        self.lbl_username4 = tk.Label(self.monster_frame, text="PDOR FIGLIO DI KMER")
        self.lbl_username4.pack()

        self.text_frame.columnconfigure(0, weight=1, minsize=672)
        self.text_frame.rowconfigure(0, weight=1, minsize=180)

        self.entry_message = tk.Label(self.text_frame, bd=5)
        #self.entry_message.bind('<Return>', self.send_message)
        #self.entry_message.focus()
        self.entry_message.config(text="Welcome to the game!")
        self.entry_message.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        self.start_button = tk.Button(self.monster_frame, text = "Start Game", command = self.send_start_game)
        self.start_button.pack()

        self.buttons_frame.columnconfigure(0, weight=1, minsize=144)
        self.buttons_frame.columnconfigure(1, weight=1, minsize=144) 
        self.buttons_frame.rowconfigure(0, weight=1, minsize=90)
        self.buttons_frame.rowconfigure(1, weight=1, minsize=90)

        self.turn_button = tk.Button(self.buttons_frame, text = "END TURN", command = self.send_end_turn)
        self.turn_button.grid(row=1, column=1, padx=0, pady=0, sticky=tk.NSEW)
        self.attack_button = tk.Button(self.buttons_frame, text = "ATTACK", command = self.attack)
        self.attack_button.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.heal_button = tk.Button(self.buttons_frame, text = "HEAL", command = self.heal)
        self.heal_button.grid(row=0, column=1, padx=0, pady=0, sticky=tk.NSEW)
        self.block_button = tk.Button(self.buttons_frame, text = "BLOCK", command = self.block)
        self.block_button.grid(row=1, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.turn_button["state"] = "disabled"
        self.lockButtons()
    
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