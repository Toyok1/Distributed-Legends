import tkinter as tk
import random


class UserTypeDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Pick your class")
        classTypes = [("Knight", 0),
                      ("Priest", 2), ("Mage", 3), ("Monster", 1)]
        # classHost = [("Monster", 1)]

        # Set window size and position
        self.geometry("200x150")
        self.center_window()

        # Create radio buttons
        self.var = tk.IntVar()
        self.var.set(random.randint(0, 3))
        self.result = self.var.get()

        tk.Label(self,
                 text="""Choose your class:""",
                 justify=tk.LEFT,
                 padx=20).pack()

        for classType, val in classTypes:
            tk.Radiobutton(self,
                           text=classType,
                           padx=20,
                           variable=self.var,
                           value=val).pack()
        # Create OK button

        ok_button = tk.Button(self, text="OK", command=self.ok)
        self.bind('<Return>', self.ok_event)
        ok_button.pack()

    def ok_event(self, event):
        self.ok()

    def ok(self):
        # Return the selected option
        self.result = self.var.get()
        self.destroy()

    def center_window(self):
        # Get window size and position
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate center position
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)

        # Set window position
        self.geometry(f"+{x}+{y}")
