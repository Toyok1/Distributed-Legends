import threading
import os
import tkinter as tk
import time
import uuid
import sys
import re
from functools import partial

from PIL import ImageTk, Image
from GRPCClientHelper import helper, player, serverDialog, userTypeDialog
from cryptography.fernet import Fernet
from tkinter import simpledialog
from tkinter import ttk
from GRPCClientHelper.config import key, cancel_id, aniThreadPointer, pg_type


class Client():
    def __init__(self, user: str, userType: int, serverAddress: str, window, isHost: int):
        # the frame to put ui components on
        self.GAME_STARTED = False
        self.isHost = True if isHost == 1 else False
        self.myPlayer = None  # quick reference to my player
        self.otherPlayers = []  # quick reference to everyone but me
        #self.myPostOffice.players = []  # quick refernce to every player in the game
        self.window = window
        self.myHp = [tk.IntVar(), tk.IntVar(), tk.IntVar(), tk.IntVar()]
        self.myBlock = 0
        self.myPlayerType = userType
        self.username = user
        self.heroesList = []
        self.myTurn = False
        self.state = "idle"
        self.myUid = str(uuid.uuid4())
        self.labelrefs = [[], [], []]
        self.fernet = Fernet(key)
        self.isFinished = False
        self.myPostOffice = helper.PostOffice(serverAddress, user, self.myUid, userType)
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
        threading.Thread(target=self.__listen_for_finish, daemon=True).start()

        # probably the host won't need to run this thread so TODO when we have a way to distinguish them: get rid of it for the host.
        threading.Thread(target=self.__check_for_start, daemon=True).start()
        self.window.mainloop()

    def __check_for_start(self):
        while not self.GAME_STARTED:
            b = self.myPostOffice.CheckStarted()
            if b.started:
                self.GAME_STARTED = b.started
                self.cleanInitialList()
        self.start_button.destroy()

    def __diagnose(self):
        while True:
            if self.myPlayer != None:
                print("-------- START DIAGNOSTIC ---------")
                print(self.myPlayer.getUsername(), " - HP: ",self.myPlayer.getHp(), " - Block: ", self.myPlayer.getBlock())
                for item in self.myPostOffice.players:
                    print(item)
                print("-------- END DIAGNOSTIC ---------")
            time.sleep(10)

    def __listen_for_health(self):
        for health in self.myPostOffice.HealthStream():
            healed = player.transformFromJSON(health.json_str)
            health_amount = health.hp

            for pl in self.myPostOffice.players:
                if pl.getUid() == healed.getUid():
                    pl.setHp(health_amount)
                    self.adjustLabels(pl)

    def __listen_for_block(self):
        for block in self.myPostOffice.BlockStream():
            blocker = player.transformFromJSON(block.json_str)
            block_amount = block.block

            for pl in self.myPostOffice.players:
                # if  utente["ip"]  ==  req_ip:
                if pl.getUid() == blocker.getUid():  # TODO change it to ip when not testing
                    pl.setBlock(block_amount)
                    self.adjustLabels(pl)

    def __listen_for_actions(self):
        for action in self.myPostOffice.ActionStream():
            actor = player.transformFromJSON(action.sender)
            victim = player.transformFromJSON(action.reciever)
            action_amount = action.amount
            action_type = action.action_type
            mode = ""

            match action_type:
                case 0:
                    mode = "attacks"
                case 1:
                    mode = "heals"
                case 2:
                    mode = "blocks for"
                case _:
                    mode = "idles"  # default

            addendum = victim.getUsername() 
            '''if action_type == 2:
                print_message_array = [
                    "User", actor.getUsername(), "prepares to block!"]
            else:'''
            print_message_array = ["User", actor.getUsername(), mode, addendum, "for", str(abs(action_amount)), "points!"]

            # gets rid of the double space in addendum when action_type != 2
            print_message = " ".join(print_message_array).replace("  ", " ")
            self.entry_message.config(text=print_message)
            self.state = mode
            print("--- MESSAGE ---")
            print(print_message)
            print("--- MESSAGE ---")
            # if the victim can block an attack he will do that before getting his hp hit
            if victim.getBlock() > 0 and action_type == 0 and victim.getUid() == self.myPlayer.getUid():
                action_amount = action_amount + int(victim.getBlock())
                new_block = 0 if action_amount < 0 else action_amount
                self.myPostOffice.SendBlock(user=victim, amount=new_block)

            if action_type < 2 and victim.getUid() == self.myPlayer.getUid():
                action_amount = victim.getHp() + action_amount
                action_amount = 0 if action_amount < 0 else action_amount
                action_amount = 100 if (victim.getUsertype() == 1 and action_amount > 100) else action_amount
                self.myPostOffice.SendHealth(user=victim, amount=action_amount)

            elif victim.getUid() == self.myPlayer.getUid():
                self.myPostOffice.SendBlock(user=victim, amount=action_amount)

    def __listen_for_turns(self):
        while self.myPlayer is None:
            pass
        for turn in self.myPostOffice.TurnStream():
            what = player.transformFromJSON(turn.json_str)

            if self.GAME_STARTED:
                print("STARTED")
                counter = 0
                for p in self.myPostOffice.players:
                    #print("Player " + p.getUsername() + "has" + str(p.getHp()) + " hp")
                    if p.getHp() <= 0:
                        counter += 1
                if counter == len(self.myPostOffice.players) - 1:
                    self.isFinished = True
                    self.myPostOffice.SendFinishGame()
                    # end the game right here

            if what.getUsername() == self.myPlayer.getUsername() and what.getUid() == self.myPlayer.getUid():  # for testing use this line
                # if self.fernet.decrypt(turn.ip).decode() == self.ip:
                print("Mio turno: " + self.myPlayer.getUsername())
                self.turn_button["state"] = "normal"
                self.unlockButtons()  # unlock the buttons when it's my turn
                # if miei hp <= 0 endturn + interfaccia "you died"

                if self.myPlayer.getHp() <= 0:
                    if self.myPlayer.getUsertype() == 1:  # monster
                        self.entry_message.config(
                            text="THE MONSTER IS DEAD! The game will end shortly.")
                        # end the game right here
                    else:
                        self.entry_message.config(
                            text="YOU ARE DEAD! Wait for one of your allies to revive you.")
                        self.lockButtons()
                        self.send_end_turn()

    def __listen_for_finish(self):
        while self.isFinished == False:
            # doNothing
            pass
        for finish in self.myPostOffice.FinishStream():
            #print("Game is finished")
            if finish.fin == True:
                if self.myPlayer.getUsertype() == 1:
                    self.entry_message.config(text=finish.MonsterWin)
                else:
                    self.entry_message.config(text=finish.HeroesDefeat)
            else:
                if self.myPlayer.getUsertype() == 1:
                    self.entry_message.config(text=finish.MonsterDefeat)
                else:
                    self.entry_message.config(text=finish.HeroesWin)
            self.closeGame()
        print("Game would have finished")

    def closeGame(self):
        # TODO end game
        self.lockButtons()
        self.isFinished = True
        self.turn_button["state"] = "disabled"
        self.state = "idle"
        self.myPostOffice = None
    # TODO: implement a one action per turn thing

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
        self.lockButtons()
        self.state = "idle"
        self.myPostOffice.EndTurn(self.myPlayer)

    def attack_single(self, attacked):
        # attack people that are not your same class or friends
        if self.myPlayer.getUsertype() == 1:
            self.assignButtons()
        self.assignButtons()
        self.lockButtons()
        self.state = "attack"
        # self.__after_action()
        print("MESSAGGIO CREATO")
        self.myPostOffice.SendAction(self.myPlayer, attacked, actionType=0)

    def heal_single(self, healed):
        if self.myPlayer.getUsertype() != 1:
            self.assignButtons()
        self.assignButtons()
        self.lockButtons()
        self.state = "heal"
        self.myPostOffice.SendAction(self.myPlayer, healed, actionType=1)

    def block_single(self, blocked):
        # self.__after_action()
        if self.myPlayer.getUsertype() != 1:
            self.assignButtons()
        self.assignButtons()
        self.lockButtons()
        self.state = "protect"
        self.myPostOffice.SendAction(self.myPlayer, blocked, actionType=2)

    def adjustLabels(self, pl):
        # TODO: remove old disconnected player from lables references for change life value by their indexs 
        localLabelsRef = self.labelrefs
        
        for old_player in self.myPostOffice.disconnected_players:
            ind = [self.labelrefs[0][i]["text"] for i in range(len(localLabelsRef[0]))].index(old_player.getUsername())
            localLabelsRef[0].remove(localLabelsRef[0][ind])
            localLabelsRef[1].remove(localLabelsRef[1][ind])
            localLabelsRef[2].remove(localLabelsRef[2][ind])
            pass
        
        if pl.getUsername() in [localLabelsRef[0][i]["text"] for i in range(len(localLabelsRef[0]))]:
                        ind = [localLabelsRef[0][i]["text"] for i in range(len(localLabelsRef[0]))].index(pl.getUsername())
                        if pl.getUsertype() == 1:

                            localLabelsRef[1][ind].config(
                                text=str(pl.getHp())+'/100 ' + '['+str(pl.getBlock())+']')
                        else:

                            localLabelsRef[1][ind].config(
                                text=str(pl.getHp())+'/50 ' + '['+str(pl.getBlock())+']')

    def mapFuncToButtons(self, function, shout):
        buttons = [self.attack_button, self.block_button, self.heal_button]

        for i in range(0, len(self.heroesList)):
            try:
                buttons[i].configure(
                    text=shout + '\n' + self.heroesList[i].getUsername())
                func = partial(function, self.heroesList[i])
                buttons[i].configure(command=func)
            except:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
        for i in range(len(self.heroesList),len(buttons)):
            try:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
            except:
                print("Error with buttons with index ",i)

        self.turn_button.configure(text="BACK")
        self.turn_button.configure(command=self.assignButtons)

    def do_nothing(self):
        print("Did nothing")
        pass

        

    def cleanInitialList(self):
        i = 0
        v = [self.hero1_username, self.hero2_username, self.hero3_username]
        v2 = [self.hero1_healthLabel, self.hero2_healthLabel, self.hero3_healthLabel]
        v3 = [self.hero1, self.hero2, self.hero3]
        for u in self.myPostOffice.players:
            if u.getUsername() == self.username:
                self.myPlayer = u
                self.myPlayerType = u.getUsertype()
                if self.myPlayerType == 1:
                    self.monster_label.config(text=u.getUsername())
                    self.monsterRef = u
                    self.labelrefs[0].append(self.monster_label)
                    self.labelrefs[1].append(self.monster_healthLabel)
                    self.labelrefs[2].append(self.monster)
                    self.myHp[0].set(u.getHp())
                else:
                    self.heroesList.append(u)
                    v[i].config(text=u.getUsername())
                    self.labelrefs[0].append(v[i])
                    self.labelrefs[1].append(v2[i])
                    self.labelrefs[2].append(v3[i])
                    self.myHp[i+1].set(u.getHp())
                    i += 1
            else:
                if u.getUsertype() == 1:
                    self.monster_label.config(text=u.getUsername())
                    self.monsterRef = u
                    self.labelrefs[0].append(self.monster_label)
                    self.labelrefs[1].append(self.monster_healthLabel)
                    self.labelrefs[2].append(self.monster)
                    self.myHp[0].set(u.getHp())
                    # monster = u
                else:
                    self.heroesList.append(u)
                    v[i].config(text=u.getUsername())
                    self.labelrefs[0].append(v[i])
                    self.labelrefs[1].append(v2[i])
                    self.labelrefs[2].append(v3[i])
                    self.myHp[i+1].set(u.getHp())
                    i += 1

        while i < 3:
            v[i].destroy()
            v2[i].destroy()
            v3[i].destroy()
            i += 1
        self.assignButtons()

    def assignButtons(self):
        #print("ASSIGNING")
        self.attack_button.configure(text="ATTACK")
        self.block_button.configure(text="BLOCK")
        self.heal_button.configure(text="HEAL")
        self.turn_button.configure(text="END TURN")
        self.turn_button.configure(command=self.send_end_turn)
        if self.myPlayer.getUsertype() == 1:
            #print("ASSINGED MONSTER")
            # monster
            attack = partial(self.mapFuncToButtons, self.attack_single, "ATTACK")
            self.attack_button.configure(command=attack)
            block = partial(self.block_single, self.myPlayer)
            self.block_button.configure(command=block)
            heal = partial(self.heal_single, self.myPlayer)
            self.heal_button.configure(command=heal)
        else:
            #print("ASSIGNED HERO")
            attack = partial(self.attack_single, self.monsterRef)
            self.attack_button.configure(command=attack)
            block = partial(self.mapFuncToButtons, self.block_single, "BLOCK FOR")
            self.block_button.configure(command=block)
            heal = partial(self.mapFuncToButtons, self.heal_single, "HEAL")
            self.heal_button.configure(command=heal)

    def send_start_game(self):
        # if i'm the host i can start the game  TODO: make it so that only hosts can use this button and maybe delete it after use (?)
        self.myPostOffice.StartGame()
        self.cleanInitialList()

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
            # 1000// len(self.imgs)  # Show all frames in 1000 ms.
            ms_delay = 250
            cancel_id = root.after(
                ms_delay, self.update_label_image, animation, self.imgs, ms_delay, 0)

    def enable_animation_thread(self, animation):
        global cancel_id
        global aniThreadPointer
        if cancel_id is None:
            t = threading.Thread(target=self.enable_animation, args=(
                animation,), daemon=True)  # create thread
            t.start()
            aniThreadPointer.append(t)

    def cancel_animation(self):
        global cancel_id
        global aniThreadPointer
        if cancel_id is not None:  # Animation started?
            self.window.after_cancel(cancel_id)
            while aniThreadPointer != []:  # kill all threads
                ttmp = aniThreadPointer.pop()
                ttmp.join()
            cancel_id = None

    def loadImgs(self):
        global pg_type
        self.imgs = []
        path = "src/"+pg_type[1]+"/"+"idle"+"/"
        for i in os.listdir(path):
            self.imgs.append(ImageTk.PhotoImage(file=path+i))

    def __setup_ui(self):
        self.master_frame = tk.Frame(self.window)
        self.master_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.master_frame.columnconfigure(0, weight=1, minsize=960)  # 16:10
        self.master_frame.rowconfigure(0, weight=1, minsize=420)
        self.master_frame.rowconfigure(1, weight=1, minsize=180)

        bgPhoto = ImageTk.PhotoImage(Image.open("./src/Background2.png"))

        self.background_frame = tk.Frame(
            self.master_frame, bg="", width=480, height=420)
        self.background_frame.place(x=0, y=0, width=480, height=420)
        self.background_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.background_frame.columnconfigure(0, weight=1, minsize=480)
        self.background_frame.rowconfigure(0, weight=1, minsize=420)

        self.background = tk.Label(
            self.background_frame, image=bgPhoto, width=480, height=420)
        self.background.image = bgPhoto
        self.background.grid(row=0, column=0, sticky=tk.NSEW)

        # HEROES SETUP

        self.loadImgs()
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background='green')

        self.hero1_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#5f4548")
        self.hero1_frame.grid(row=0, column=0, padx=290, pady=80, sticky=tk.NW)
        self.hero1_frame.columnconfigure(0, weight=1)
        self.hero1_frame.rowconfigure([0, 1, 2], weight=1)
        self.hero1 = tk.Label(
            self.hero1_frame, bg="#5f4548", image=self.imgs[0])
        self.hero1.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)

        self.hero1_username = tk.Label(
            self.hero1_frame, bg="#5f4548", text="Hero 1")
        self.hero1_username.grid(
            row=1, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.hero1_healthLabel = tk.Label(
            self.hero1_frame, bg="#5f4548", text='50/50 [0]')
        self.hero1_healthLabel.grid(
            row=2, column=0, padx=0, pady=0, sticky=tk.NSEW)

        ''' at this point we need to declare different labels and we can even fill them later when other people join but for right now as a proof of concept i'll use the knight'''
        self.hero2_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#2b2735")
        self.hero2_frame.grid(row=0, column=0, padx=180, pady=60, sticky=tk.SW)
        self.hero2_frame.columnconfigure(0, weight=1)
        self.hero2_frame.rowconfigure([0, 1, 2], weight=1)

        self.hero2 = tk.Label(
            self.hero2_frame, bg="#2b2735", image=self.imgs[0])
        self.hero2.grid(row=0, column=0, sticky=tk.NSEW)
        self.hero2_username = tk.Label(
            self.hero2_frame, bg="#2b2735", text="Hero 2")
        self.hero2_username.grid(
            row=1, column=0, sticky=tk.NSEW)
        self.hero2_healthLabel = tk.Label(
            self.hero2_frame, bg="#2b2735", text='50/50 [0]')
        self.hero2_healthLabel.grid(
            row=2, column=0, sticky=tk.NSEW)

        self.hero3_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#5f4548")
        self.hero3_frame.grid(row=0, column=0, padx=90, pady=100, sticky=tk.S)
        self.hero3_frame.columnconfigure(0, weight=1)
        self.hero3_frame.rowconfigure([0, 1, 2], weight=1)

        self.hero3 = tk.Label(
            self.hero3_frame, bg="#5f4548", image=self.imgs[0])
        self.hero3.grid(row=0, column=0, sticky=tk.NSEW)
        self.hero3_username = tk.Label(
            self.hero3_frame, bg="#5f4548", text="Hero 3")
        self.hero3_username.grid(
            row=1, column=0, sticky=tk.NSEW)
        self.hero3_healthLabel = tk.Label(
            self.hero3_frame, bg="#5f4548", text='50/50 [0]')
        self.hero3_healthLabel.grid(
            row=2, column=0, sticky=tk.NSEW)

        # MONSTER SETUP
        self.monster_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#323046")
        self.monster_frame.grid(row=0, column=0, padx=60, sticky=tk.E)

        image = Image.open("./src/monster/1.png")
        photo = ImageTk.PhotoImage(image)

        self.monster = tk.Label(self.monster_frame, bg="#323046", image=photo)
        self.monster.image = photo  # keep a reference!
        self.monster.pack()
        self.monster_label = tk.Label(
            self.monster_frame, bg="#323046", text="Monster")
        self.monster_label.pack()
        self.monster_healthLabel = tk.Label(
            self.monster_frame, bg="#323046", text='100/100 [0]')
        self.monster_healthLabel.pack()

        self.controls_frame = tk.Frame(self.master_frame, borderwidth=1)
        self.controls_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self.controls_frame.columnconfigure(0, weight=1, minsize=288)
        self.controls_frame.columnconfigure(1, weight=2, minsize=672)
        self.controls_frame.rowconfigure(0, weight=1, minsize=180)

        # BUTTONS SETUP
        self.buttons_frame = tk.Frame(
            self.controls_frame, borderwidth=1, bg="red")
        self.buttons_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.buttons_frame.columnconfigure([0, 1], weight=1, minsize=144)
        self.buttons_frame.rowconfigure([0, 1], weight=1, minsize=90)

        self.attack_button = tk.Button(
            self.buttons_frame, text="ATTACK", command=lambda: self.attack_single(None))
        self.attack_button.grid(row=0, column=0, sticky=tk.NSEW)
        self.heal_button = tk.Button(
            self.buttons_frame, text="HEAL", command=lambda: self.heal_single(None))
        self.heal_button.grid(row=0, column=1, sticky=tk.NSEW)
        self.block_button = tk.Button(
            self.buttons_frame, text="BLOCK", command=lambda: self.block_single(None))
        self.block_button.grid(row=1, column=0, sticky=tk.NSEW)
        self.turn_button = tk.Button(
            self.buttons_frame, text="END TURN", command=self.send_end_turn)
        self.turn_button.grid(row=1, column=1, sticky=tk.NSEW)
        self.turn_button["state"] = "disabled"
        self.lockButtons()

        # TEXT MESSAGE SETUP
        self.text_frame = tk.Frame(
            master=self.controls_frame, borderwidth=1, bg="red")
        self.text_frame.grid(row=0, column=1, sticky=tk.SE)
        self.text_frame.columnconfigure(0, weight=1, minsize=672)
        self.text_frame.rowconfigure(0, weight=1, minsize=180)

        self.entry_message = tk.Label(self.text_frame, bd=5)
        # self.entry_message.bind('<Return>', self.send_message)
        # self.entry_message.focus()
        self.entry_message.config(text="Welcome to the game!")
        self.entry_message.grid(row=0, column=0, padx=5,
                                pady=5, sticky=tk.NSEW)

        self.start_button = tk.Button(self.monster_frame, text="Start Game", bg="#323046", command=self.send_start_game)
        
        if self.isHost:
            self.start_button.pack()
            #self.start_button["state"] = "disabled"

    def __after_action(self):
        self.loadImgs()
        self.cancel_animation()
        self.enable_animation_thread(self.label1)
        self.enable_animation_thread(self.label2)
        self.enable_animation_thread(self.label3)


if __name__ == '__main__':
    root = tk.Tk()
    root.resizable(False, False)
    root.geometry("960x600")
    root.iconbitmap("./src/icon/icon.ico")
    MainWindow = tk.Frame(root, width=300, height=300)
    MainWindow.pack()
    root.withdraw()  # Hides the window
    username = None
    # "localhost"  # None when we deploy but for testing localhost is fine
    serverAddress = "localhost"
    while username is None:
        # retrieve a username so we can distinguish all the different clients
        username = simpledialog.askstring(
            "Username", "What's your username?", parent=root)
    root.title("RPGCombat - " + username)

    isHost = int(list(sys.argv)[1]) if len(list(sys.argv)) > 1 else 2

    userType_int = None

    if isHost == 1:
        userType_int = 1
    else:
        while True:  # pseudo do while loop
            userType = userTypeDialog.UserTypeDialog(root)
            root.wait_window(userType)
            if userType.result != 0:
                break

    # if isHost == 0:
    while (serverAddress != "localhost") or (serverAddress is None):
        # retrieve a username so we can distinguish all the different clients
        serverAddress = simpledialog.askstring(
            "Game's address", "What's the address?", parent=root)
        if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", serverAddress):
            break
    # else:
    # *code to start hosting server here*

    root.deiconify()  # Makes the window visible again
    # this starts a client and thus a thread which keeps connection to server open
    c = Client(username, userType.result if userType_int is None else userType_int, serverAddress, MainWindow, isHost)
