import threading
import os
import tkinter as tk
import time
import uuid
import sys
import re
from functools import partial
import socket
from requests import get

from PIL import ImageTk, Image, ImageOps
from GRPCClientHelper import helper, player, serverDialog, userTypeDialog
from tkinter import simpledialog
from tkinter import ttk
from GRPCClientHelper.config import key


class Client():
    def __init__(self, user: str, userType: int, serverAddress: str, window, isHost: int):
        self.GAME_STARTED = False
        self.IS_IT_MY_TURN = False
        self.isHost = True if isHost == 1 else False
        self.window = window
        self.myHp = [tk.IntVar(), tk.IntVar(), tk.IntVar(), tk.IntVar()]
        self.myBlock = 0
        self.imgs = []
        self.imgs_mirrored = []
        self.history_index = 0
        # self.lavagnetta = ["Welcome to the game!"]
        self.myPlayerType = userType
        self.username = user
        self.myTurn = False
        self.state = "idle"
        self.myUid = str(uuid.uuid4())
        self.labelrefs = {}
        self.myPostOffice = helper.PostOffice(
            serverAddress, user, self.myUid, 'prova', userType)
        self.myPostOffice.Subscribe()

        self.__setup_ui()

        '''try:
            threading.Thread(target=self.myPostOffice.Listen_for_PingPong, args=(
                self.myUid,), daemon=True).start()
        except:
            self.entry_message.config(
                text="Connection lost :(")
            self.closeGame()'''

        threading.Thread(target=self.__listen_for_turns, daemon=True).start()
        threading.Thread(target=self.__listen_for_actions, daemon=True).start()
        threading.Thread(target=self.__listen_for_finish, daemon=True).start()

        '''if userType != 1:
            threading.Thread(target=self.__check_for_start, daemon=True).start()'''
        self.window.mainloop()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('192.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def do_nothing(self):
        pass

    def __listen_for_turns(self):
        while self.myPostOffice.myPlayer is None:
            pass
        for turn in self.myPostOffice.TurnStream():
            # print("TURNO - ", turn)
            if self.myPostOffice.isFinished == True:
                break
            what = player.transformFromJSON(turn.json_str)

            if self.GAME_STARTED:
                for pl in self.myPostOffice.players:
                    self.adjustLabels(pl)
                # list of all types of users. If there is no monster the heroes win by default.
                # NORMAL END GAME HANDLER (ONLY 1 PLAYER WITH MORE THAN 0 HP)
                if len(self.myPostOffice.playersCheck) <= 1:
                    print(self.myPostOffice.playersCheck[0].getUsername())
                    self.isStartedGame = False
                    self.TERMINATE = True
                    self.myPostOffice.SendFinishGame(
                        self.myPostOffice.playersCheck[0].getUsername())
                    print("GAME FINISHED"+" should send " +
                          self.myPostOffice.playersCheck[0].getUsername()+" to FinishGame")
                    break

            if what.getUid() == self.myPostOffice.myPlayer.getUid():
                # if self.fernet.decrypt(turn.ip).decode() == self.ip:
                # print("Mio turno: " + self.myPostOffice.myPlayer.getUsername())
                self.turn_button["state"] = "normal"
                self.IS_IT_MY_TURN = True
                self.unlockButtons()  # unlock the buttons when it's my turn
                # if miei hp <= 0 endturn + interfaccia "you died"

                if self.myPostOffice.myPlayer.getHp() <= 0:
                    if self.myPostOffice.myPlayer.getUsertype() == 1:  # monster
                        self.entry_message.config(
                            text="THE MONSTER IS DEAD! this shouldn't happen, TODO change it")
                        self.lockButtons()
                        # end the game right here
                    else:
                        self.entry_message.config(
                            text="YOU ARE DEAD! Better luck next time.")
                        self.lockButtons()
                        self.send_end_turn()
            else:
                self.IS_IT_MY_TURN = False

    def __check_for_start(self):
        try:
            while not self.GAME_STARTED:
                b = self.myPostOffice.CheckStarted()
                if b.started:
                    self.GAME_STARTED = b.started
                    self.cleanInitialList()
            self.start_button.destroy()
        except:
            # print("Error in __check_for_start ")
            self.__check_for_start()

    def __completeTurn(self):
        self.peers = ["1"]
        while True:
            while len(self.myPostOffice.peers_actions) < len(self.peers) + 1:
                time.sleep(0.5)
            print("completing turn")
            for action in self.peers_actions:
                actor = player.transformFromJSON(action.sender)
                victim = player.transformFromJSON(action.reciever)
                for p in self.myPostOffice.players:
                    if p.getUid() == victim.getUid():
                        victim = p
                        break

                action_amount = action.amount
                action_type = action.action_type
                mode = ""

                if action_type == 0:
                    mode = "attacks"
                elif action_type == 1:
                    mode = "heals"
                elif action_type == 2:
                    mode = "blocks for"
                else:
                    mode = "idles"

                addendum = victim.getUsername()
                print_message_array = ["User", actor.getUsername(
                ), mode, addendum, "for", str(abs(action_amount)), "points!"]

                # gets rid of the double space in addendum when action_type != 2
                print_message = " ".join(
                    print_message_array).replace("  ", " ")
                self.lavagnetta.append(print_message)

            for p in self.myPostOffice.players:
                self.adjustLabels(p)

            self.myPostOffice.peers_actions = []
            self.unlockButtons()

    def __listen_for_actions(self):
        while True:
            while len(self.myPostOffice.actionList) > self.history_index:
                action = self.myPostOffice.actionList[self.history_index]
                actor = player.transformFromJSON(action.sender)
                victim = player.transformFromJSON(action.reciever)
                self.history_index += 1
                for p in self.myPostOffice.players:
                    if p.getUid() == victim.getUid():
                        victim = p
                        break

                action_amount = action.amount
                action_type = action.action_type
                mode = ""

                if action_type == 0:
                    mode = "attacks"
                    victim.takeDamage(action_amount)
                elif action_type == 1:
                    mode = "heals"
                    victim.heal(action_amount)
                elif action_type == 2:
                    mode = "blocks for"
                    victim.obtainBlock(action_amount)
                else:
                    mode = "idles"

                addendum = victim.getUsername()
                print_message_array = ["User", actor.getUsername(
                ), mode, addendum, "for", str(abs(action_amount)), "points!"]

                # gets rid of the double space in addendum when action_type != 2
                print_message = " ".join(
                    print_message_array).replace("  ", " ")
                self.entry_message.config(text=print_message)
                self.state = mode

    def __listen_for_finish(self):
        numberAlive = 5
        while numberAlive > 1:
            if len(self.myPostOffice.players) == 1 and self.GAME_STARTED:
                break
            numberAlive = 0
            for i in range(len(self.myPostOffice.players)):
                numberAlive += 1 if self.myPostOffice.players[i].getHp(
                ) > 0 else 0
            # print("Number of players alive: ", numberAlive)
        print("Game is finished BY LISTEN FOR FINISH")
        for finish in self.myPostOffice.FinishStream():
            print("Game is finished ", finish.fin)
            self.entry_message.config(text=finish.fin + " won the game")
            break

    def send_end_turn(self):
        self.turn_button["state"] = "disabled"
        self.lockButtons()
        self.myPostOffice.SendEndTurn()

    def closeGame(self):
        self.lockButtons()
        self.myPostOffice.isFinished = True
        self.turn_button["state"] = "disabled"
        self.state = "idle"
        self.send_end_turn()

    def lockButtons(self):
        self.attack_button["state"] = "disabled"
        self.heal_button["state"] = "disabled"
        self.block_button["state"] = "disabled"

    def unlockButtons(self):
        self.attack_button["state"] = "normal"
        self.heal_button["state"] = "normal"
        self.block_button["state"] = "normal"
        self.lavagnetta = []
        self.entry_message.config(text="Do something!")

    def attack_single(self, attacked):
        # attack people that are not your same class or friends
        self.assignButtons()
        self.lockButtons()
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, attacked, actionType=0)

    def heal_single(self, healed):
        self.assignButtons()
        self.lockButtons()
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, healed, actionType=1)

    def block_single(self, blocked):
        self.assignButtons()
        self.lockButtons()
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, blocked, actionType=2)

    def adjustLabels(self, pl):
        # #print("CHANGING LABELS FOR ", pl)
        # TODO: remove old disconnected player from labels references to change life value by their indexes
        self.labelrefs[pl.getUid()]["health_label"].config(
            text=str(pl.getHp())+'/50 ' + '['+str(pl.getBlock())+']')

    def mapFuncToButtons(self, function, shout):
        buttons = [self.attack_button, self.block_button, self.heal_button]
        # #print(len(self.myPostOffice.heroesList), " ", len(buttons))
        not_me = [p for p in self.myPostOffice.players if p.getUid(
        ) != self.myPostOffice.myPlayer.getUid()]
        for i in range(0, len(not_me)):
            try:
                buttons[i].configure(
                    text=shout + '\n' + not_me[i].getUsername())
                func = partial(function, not_me[i])
                buttons[i].configure(command=func)
            except:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
        for i in range(len(not_me), len(buttons)):
            try:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
            except:
                print("Error with buttons with index ", i)

        self.turn_button.configure(text="BACK")
        self.turn_button.configure(command=self.assignButtons)

    def cleanInitialList(self):
        # [{"uid": adsd, health_label: label},{},{},{}]
        # {uid_1:...., uid_2....}
        i = 0
        v = [self.hero1_username, self.hero2_username,
             self.hero3_username]  # labels_username
        v2 = [self.hero1_healthLabel, self.hero2_healthLabel,
              self.hero3_healthLabel]  # labels_health
        v3 = [self.hero1, self.hero2, self.hero3]  # labels_images
        for u in self.myPostOffice.players:
            # #print("Cleaning ", u)
            if u.getUid() == self.myPostOffice.myPlayer.getUid():
                self.myPostOffice.myPlayer = u
                self.myPlayerType = u.getUsertype()
                # print("My player is ", u)
                self.monster_label.config(text=u.getUsername())
                self.monsterRef = u
                self.monster.config(image=self.imgs_mirrored[u.getUsertype()])
                new_el = {"health_label": self.monster_healthLabel,
                          "image_label": self.monster, "username_label": self.monster_label}
                self.labelrefs[u.getUid()] = new_el
                self.myHp[0].set(u.getHp())

            else:
                v[i].config(text=u.getUsername())
                v3[i].config(image=self.imgs[u.getUsertype()])
                new_el = {
                    "health_label": v2[i], "image_label": v3[i], "username_label": v[i]}
                self.labelrefs[u.getUid()] = new_el
                self.myHp[i+1].set(u.getHp())
                i += 1

        while i < 3:
            v[i].destroy()
            v2[i].destroy()
            v3[i].destroy()
            i += 1
        self.assignButtons()

    def assignButtons(self):
        # #print("ASSIGNING")
        self.attack_button.configure(text="ATTACK")
        self.block_button.configure(text="BLOCK")
        self.heal_button.configure(text="HEAL")
        self.turn_button.configure(text="END TURN")
        self.turn_button.configure(command=self.send_end_turn)
        # if self.myUid == "1":
        # monster
        attack = partial(self.mapFuncToButtons,
                         self.attack_single, "ATTACK")
        self.attack_button.configure(command=attack)
        block = partial(self.block_single, self.myPostOffice.myPlayer)
        self.block_button.configure(command=block)
        heal = partial(self.heal_single, self.myPostOffice.myPlayer)
        self.heal_button.configure(command=heal)
        '''else:
            # #print("ASSIGNED HERO")
            self.monsterRef = self.myPostOffice.players[0]
            attack = partial(self.mapFuncToButtons,
                             self.attack_single, "ATTACK")
            self.attack_button.configure(command=attack)
            block = partial(self.mapFuncToButtons,
                            self.block_single, "BLOCK FOR")
            self.block_button.configure(command=block)
            heal = partial(self.mapFuncToButtons, self.heal_single, "HEAL")
            self.heal_button.configure(command=heal)'''

    def send_start_game(self):
        # if i'm the host i can start the game  TODO: make it so that only hosts can use this button and maybe delete it after use (?)
        self.myPostOffice.StartGame()
        self.cleanInitialList()
        self.lockButtons()
        self.start_button.destroy()
        threading.Timer(16, self.trueStart).start()
        self.entry_message.configure(text="Now Loading...")

    def trueStart(self):
        self.GAME_STARTED = True
        if self.IS_IT_MY_TURN == True:
            self.unlockButtons()
            self.turn_button["state"] = "normal"

    def loadImgs(self):
        path = "src/"+"sprites/"
        # for image in os.listdir(path):
        images = ["0.png", "1.png", "2.png", "3.png"]
        for image in images:
            self.imgs.append(ImageTk.PhotoImage(file=path+image))
        pathMirror = "src/"+"sprites/mirrored/"
        # for image in os.listdir(path):
        images = ["0.png", "1.png", "2.png", "3.png"]
        for image in images:
            self.imgs_mirrored.append(
                ImageTk.PhotoImage(file=pathMirror+image))

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

        self.hero1_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#5f4548")
        self.hero1_frame.grid(row=0, column=0, padx=290, pady=80, sticky=tk.NW)
        self.hero1_frame.columnconfigure(0, weight=1)
        self.hero1_frame.rowconfigure([0, 1, 2], weight=1)
        self.hero1 = tk.Label(
            self.hero1_frame, bg="#5f4548", image=self.imgs[0])
        self.hero1.grid(row=0, column=0, padx=0, pady=0, sticky=tk.NSEW)

        self.hero1_username = tk.Label(
            self.hero1_frame, bg="#5f4548", fg='#fff', text="Hero 1")
        self.hero1_username.grid(
            row=1, column=0, padx=0, pady=0, sticky=tk.NSEW)
        self.hero1_healthLabel = tk.Label(
            self.hero1_frame, bg="#5f4548", fg='#fff', text='50/50 [0]')
        self.hero1_healthLabel.grid(
            row=2, column=0, padx=0, pady=0, sticky=tk.NSEW)

        ''' at this point we need to declare different labels and we can even fill them later when other people join but for right now as a proof of concept i'll use the knight'''
        self.hero2_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#5f4548")
        self.hero2_frame.grid(row=0, column=0, padx=180, pady=60, sticky=tk.SW)
        self.hero2_frame.columnconfigure(0, weight=1)
        self.hero2_frame.rowconfigure([0, 1, 2], weight=1)

        self.hero2 = tk.Label(
            self.hero2_frame, bg="#5f4548", image=self.imgs[2])
        self.hero2.grid(row=0, column=0, sticky=tk.NSEW)
        self.hero2_username = tk.Label(
            self.hero2_frame, bg="#5f4548", fg='#fff', text="Hero 2")
        self.hero2_username.grid(
            row=1, column=0, sticky=tk.NSEW)
        self.hero2_healthLabel = tk.Label(
            self.hero2_frame, bg="#5f4548", fg='#fff', text='50/50 [0]')
        self.hero2_healthLabel.grid(
            row=2, column=0, sticky=tk.NSEW)

        self.hero3_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#5f4548")
        self.hero3_frame.grid(row=0, column=0, padx=90, pady=100, sticky=tk.S)
        self.hero3_frame.columnconfigure(0, weight=1)
        self.hero3_frame.rowconfigure([0, 1, 2], weight=1)

        self.hero3 = tk.Label(
            self.hero3_frame, bg="#5f4548", image=self.imgs[3])
        self.hero3.grid(row=0, column=0, sticky=tk.NSEW)
        self.hero3_username = tk.Label(
            self.hero3_frame, bg="#5f4548", fg='#fff', text="Hero 3")
        self.hero3_username.grid(
            row=1, column=0, sticky=tk.NSEW)
        self.hero3_healthLabel = tk.Label(
            self.hero3_frame, bg="#5f4548", fg='#fff', text='50/50 [0]')
        self.hero3_healthLabel.grid(
            row=2, column=0, sticky=tk.NSEW)

        # MONSTER SETUP
        self.monster_frame = tk.Frame(
            self.background_frame, padx=5, pady=5, bg="#323046")
        self.monster_frame.grid(row=0, column=0, padx=60, sticky=tk.E)

        # image = Image.open("./src/monster/1.png")
        # photo = ImageTk.PhotoImage(image)

        self.monster = tk.Label(
            self.monster_frame, bg="#323046", image=self.imgs_mirrored[1])
        # self.monster.image = photo  # keep a reference!
        self.monster.pack()
        self.monster_label = tk.Label(
            self.monster_frame, bg="#323046", fg='#fff', text="Monster")
        self.monster_label.pack()
        self.monster_healthLabel = tk.Label(
            self.monster_frame, bg="#323046", fg='#fff', text='50/50 [0]')
        self.monster_healthLabel.pack()

        self.controls_frame = tk.Frame(self.master_frame, borderwidth=1)
        self.controls_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self.controls_frame.columnconfigure(0, weight=1, minsize=288)
        self.controls_frame.columnconfigure(1, weight=2, minsize=672)
        self.controls_frame.rowconfigure(0, weight=1, minsize=180)

        # BUTTONS SETUP
        self.buttons_frame = tk.Frame(
            self.controls_frame, borderwidth=1, bg="#5f4548")
        self.buttons_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.buttons_frame.columnconfigure([0, 1], weight=1, minsize=144)
        self.buttons_frame.rowconfigure([0, 1], weight=1, minsize=90)
        self.attack_button = tk.Button(
            self.buttons_frame, text="ATTACK", bg='#f00', fg='#fff', command=self.do_nothing)
        self.attack_button.grid(row=0, column=0, sticky=tk.NSEW)
        self.heal_button = tk.Button(
            self.buttons_frame, text="HEAL", command=self.do_nothing)
        self.heal_button.grid(row=0, column=1, sticky=tk.NSEW)
        self.block_button = tk.Button(
            self.buttons_frame, text="BLOCK", command=self.do_nothing)
        self.block_button.grid(row=1, column=0, sticky=tk.NSEW)
        self.turn_button = tk.Button(
            self.buttons_frame, text="END TURN", command=self.send_end_turn)
        self.turn_button.grid(row=1, column=1, sticky=tk.NSEW)
        self.turn_button["state"] = "disabled"
        self.assignButtons()
        self.lockButtons()

        # TEXT MESSAGE SETUP
        self.text_frame = tk.Frame(
            master=self.controls_frame, borderwidth=1, bg="#5f4548")
        self.text_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self.text_frame.columnconfigure(0, weight=1, minsize=672)
        self.text_frame.rowconfigure(0, weight=1, minsize=180)

        self.entry_message = tk.Label(self.text_frame, bd=5)

        if self.isHost == True:
            my_str = "Welcome to the game! Have your friends connect to your global IP: " + \
                "idk figure it out" + \
                " \nor your local IP: " + self.get_local_ip()  # TODO: CHANGE THIS URGENTLY
            self.entry_message.config(text=my_str)
        else:
            self.entry_message.config(text="Welcome to the game!")
        self.entry_message.grid(row=0, column=0, padx=5,
                                pady=5, sticky=tk.NSEW)

        self.start_button = tk.Button(
            self.monster_frame, text="Start Game", bg="#323046", padx=0, pady=0, command=self.send_start_game)

        if self.isHost:
            self.start_button.pack()
            # self.start_button["state"] = "disabled"

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
    try:
        root.iconbitmap("./src/icon/icon.ico")
    except:
        pass
    MainWindow = tk.Frame(root, width=300, height=300)
    MainWindow.pack()
    root.withdraw()  # Hides the window
    username = None
    # "localhost"  # None when we deploy but for testing localhost is fine

    while username is None or username.strip() == "":
        # retrieve a username so we can distinguish all the different clients
        username = simpledialog.askstring(
            "Username", "What's your username?", parent=root)
    root.title("Distributed Legends - " + username)

    isHost = int(list(sys.argv)[1]) if len(list(sys.argv)) > 1 else 2

    userType_int = None

    while True:
        userType = userTypeDialog.UserTypeDialog(root)
        root.wait_window(userType)
        if userType.result != None:
            break

    isHost = 1  # TODO: sono tutti host
    serverAddress = None if isHost != 1 else "localhost"

    while (serverAddress != "localhost") or (serverAddress is None):
        # retrieve a username so we can distinguish all the different clients
        serverAddress = simpledialog.askstring(
            "Game's address", "What's the address?", parent=root)
        if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", serverAddress):
            break

    root.deiconify()  # Makes the window visible again
    # this starts a client and thus a thread which keeps connection to server open
    c = Client(username, userType.result if userType_int is None else userType_int,
               serverAddress, MainWindow, isHost)
