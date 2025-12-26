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
        self.control_frame.rowconfigure(0, weight=1)
        self.control_frame.columnconfigure(0, weight=1)
        # Ensure a second column exists for right-aligned controls (no extra weight)
        self.control_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.control_frame)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        # Create each top-level tab, passing the shared DatabaseManager
        self.transactions_tab = TransactionsTab(self.notebook, self.db)
        self.net_worth_tab = NetWorthTab(self.notebook, self.db)
        self.budget_tab = BudgetTab(self.notebook, self.db)
        self.visualizations_tab = VisualizationsTab(self.notebook, self.db)
        self.reports_tab = ReportsTab(self.notebook, self.db)

        # Attach tabs to the notebook
        self.notebook.add(self.transactions_tab.frame, text="Transactions")
        self.notebook.add(self.net_worth_tab.frame, text="Net Worth")
        self.notebook.add(self.budget_tab.frame, text="Budget")
        self.notebook.add(self.visualizations_tab.frame, text="Visualizations")
        self.notebook.add(self.reports_tab.frame, text="Reports")

        # Create settings button with cogwheel icon
        full_settings_img = Image.open('assets\cogwheel.png')
        resized_settings_img = full_settings_img.resize((20, 20), Image.LANCZOS)
        settings_icon = ImageTk.PhotoImage(resized_settings_img)
        self.settings_button = ttk.Button(self.control_frame, image=settings_icon, style="Nopadding.TButton", command=self.open_settings)
        self.settings_button.image = settings_icon  # Keep a reference to avoid garbage collection
        self.settings_button.grid(row=0, column=0, sticky='ne', padx=38, pady=5)

        # Create help button with question mark icon
        full_help_img = Image.open('assets\help.png')
        resized_help_img = full_help_img.resize((20, 20), Image.LANCZOS)
        help_icon = ImageTk.PhotoImage(resized_help_img)
        self.help_button = ttk.Button(self.control_frame, image=help_icon, style="Nopadding.TButton", command=self.open_help)
        self.help_button.image = help_icon  # Keep a reference to avoid garbage collection
        self.help_button.grid(row=0, column=0, sticky='ne', padx=5, pady=5)

    def open_settings(self):
        SettingsWindow(self.root, self.db)

    def open_help(self):
        HelpWindow(self.root)