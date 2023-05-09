import os
import subprocess
import sys
import tkinter as tk

from GRPCClientHelper import serverDialog

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    root.iconbitmap("./src/icon/icon.ico")
    root.title("RPGCombat - Host choice")
    root.withdraw()

    while True:  # in the future this is replaced by the script that opens up the server together with the client
        isHost = serverDialog.ServerDialog(root)
        root.wait_window(isHost)
        if isHost.result != 0:
            break

    if isHost.result == 1:
        os.system("(python SERVER.py || python3 SERVER.py) & (python client.py 1 ||python3 client.py 1 )")
    elif isHost.result == 2:
        os.system("python client.py || python3 client.py")
    else:
        print("errore")
