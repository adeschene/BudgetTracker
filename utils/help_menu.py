import tkinter as tk
from tkinter import ttk
from utils.helpers import center_window

class HelpWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Help")
        self.window.geometry("400x300")
        self.window.transient(parent)

        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(frame, text="1", command=self.help1).pack(pady=10)
        ttk.Button(frame, text="2", command=self.help2).pack(pady=10)
        ttk.Button(frame, text="3", command=self.help3).pack(pady=10)
        ttk.Button(frame, text="Close", command=self.window.destroy).pack(pady=10)

        self.window.update_idletasks()
        center_window(self.window)
        self.window.deiconify()
    
    def help1(self):
        pass
    
    def help2(self):
        pass
    
    def help3(self):
        pass