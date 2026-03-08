import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from utils.import_template_manager import ImportTemplateManager
from utils.category_manager import CategoryManager
from utils.account_manager import AccountManager
from utils.csv_exporter import CSVExporter
from utils.helpers import center_window

class SettingsWindow:
    def __init__(self, parent, db, main_window=None):
        self.db = db
        self.parent = parent
        self.main_window = main_window or parent
        self.csv_exporter = CSVExporter(self.db) # CSV export helper
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Settings")
        self.window.geometry("300x230")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(frame, text="Manage Accounts", command=self.manage_accounts).pack(pady=10)
        ttk.Button(frame, text="Manage Categories", command=self.manage_categories).pack(pady=10)
        ttk.Button(frame, text="Manage Import Templates", command=self.manage_import_templates).pack(pady=10)
        ttk.Button(frame, text="Export Transactions", command=self.export_data).pack(pady=10)

        self.window.update_idletasks()
        center_window(self.window)
        self.window.deiconify()
    
    def manage_accounts(self):
        self.window.destroy()
        AccountManager(self.parent, self.db)
    
    def manage_categories(self):
        self.window.destroy()
        CategoryManager(self.parent, self.db, callback=self.main_window.refresh_dependent_tabs)
    
    def manage_import_templates(self):
        self.window.destroy()
        ImportTemplateManager(self.parent, self.db)
    
    def export_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Transactions"
        )
        
        if file_path:
            try:
                self.csv_exporter.export_transactions(file_path)
                messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")