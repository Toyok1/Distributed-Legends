import os
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk


pg_type = ["monster", "knight", "priest", "mage", ]


class Hero_Frame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, borderwidth=1,
                          bg="brown", padx=10, pady=10)

        # HEROES SETUP
        for i in range(2):
            self.columnconfigure(i, weight=1)
        for j in range(3):
            self.rowconfigure(j, weight=1)

        self.loadImgs()

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background='green')

        self.hero1 = tk.Label(self, image=self.imgs[0])
        self.hero1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        # @self.enable_animation_thread(self.label1)
        self.hero1_username = tk.Label(self, text=self.username)
        self.hero1_username.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)
        self.hero1_health = ttk.Progressbar(
            self, style="Horizontal.TProgressbar", orient='horizontal', variable=self.myHp, mode='determinate')
        self.hero1_health.step(99.9)
        self.hero1_health.grid(row=0, column=0, padx=5, pady=5, sticky=tk.S)

        ''' at this point we need to declare different labels and we can even fill them later when other people join but for right now as a proof of concept i'll use the knight'''
        self.hero2 = tk.Label(
            self, image=self.imgs[self.classType])
        self.hero2.grid(row=2, column=0, padx=5, pady=5, sticky=tk.NSEW)
        # self.enable_animation_thread(self.label2)
        self.hero2_username = tk.Label(self, text=self.username)
        self.hero2_username.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N)
        self.hero2_health = ttk.Progressbar(
            self, orient='horizontal', variable=self.myHp, mode='determinate')
        self.hero2_health.step(99.9)
        self.hero2_health.grid(row=2, column=0, padx=5, pady=5, sticky=tk.S)

        self.hero3 = tk.Label(self, image=self.imgs[0])
        self.hero3.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        # self.enable_animation_thread(self.label3)
        self.hero3_username = tk.Label(self, text=self.username)
        self.hero3_username.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.hero3_health = ttk.Progressbar(
            self, orient='horizontal', variable=self.myHp, mode='determinate')
        self.hero3_health.step(99.9)
        self.hero3_health.grid(row=1, column=1, padx=5, pady=5, sticky=tk.S)

    def loadImgs(self):
        global pg_type
        self.imgs = []
        path = "src/"+pg_type[0]+"/"+"idle"+"/"
        for i in os.listdir(path):
            self.imgs.append(ImageTk.PhotoImage(file=path+i))
