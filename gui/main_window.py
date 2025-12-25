import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager
from gui.transactions_tab import TransactionsTab
from gui.net_worth_tab import NetWorthTab
from gui.budget_tab import BudgetTab
from gui.visualizations_tab import VisualizationsTab
from gui.reports_tab import ReportsTab
from utils.import_template_manager import ImportTemplateManager
from utils.category_manager import CategoryManager
from utils.account_manager import AccountManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Budget Tracker")
        # Open window in the center of the screen
        w, h = 1200, 800
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Initialize database manager
        self.db = DatabaseManager()

        # Create application menu and main UI (tabs)
        self.setup_menu()
        self.setup_ui()
    
    def setup_menu(self):
        # Build the top menubar with File, Data and Help menus
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Manage Categories", command=self.manage_categories)
        settings_menu.add_command(label="Manage Accounts", command=self.manage_accounts)
        settings_menu.add_command(label="Manage Import Templates", command=self.manage_import_templates)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create and attach each top-level tab, passing the shared DatabaseManager
        self.transactions_tab = TransactionsTab(self.notebook, self.db)
        self.net_worth_tab = NetWorthTab(self.notebook, self.db)
        self.budget_tab = BudgetTab(self.notebook, self.db)
        self.visualizations_tab = VisualizationsTab(self.notebook, self.db)
        self.reports_tab = ReportsTab(self.notebook, self.db)

        self.notebook.add(self.transactions_tab.frame, text="Transactions")
        self.notebook.add(self.net_worth_tab.frame, text="Net Worth")
        self.notebook.add(self.budget_tab.frame, text="Budget")
        self.notebook.add(self.visualizations_tab.frame, text="Visualizations")
        self.notebook.add(self.reports_tab.frame, text="Reports")
    
    def manage_categories(self):
        CategoryManager(self.root, self.db)

    def manage_accounts(self):
        AccountManager(self.root, self.db)

    def manage_import_templates(self):
        ImportTemplateManager(self.root, self.db)

    def show_about(self):
        messagebox.showinfo("About", "Personal Budget Tracker v1.0\n\nTrack your finances with ease!")
