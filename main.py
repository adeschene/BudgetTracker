import tkinter as tk
from tkinter import ttk

from matplotlib import style
from gui.main_window import MainWindow

def main():
    root = tk.Tk()
    
    # Import the tcl file
    root.tk.call('source', 'assets/forest-dark.tcl')
    # Set the theme with the theme_use method
    style = ttk.Style(root)
    style.theme_use('forest-dark')
    # Treeview style config
    style.configure("Treeview", rowheight=30)
    # Create a custom style that removes all internal padding
    style.configure("Nopadding.TButton", padding=0)

    app = MainWindow(root)

    root.mainloop()

if __name__ == "__main__":
    main()
