import tkinter as tk
from tkinter import ttk
from GRPCClientHelper.player import Player


class Hero_Frame(tk.Frame):
    def __init__(self, parent, player: Player):
        tk.Frame.__init__(self, parent, borderwidth=1,
                          bg="brown", padx=10, pady=10)
        self.parent = parent
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TProgressbar", background='green')

        self.figure = tk.Label(
            self, image=self.parent.imgs[player.getUsertype])
        # @self.enable_animation_thread(self.label1)
        self.username = tk.Label(self, text=self.player.getUsername)
        self.health = ttk.Progressbar(
            self, style="Horizontal.TProgressbar", orient='horizontal', variable=self.player.getHp(), mode='determinate')
        self.health.step(99.9)

        self.username.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.figure.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
        self.health.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
