import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.csv_importer import CSVImporter
from gui.transactions_tab import TransactionsTab
from gui.net_worth_tab import NetWorthTab
from gui.budget_tab import BudgetTab
from gui.visualizations_tab import VisualizationsTab
from gui.reports_tab import ReportsTab

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Budget Tracker")
        self.root.geometry("1200x700")
        
        self.db = DatabaseManager()
        self.csv_importer = CSVImporter(self.db)
        
        self.setup_menu()
        self.setup_ui()
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Manage Categories", command=self.manage_categories)
        data_menu.add_command(label="Manage Accounts", command=self.manage_accounts)
        data_menu.add_separator()
        data_menu.add_command(label="Manage Import Templates", command=self.manage_import_templates)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        self.transactions_tab = TransactionsTab(self.notebook, self.db, self)
        self.net_worth_tab = NetWorthTab(self.notebook, self.db)
        self.budget_tab = BudgetTab(self.notebook, self.db)
        self.visualizations_tab = VisualizationsTab(self.notebook, self.db)
        self.reports_tab = ReportsTab(self.notebook, self.db)

        self.notebook.add(self.transactions_tab.frame, text="Transactions")
        self.notebook.add(self.net_worth_tab.frame, text="Net Worth")
        self.notebook.add(self.budget_tab.frame, text="Budget")
        self.notebook.add(self.visualizations_tab.frame, text="Visualizations")
        self.notebook.add(self.reports_tab.frame, text="Reports")
    
    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        dialog = ImportDialog(self.root, self.db, self.csv_importer, file_path)
        self.root.wait_window(dialog.dialog)
        
        if dialog.success:
            self.transactions_tab.refresh_transactions()
            messagebox.showinfo("Success", f"Imported {dialog.count} transactions")
    
    def manage_categories(self):
        CategoryManager(self.root, self.db)

    def manage_accounts(self):
        AccountManager(self.root, self.db)

    def manage_import_templates(self):
        from gui.import_template_manager import ImportTemplateManager
        ImportTemplateManager(self.root, self.db)

    def show_about(self):
        messagebox.showinfo("About", "Personal Budget Tracker v1.0\n\nTrack your finances with ease!")

class ImportDialog:
    def __init__(self, parent, db, csv_importer, file_path):
        self.db = db
        self.csv_importer = csv_importer
        self.file_path = file_path
        self.success = False
        self.count = 0

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import CSV")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Import Template:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(self.dialog, textvariable=self.template_var, state='readonly')
        templates = self.db.get_import_templates()
        template_combo['values'] = [t['template_name'] for t in templates]
        template_combo.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        self.has_header_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.dialog, text="File has header row", variable=self.has_header_var).grid(row=1, column=0, columnspan=2, pady=5)

        self.auto_categorize_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.dialog, text="Auto-categorize transactions", variable=self.auto_categorize_var).grid(row=2, column=0, columnspan=2, pady=5)

        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Import", command=self.do_import, width=10).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

    def do_import(self):
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showerror("Error", "Please select an import template")
            return

        templates = self.db.get_import_templates()
        template = next((t for t in templates if t['template_name'] == template_name), None)

        if not template:
            messagebox.showerror("Error", "Template not found")
            return

        try:
            self.count = self.csv_importer.import_transactions(
                self.file_path,
                template=template,
                has_header=self.has_header_var.get(),
                auto_categorize=self.auto_categorize_var.get()
            )
            self.success = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")

class CategoryManager:
    def __init__(self, parent, db):
        self.db = db
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Categories")
        self.window.geometry("500x400")
        self.window.transient(parent)
        
        frame = tk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(frame, columns=('Name', 'Type', 'Keywords'), show='headings')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Keywords', text='Keywords')
        self.tree.pack(fill='both', expand=True)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Add Category", command=self.add_category).pack(side='left', padx=5)
        tk.Button(button_frame, text="Close", command=self.window.destroy).pack(side='left', padx=5)
        
        self.refresh_categories()
    
    def refresh_categories(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        categories = self.db.get_categories()
        for cat in categories:
            self.tree.insert('', 'end', values=(cat['name'], cat['type'], cat['keywords']))
    
    def add_category(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Category")
        dialog.geometry("300x200")
        
        tk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        tk.Label(dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        type_var = tk.StringVar(value='expense')
        ttk.Combobox(dialog, textvariable=type_var, values=['income', 'expense']).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        tk.Label(dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        keywords_var = tk.StringVar()
        tk.Entry(dialog, textvariable=keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        def save():
            self.db.add_category(name_var.get(), type_var.get(), keywords_var.get())
            self.refresh_categories()
            dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)

class AccountManager:
    def __init__(self, parent, db):
        self.db = db
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Accounts")
        self.window.geometry("500x400")
        self.window.transient(parent)
        
        frame = tk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(frame, columns=('Name', 'Type', 'Balance'), show='headings')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Balance', text='Balance')
        self.tree.pack(fill='both', expand=True)
        
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Account", command=self.add_account).pack(side='left', padx=5)
        tk.Button(button_frame, text="Edit Account", command=self.edit_account).pack(side='left', padx=5)
        tk.Button(button_frame, text="Delete Account", command=self.delete_account).pack(side='left', padx=5)
        tk.Button(button_frame, text="Close", command=self.window.destroy).pack(side='left', padx=5)

        self.refresh_accounts()

    def refresh_accounts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        accounts = self.db.get_accounts()
        for acc in accounts:
            self.tree.insert('', 'end', values=(acc['name'], acc['type'], f"${acc['balance']:.2f}"), tags=(acc['id'],))

    def add_account(self):
        AccountDialog(self.window, self.db, callback=self.refresh_accounts)

    def edit_account(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to edit")
            return

        account_id = self.tree.item(selection[0])['tags'][0]
        accounts = self.db.get_accounts()
        account = next((acc for acc in accounts if acc['id'] == account_id), None)

        if account:
            AccountDialog(self.window, self.db, account=account, callback=self.refresh_accounts)

    def delete_account(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this account?"):
            account_id = self.tree.item(selection[0])['tags'][0]
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            conn.commit()
            conn.close()
            self.refresh_accounts()


class AccountDialog:
    def __init__(self, parent, db: DatabaseManager, account=None, callback=None):
        self.db = db
        self.account = account
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Account" if not account else "Edit Account")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_var = tk.StringVar(value=account['name'] if account else '')
        tk.Entry(self.dialog, textvariable=self.name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        tk.Label(self.dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=account['type'] if account else 'checking')
        ttk.Combobox(self.dialog, textvariable=self.type_var, values=['checking', 'savings', 'credit', 'investment']).grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        tk.Label(self.dialog, text="Balance:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.balance_var = tk.StringVar(value=str(account['balance']) if account else '0')
        tk.Entry(self.dialog, textvariable=self.balance_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="Save", command=self.save, width=10).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

    def save(self):
        try:
            balance = float(self.balance_var.get())

            if self.account:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE accounts SET name = ?, type = ?, balance = ?, last_updated = ?
                    WHERE id = ?
                ''', (self.name_var.get(), self.type_var.get(), balance, datetime.now().isoformat(), self.account['id']))
                conn.commit()
                conn.close()
            else:
                self.db.add_account(self.name_var.get(), self.type_var.get(), balance)

            if self.callback:
                self.callback()

            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid balance amount")
