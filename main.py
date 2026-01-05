import tkinter as tk
from tkinter import ttk

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
    style.configure("Count.TLabel", font=('Roboto', 10), foreground="#00AD4E")
    style.configure("Nopadding.TButton", padding=0)
    # Increased button font, normal button
    style.configure("Med.TButton", font=('Roboto', 12), padding=0)
    style.configure("Big.TButton", font=('Roboto', 16), padding=0)
    # Extend the Accent button style and add larget font
    style.configure("Big.Accent.TButton", font=('Roboto', 16), padding=0)
    # Create a custom style for font in net worth template application LabelFrames
    style.configure("NWTE.TLabelframe.Label", font=('Roboto', 11))
    # Styling for main tab notebook
    style.configure("Centered.TNotebook", tabposition='n', tabmargins=[0, 5, 0, 0])
    style.layout("Centered.TNotebook.Tab", [
        ('Notebook.tab', {'sticky': 'nswe', 'children': [
            ('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [
                ('Notebook.label', {'side': 'top', 'sticky': ''})], # Removing sticky='w' centers text
            })]
        })]
    )
    # Extend centered style for main window tabs specifically, larger font, more padding
    style.configure("Main.Centered.TNotebook.Tab", font=('Roboto', 11), padding=[8, 0, 8, 0])
    

    app = MainWindow(root)

    root.mainloop()

if __name__ == "__main__":
    main()
