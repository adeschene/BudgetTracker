import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.helpers import center_window

class AccountManager:
    def __init__(self, parent, db):
        self.db = db
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Manage Accounts")
        self.window.geometry("450x500")
        self.window.transient(parent)

        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(frame, columns=('Name', 'Type'), show='headings')
        self.tree.heading('Name', text='Name', anchor='center')
        self.tree.heading('Type', text='Type', anchor='center')
        self.tree.column('Name', anchor='center')
        self.tree.column('Type', anchor='center')
        self.tree.pack(fill='both', expand=True)
        
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Add Account", style='Accent.TButton', command=self.add_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Account", command=self.edit_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Account", command=self.delete_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side='left', padx=5)

        self.refresh_accounts()
        
        self.window.update_idletasks()
        center_window(self.window)
        self.window.deiconify()

    def refresh_accounts(self):
        # Reload accounts from DB and populate the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        accounts = self.db.get_accounts()
        for acc in accounts:
            self.tree.insert('', 'end', values=(acc['name'], acc['type'].title()), tags=(acc['id'],))

    def add_account(self):
        AccountDialog(self.window, self.db, callback=self.refresh_accounts)

    def edit_account(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to edit")
            return

        account_id = int(self.tree.item(selection[0])['tags'][0])
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
            account_id = int(self.tree.item(selection[0])['tags'][0])
            # Direct SQL here to ensure immediate removal; then refresh list
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

        # Dialog for creating or editing an account record
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Account" if not account else "Edit Account")
        self.dialog.geometry("300x300")
        self.dialog.transient(parent)

        ttk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_var = tk.StringVar(value=account['name'] if account else '')
        ttk.Entry(self.dialog, textvariable=self.name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=account['type'] if account else 'Checking')
        ttk.Combobox(self.dialog, textvariable=self.type_var, values=['Checking', 'Savings', 'Credit', 'Investment'], state='readonly').grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        self.auto_template_var = tk.BooleanVar(value=True)
        self.auto_template_check = ttk.Checkbutton(self.dialog, text="Automatically add a Net Worth\ntemplate entry for this account", variable=self.auto_template_var)
        self.auto_template_check.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='w')

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)
        
        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()
        self.dialog.grab_set()

    def save(self):
        # Persist the account (update existing or insert new)
        accounts = [a['name'] for a in self.db.get_accounts()]
        new_acc_name = self.name_var.get()
        if self.account: # Editing existing account
            # Check for duplicate account names but allow renaming to same name
            if self.account['name'] != new_acc_name and new_acc_name in accounts:
                messagebox.showerror("Error", "Account name already in use")
                return
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # Update record directly using SQL
            cursor.execute('''
                UPDATE accounts SET name = ?, type = ?, last_updated = ?
                WHERE id = ?
            ''', (self.name_var.get(), self.type_var.get().lower(), datetime.now().isoformat(), self.account['id']))
            conn.commit()
            conn.close()
        else: # New account
            # Check for duplicate account names
            if new_acc_name in accounts:
                messagebox.showerror("Error", "Account already exists")
                return
            self.db.add_account(new_acc_name, self.type_var.get(), self.auto_template_var.get())

        if self.callback:
            self.callback()

        self.dialog.destroy()
