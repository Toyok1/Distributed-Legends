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
from GRPCClientHelper.config import key, cancel_id, aniThreadPointer, pg_type, sentinel_list


class Client():
    def __init__(self, user: str, userType: int, serverAddress: str, window, isHost: int):
        # the frame to put ui components on
        # self.myPostOffice.myPlayer = None  # quick reference to my player
        # self.otherPlayers = []  # quick reference to everyone but me
        # self.myPostOffice.players = []  # quick refernce to every player in the game
        # self.myPostOffice.heroesList = []
        self.GAME_STARTED = False
        self.isHost = True if isHost == 1 else False
        self.window = window
        self.myHp = [tk.IntVar(), tk.IntVar(), tk.IntVar(), tk.IntVar()]
        self.myBlock = 0
        self.imgs = []
        self.myPlayerType = userType
        self.username = user
        self.myTurn = False
        self.state = "idle"
        self.myUid = str(uuid.uuid4())
        self.labelrefs = {}
        self.fernet = Fernet(key)
        self.isFinished = False
        self.myPostOffice = helper.PostOffice(
            serverAddress, user, self.myUid, userType)
        self.myPostOffice.Subscribe()

        try:
            threading.Thread(target=self.myPostOffice.Listen_for_PingPong, args=(
                self.myUid,), daemon=True).start()
        except:
            self.CloseGame()

        self.__setup_ui()

        threading.Thread(target=self.__listen_for_turns, daemon=True).start()
        threading.Thread(target=self.__listen_for_actions, daemon=True).start()
        threading.Thread(target=self.__listen_for_attack, daemon=True).start()
        threading.Thread(target=self.__listen_for_health, daemon=True).start()
        threading.Thread(target=self.__listen_for_block, daemon=True).start()
        threading.Thread(target=self.__listen_for_labels, daemon=True).start()
        # threading.Thread(target=self.__diagnose, daemon=True).start()
        threading.Thread(target=self.__listen_for_finish, daemon=True).start()

        # probably the host won't need to run this thread so TODO when we have a way to distinguish them: get rid of it for the host.

        if userType != 1:
            threading.Thread(target=self.__check_for_start,
                             daemon=True).start()
        self.window.mainloop()

    def __check_for_start(self):
        try:
            while not self.GAME_STARTED:
                b = self.myPostOffice.CheckStarted()
                if b.started:
                    self.GAME_STARTED = b.started
                    self.cleanInitialList()
            self.start_button.destroy()
        except:
            print("Error in __check_for_start ")
            self.__check_for_start()

    def __diagnose(self):

        try:
            while True:
                if self.myPostOffice.myPlayer != None:
                    print("-------- START DIAGNOSTIC ---------")
                    print(self.myPostOffice.myPlayer.getUsername(), " - HP: ",
                          self.myPostOffice.myPlayer.getHp(), " - Block: ", self.myPostOffice.myPlayer.getBlock())
                    for item in self.myPostOffice.players:
                        print(item)
                    print("-------- END DIAGNOSTIC ---------")
                time.sleep(10)
        except:
            print("Error in __diagnose ")
            self.__diagnose()

    def __listen_for_labels(self):
        global sentinel_list

        while True:
            while not sentinel_list:
                time.sleep(0.25)
            sentinel_list = False
            for p in self.myPostOffice.players:
                self.adjustLabels(p)

    def __listen_for_health(self):
        try:
            for health in self.myPostOffice.HealingStream():
                print("HEALING: ", health, type(health.hp))
                healed = player.transformFromJSON(health.json_str)
                for p in self.myPostOffice.players:
                    if p.getUid() == healed.getUid():
                        healed = p
                health_amount = int(health.hp)

                healed.heal(health_amount)
                # self.adjustLabels(healed)
                '''for pl in self.myPostOffice.players:
                    self.adjustLabels(pl)'''
        except:
            print("Error in __listen_for_health")
            self.__listen_for_health()

    def __listen_for_attack(self):
        try:
            for a in self.myPostOffice.AttackStream():
                print("ATTACK: ", a)
                attacked = player.transformFromJSON(a.json_str)
                for p in self.myPostOffice.players:
                    if p.getUid() == attacked.getUid():
                        attacked = p
                attack_amount = int(a.attack)

                attacked.takeDamage(attack_amount)
        except:
            print("Error in __listen_for_attack")
            self.__listen_for_attack()

    def __listen_for_block(self):
        try:
            for block in self.myPostOffice.BlockStream():
                print("BLOCK: ", block, type(block.block))
                blocked = player.transformFromJSON(block.json_str)
                for p in self.myPostOffice.players:
                    if p.getUid() == blocked.getUid():
                        blocked = p
                block_amount = int(block.block)

                blocked.block(block_amount)
                # self.adjustLabels(blocked)
                '''for pl in self.myPostOffice.players:
                    self.adjustLabels(pl)'''
        except:
            print("Error in __listen_for_block")
            self.__listen_for_block()

    def __listen_for_actions(self):
        for action in self.myPostOffice.ActionStream():
            actor = player.transformFromJSON(action.sender)
            victim = player.transformFromJSON(action.reciever)
            for p in self.myPostOffice.players:
                if p.getUid() == victim.getUid():
                    victim = p
                    break

            action_amount = action.amount
            action_type = action.action_type
            mode = ""

            print(actor, victim, action_amount, action_type)

            if action_type == 0:
                mode = "attacks"
            elif action_type == 1:
                mode = "heals"
            elif action_type == 2:
                mode = "blocks for"
            else:
                mode = "idles"

            print("DONE CHECKING")
            addendum = victim.getUsername()
            print_message_array = ["User", actor.getUsername(
            ), mode, addendum, "for", str(abs(action_amount)), "points!"]

            # gets rid of the double space in addendum when action_type != 2
            print_message = " ".join(
                print_message_array).replace("  ", " ")
            print("print message did")
            self.entry_message.config(text=print_message)
            self.state = mode
            print("--- MESSAGE ---")
            print(print_message)
            print("--- MESSAGE ---")
            # print("MIO UID", self.myPostOffice.myPlayer.getUid())
            if victim.getUid() == self.myPostOffice.myPlayer.getUid():
                if action_type == 0:
                    self.myPostOffice.SendAttack(
                        user=victim, amount=action_amount)
                elif action_type == 1:
                    self.myPostOffice.SendHealing(
                        user=victim, amount=action_amount)
                elif action_type == 2:
                    self.myPostOffice.SendBlock(
                        user=victim, amount=action_amount)
                else:
                    print("Error with the actions :(")

    def __listen_for_turns(self):
        try:
            while self.myPostOffice.myPlayer is None:
                pass
            for turn in self.myPostOffice.TurnStream():
                what = player.transformFromJSON(turn.json_str)

                if self.GAME_STARTED:
                    print("STARTED")
                    counter = 0
                    for p in self.myPostOffice.players:
                        # print("Player " + p.getUsername() + "has" + str(p.getHp()) + " hp")
                        if p.getHp() <= 0:
                            counter += 1
                    if counter == len(self.myPostOffice.players) - 1:
                        self.isFinished = True
                        self.myPostOffice.SendFinishGame()
                        # end the game right here

                if what.getUsername() == self.myPostOffice.myPlayer.getUsername() and what.getUid() == self.myPostOffice.myPlayer.getUid():  # for testing use this line
                    # if self.fernet.decrypt(turn.ip).decode() == self.ip:
                    print("Mio turno: " + self.myPostOffice.myPlayer.getUsername())
                    self.turn_button["state"] = "normal"
                    self.unlockButtons()  # unlock the buttons when it's my turn
                    # if miei hp <= 0 endturn + interfaccia "you died"

                    if self.myPostOffice.myPlayer.getHp() <= 0:
                        if self.myPostOffice.myPlayer.getUsertype() == 1:  # monster
                            self.entry_message.config(
                                text="THE MONSTER IS DEAD! The game will end shortly.")
                            # end the game right here
                        else:
                            self.entry_message.config(
                                text="YOU ARE DEAD! Wait for one of your allies to revive you.")
                            self.lockButtons()
                            self.send_end_turn()
        except:
            print("Error in __listen_for_turns")
            self.__listen_for_turns()

    def __listen_for_finish(self):
        try:
            while self.isFinished == False:
                # doNothing
                pass
            for finish in self.myPostOffice.FinishStream():
                # print("Game is finished")
                if finish.fin == True:
                    if self.myPostOffice.myPlayer.getUsertype() == 1:
                        self.entry_message.config(text=finish.MonsterWin)
                    else:
                        self.entry_message.config(text=finish.HeroesDefeat)
                else:
                    if self.myPostOffice.myPlayer.getUsertype() == 1:
                        self.entry_message.config(text=finish.MonsterDefeat)
                    else:
                        self.entry_message.config(text=finish.HeroesWin)
                self.closeGame()
            print("Game would have finished")
        except:
            print("Error in __listen_for_turns")
            self.__listen_for_turns()

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
        # self.myPostOffice.ManualUpdateList(self.myPostOffice.myPlayer.getUid())
        for p in self.myPostOffice.players:
            self.adjustLabels(p)
        self.myPostOffice.EndTurn(self.myPostOffice.myPlayer)

    def attack_single(self, attacked):
        # attack people that are not your same class or friends
        self.assignButtons()
        self.lockButtons()
        self.state = "attack"
        # self.__after_action()
        print("MESSAGGIO CREATO")
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, attacked, actionType=0)

    def heal_single(self, healed):
        if self.myPostOffice.myPlayer.getUsertype() != 1:
            self.assignButtons()
        self.assignButtons()
        self.lockButtons()
        self.state = "heal"
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, healed, actionType=1)

    def block_single(self, blocked):
        # self.__after_action()
        if self.myPostOffice.myPlayer.getUsertype() != 1:
            self.assignButtons()
        self.assignButtons()
        self.lockButtons()
        self.state = "protect"
        self.myPostOffice.SendAction(
            self.myPostOffice.myPlayer, blocked, actionType=2)

    def adjustLabels(self, pl):
        print("CHANGING LABELS")
        # TODO: remove old disconnected player from labels references to change life value by their indexes
        if pl.getUsertype() == 1:
            self.labelrefs[pl.getUid()]["health_label"].config(
                text=str(pl.getHp())+'/100 ' + '['+str(pl.getBlock())+']')
        else:
            self.labelrefs[pl.getUid()]["health_label"].config(
                text=str(pl.getHp())+'/50 ' + '['+str(pl.getBlock())+']')

    def mapFuncToButtons(self, function, shout):
        buttons = [self.attack_button, self.block_button, self.heal_button]
        # print(len(self.myPostOffice.heroesList), " ",len(buttons) )

        for i in range(0, len(self.myPostOffice.heroesList)):
            try:
                buttons[i].configure(
                    text=shout + '\n' + self.myPostOffice.heroesList[i].getUsername())
                func = partial(function, self.myPostOffice.heroesList[i])
                buttons[i].configure(command=func)
            except:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
        for i in range(len(self.myPostOffice.heroesList), len(buttons)):
            try:
                buttons[i].configure(text="----")
                buttons[i].configure(command=self.do_nothing)
            except:
                print("Error with buttons with index ", i)

        self.turn_button.configure(text="BACK")
        self.turn_button.configure(command=self.assignButtons)

    def do_nothing(self):
        print("Did nothing")
        pass

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
            print("Cleaning ", u)
            if u.getUid() == self.myPostOffice.myPlayer.getUid():
                self.myPostOffice.myPlayer = u
                self.myPlayerType = u.getUsertype()
                if self.myPlayerType == 1:
                    self.monster_label.config(text=u.getUsername())
                    self.monsterRef = u
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
            else:
                if u.getUsertype() == 1:
                    self.monster_label.config(text=u.getUsername())
                    self.monsterRef = u
                    new_el = {"health_label": self.monster_healthLabel,
                              "image_label": self.monster, "username_label": self.monster_label}
                    self.labelrefs[u.getUid()] = new_el
                    self.myHp[0].set(u.getHp())
                    # monster = u
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
        # print("ASSIGNING")
        self.attack_button.configure(text="ATTACK")
        self.block_button.configure(text="BLOCK")
        self.heal_button.configure(text="HEAL")
        self.turn_button.configure(text="END TURN")
        self.turn_button.configure(command=self.send_end_turn)
        if self.myPostOffice.myPlayer.getUsertype() == 1:
            # print("ASSINGED MONSTER")
            # monster
            attack = partial(self.mapFuncToButtons,
                             self.attack_single, "ATTACK")
            self.attack_button.configure(command=attack)
            block = partial(self.block_single, self.myPostOffice.myPlayer)
            self.block_button.configure(command=block)
            heal = partial(self.heal_single, self.myPostOffice.myPlayer)
            self.heal_button.configure(command=heal)
        else:
            # print("ASSIGNED HERO")
            attack = partial(self.attack_single, self.monsterRef)
            self.attack_button.configure(command=attack)
            block = partial(self.mapFuncToButtons,
                            self.block_single, "BLOCK FOR")
            self.block_button.configure(command=block)
            heal = partial(self.mapFuncToButtons, self.heal_single, "HEAL")
            self.heal_button.configure(command=heal)

    def send_start_game(self):
        # if i'm the host i can start the game  TODO: make it so that only hosts can use this button and maybe delete it after use (?)
        self.myPostOffice.StartGame()
        self.cleanInitialList()
        self.start_button.destroy()

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

    '''def update_label_image(self, label, ani_img, ms_delay, frame_num):
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

    def cancel_animation(self):'
        global cancel_id
        global aniThreadPointer
        if cancel_id is not None:  # Animation started?
            self.window.after_cancel(cancel_id)
            while aniThreadPointer != []:  # kill all threads
                ttmp = aniThreadPointer.pop()
                ttmp.join()
            cancel_id = None'''

    def loadImgs(self):

        path = "src/"+"sprites/"
        # for image in os.listdir(path):
        images = ["0.png", "1.png", "2.png", "3.png"]
        for image in images:
            self.imgs.append(ImageTk.PhotoImage(file=path+image))

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
            self.monster_frame, bg="#323046", image=self.imgs[1])
        # self.monster.image = photo  # keep a reference!
        self.monster.pack()
        self.monster_label = tk.Label(
            self.monster_frame, bg="#323046", fg='#fff', text="Monster")
        self.monster_label.pack()
        self.monster_healthLabel = tk.Label(
            self.monster_frame, bg="#323046", fg='#fff', text='100/100 [0]')
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
        '''p_a = partial(self.attack_single, None)
        p_b = partial(self.block_single, None)
        p_h = partial(self.heal_single, None)'''
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
        self.lockButtons()

        # TEXT MESSAGE SETUP
        self.text_frame = tk.Frame(
            master=self.controls_frame, borderwidth=1, bg="#5f4548")
        self.text_frame.grid(row=0, column=1, sticky=tk.SE)
        self.text_frame.columnconfigure(0, weight=1, minsize=672)
        self.text_frame.rowconfigure(0, weight=1, minsize=180)

        self.entry_message = tk.Label(self.text_frame, bd=5)
        # self.entry_message.bind('<Return>', self.send_message)
        # self.entry_message.focus()
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
        userType_int = 0
        '''
        while True:  # pseudo do while loop
            userType = userTypeDialog.UserTypeDialog(root)
            root.wait_window(userType)
            if userType.result != None:
                break
        '''

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
    c = Client(username, userType.result if userType_int is None else userType_int,
               serverAddress, MainWindow, isHost)
