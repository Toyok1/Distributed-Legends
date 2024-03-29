import tkinter as tk


class ServerDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = 0
        self.title("HOST CHOICE")
        classTypes = [("Host server", 1), ("Join server", 2)]

        # Set window size and position
        self.geometry("300x150")
        self.center_window()

        # Create radio buttons
        self.var = tk.IntVar()
        self.var.set(0)

        tk.Label(self,
                text="""Will you host server or join server?""",
                justify=tk.LEFT,
                padx=20,
                pady=20).pack()

        for classType, val in classTypes:
            tk.Radiobutton(self,
                        text=classType,
                        width=20,
                        padx=20,
                        variable=self.var,
                        value=val).pack()
        # Create OK button
        ok_button = tk.Button(self, text="OK", command=self.ok)
        ok_button.pack()

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
