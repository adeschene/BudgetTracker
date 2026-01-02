import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk 
from database.db_manager import DatabaseManager
from gui.transactions_tab import TransactionsTab
from gui.net_worth_tab import NetWorthTab
from gui.budget_tab import BudgetTab
from gui.visualizations_tab import VisualizationsTab
from gui.reports_tab import ReportsTab
from utils.settings_menu import SettingsWindow
from utils.help_menu import HelpWindow

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Budget Tracker")
        # Open window in the center of the screen
        w, h = 1280, 800
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Initialize database manager
        self.db = DatabaseManager()

        # Create main application UI (tabs)
        self.setup_ui()
    
    def setup_ui(self):
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Define grid columns: Col 0 (Left spacer), Col 1 (Tabs), Col 2 (Buttons)
        self.control_frame.columnconfigure(0, weight=1) # Left spacer
        self.control_frame.columnconfigure(1, weight=0) # Tab container (shrink to fit)
        self.control_frame.columnconfigure(2, weight=1) # Right container for buttons
        self.control_frame.rowconfigure(0, weight=1)

        # Place notebook in the center column
        self.notebook = ttk.Notebook(self.control_frame, style='Centered.TNotebook')
        self.notebook.grid(row=0, column=0, columnspan=3, sticky='nsew')

        # Triggers the on_tab_opened function within a tab class when switching to it, if it exists
        def on_tab_change(event):
            notebook = event.widget
            new_tab_id = notebook.select()
            new_tab = self.root.nametowidget(new_tab_id)
            if hasattr(new_tab,"on_tab_opened"):
                new_tab.on_tab_opened()

        self.notebook.bind("<<NotebookTabChanged>>", on_tab_change) # Optional tab switching function execution

        # Create each top-level tab, passing the shared DatabaseManager
        self.transactions_tab = TransactionsTab(self.notebook, self.db)
        self.net_worth_tab = NetWorthTab(self.notebook, self.db)
        self.budget_tab = BudgetTab(self.notebook, self.db)
        self.visualizations_tab = VisualizationsTab(self.notebook, self.db)
        self.reports_tab = ReportsTab(self.notebook, self.db)

        # Attach tabs to the notebook
        self.notebook.add(self.transactions_tab, text="Transactions")
        self.notebook.add(self.net_worth_tab, text="Net Worth")
        self.notebook.add(self.budget_tab, text="Budget")
        self.notebook.add(self.visualizations_tab, text="Visualizations")
        self.notebook.add(self.reports_tab, text="Reports")

        # Small container frame for the buttons to keep them together on the right
        self.button_container = ttk.Frame(self.control_frame)
        self.button_container.grid(row=0, column=2, sticky='ne', padx=5, pady=5)

        # Settings button with cogwheel icon
        full_settings_img = Image.open(r'assets\cogwheel.png')
        resized_settings_img = full_settings_img.resize((20, 20), Image.LANCZOS)
        settings_icon = ImageTk.PhotoImage(resized_settings_img)
        self.settings_button = ttk.Button(self.button_container, image=settings_icon, style="Nopadding.TButton", command=self.open_settings)
        self.settings_button.image = settings_icon # Keep a reference to avoid garbage collection
        self.settings_button.pack(side="left", padx=2)

        # Help button with question mark icon
        full_help_img = Image.open(r'assets\help.png')
        resized_help_img = full_help_img.resize((20, 20), Image.LANCZOS)
        help_icon = ImageTk.PhotoImage(resized_help_img)
        self.help_button = ttk.Button(self.button_container, image=help_icon, style="Nopadding.TButton", command=self.open_help)
        self.help_button.image = help_icon # Keep a reference to avoid garbage collection
        self.help_button.pack(side="left", padx=2)

    def open_settings(self):
        SettingsWindow(self.root, self.db)

    def open_help(self):
        HelpWindow(self.root)