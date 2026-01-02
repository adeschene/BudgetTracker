import tkinter as tk
from tkinter import ttk
from utils.import_template_manager import ImportTemplateManager
from utils.category_manager import CategoryManager
from utils.account_manager import AccountManager
from utils.helpers import center_window

class SettingsWindow:
    def __init__(self, parent, db):
        self.db = db
        self.parent = parent
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Settings")
        self.window.geometry("300x175")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(frame, text="Manage Accounts", command=self.manage_accounts).pack(pady=10)
        ttk.Button(frame, text="Manage Categories", command=self.manage_categories).pack(pady=10)
        ttk.Button(frame, text="Manage Import Templates", command=self.manage_import_templates).pack(pady=10)

        self.window.update_idletasks()
        center_window(self.window)
        self.window.deiconify()
    
    def manage_accounts(self):
        self.window.destroy()
        AccountManager(self.parent, self.db)
    
    def manage_categories(self):
        self.window.destroy()
        CategoryManager(self.parent, self.db)
    
    def manage_import_templates(self):
        self.window.destroy()
        ImportTemplateManager(self.parent, self.db)