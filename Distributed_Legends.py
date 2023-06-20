import os
import threading
import tkinter as tk

from GRPCClientHelper import serverDialog

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    try:
        root.iconbitmap("./src/icon/icon.ico")
    except:
        pass
    root.title("Distributed Legends p2p")
    root.withdraw()

    while True:  # in the future this is replaced by the script that opens up the server together with the client
        isHost = serverDialog.ServerDialog(root)
        root.wait_window(isHost)
        if isHost.result != 0:
            break

    if isHost.result == 1:
        threading.Thread(target=lambda: os.system(
            "(python SERVER.py || python3 SERVER.py) "), daemon=True).start()
        threading.Thread(target=lambda: os.system(
            "(python client.py 1 ||python3 client.py 1 )"), daemon=True).start()
    elif isHost.result == 2:
        os.system("python client.py || python3 client.py")
    else:
        print("errore")
