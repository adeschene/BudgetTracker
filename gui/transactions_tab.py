import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager
from gui.shared_functions import center_window

class TransactionsTab:
    def __init__(self, parent, db: DatabaseManager, main_window=None):
        self.db = db
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self.sort_column = None
        self.sort_reverse = False

        self.setup_ui()
        self.refresh_transactions()
    
    def setup_ui(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(top_frame, text="Filter by:").pack(side='left', padx=5)

        self.use_date_filter_var = tk.BooleanVar(value=False)
        date_filter_check = ttk.Checkbutton(top_frame, text="Date Filter", style='Switch',
                                          variable=self.use_date_filter_var,
                                          command=self.toggle_date_filter)
        date_filter_check.pack(side='left', padx=5)

        ttk.Label(top_frame, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(top_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                          state='disabled')
        self.start_date_picker.pack(side='left', padx=5)

        ttk.Label(top_frame, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(top_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                        maxdate=datetime.now(), state='disabled')
        self.end_date_picker.pack(side='left', padx=5)

        ttk.Label(top_frame, text="Category:").pack(side='left', padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, width=15)
        self.category_combo.pack(side='left', padx=5)
        self.update_category_list()

        ttk.Button(top_frame, text="Filter", command=self.refresh_transactions).pack(side='left', padx=5)
        ttk.Button(top_frame, text="Clear", command=self.clear_filters).pack(side='left', padx=5)
        
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(tree_frame, columns=('Date', 'Description', 'Amount', 'Category', 'Account', 'Notes'),
                                 show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Date', text='Date', command=lambda: self.sort_by_column('Date'))
        self.tree.heading('Description', text='Description', command=lambda: self.sort_by_column('Description'))
        self.tree.heading('Amount', text='Amount', command=lambda: self.sort_by_column('Amount'))
        self.tree.heading('Category', text='Category', command=lambda: self.sort_by_column('Category'))
        self.tree.heading('Account', text='Account', command=lambda: self.sort_by_column('Account'))
        self.tree.heading('Notes', text='Notes')

        self.tree.column('Date', width=60, anchor='center')
        self.tree.column('Description', width=100)
        self.tree.column('Amount', width=60, anchor='center')
        self.tree.column('Category', width=60, anchor='center')
        self.tree.column('Account', width=60, anchor='center')
        self.tree.column('Notes', width=100)

        self.tree.bind('<Double-Button-1>', self.on_double_click)

        self.tree.pack(fill='both', expand=True)
        
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)

        if self.main_window:
            ttk.Button(button_frame, text="Import CSV", style='Accent.TButton', command=self.main_window.import_csv).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Add Transaction", command=self.add_transaction).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Edit Transaction", command=self.edit_transaction).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Delete Transaction", command=self.delete_transaction).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Refresh", command=self.refresh_transactions).pack(side='left', padx=5)
    
    def update_category_list(self):
        categories = self.db.get_categories()
        category_names = [''] + [cat['name'] for cat in categories]
        self.category_combo['values'] = category_names
    
    def refresh_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        start_date = self.start_date_picker.get() if self.use_date_filter_var.get() else None
        end_date = self.end_date_picker.get() if self.use_date_filter_var.get() else None
        category = self.category_var.get() or None

        transactions = self.db.get_transactions(start_date, end_date, category)

        for trans in transactions:
            amount_str = f"${trans['amount']:.2f}"
            if trans['amount'] < 0:
                amount_str = f"-${abs(trans['amount']):.2f}"
            
            self.tree.insert('', 'end', values=(
                trans['date'],
                trans['description'],
                amount_str,
                trans['category'] or '',
                trans['account'] or '',
                trans['notes'] or ''
            ), tags=(trans['id'],))
    
    def toggle_date_filter(self):
        state = 'normal' if self.use_date_filter_var.get() else 'disabled'
        self.start_date_picker.configure(state=state)
        self.end_date_picker.configure(state=state)
        self.refresh_transactions()

    def clear_filters(self):
        self.use_date_filter_var.set(False)
        self.start_date_picker.set_date(datetime.now())
        self.end_date_picker.set_date(datetime.now())
        self.start_date_picker.configure(state='disabled')
        self.end_date_picker.configure(state='disabled')
        self.category_var.set('')
        self.refresh_transactions()

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        if column == 'Amount':
            items.sort(key=lambda x: float(x[0].replace('$', '').replace(',', '').replace('-', '-')), reverse=self.sort_reverse)
        elif column == 'Date':
            items.sort(key=lambda x: x[0], reverse=self.sort_reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def add_transaction(self):
        TransactionDialog(self.frame, self.db, callback=self.refresh_transactions)

    def edit_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a transaction to edit")
            return

        transaction_id = self.tree.item(selection[0])['tags'][0]
        transactions = self.db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)

        if transaction:
            TransactionDialog(self.frame, self.db, transaction=transaction, callback=self.refresh_transactions)

    def delete_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select transaction(s) to delete")
            return

        count = len(selection)
        message = f"Are you sure you want to delete {count} transaction(s)?"

        if messagebox.askyesno("Confirm", message):
            for item in selection:
                transaction_id = self.tree.item(item)['tags'][0]
                self.db.delete_transaction(transaction_id)
            self.refresh_transactions()

    def on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)

        if not row_id:
            return

        column_index = int(column.replace('#', '')) - 1
        column_names = ['Date', 'Description', 'Amount', 'Category', 'Account', 'Notes']
        column_name = column_names[column_index]

        if column_name not in ['Description', 'Amount', 'Category', 'Account', 'Notes']:
            return

        entry_id = self.tree.item(row_id)['tags'][0]
        current_value = self.tree.item(row_id)['values'][column_index]

        x, y, width, height = self.tree.bbox(row_id, column)

        if column_name in ['Category', 'Account']:
            self.edit_cell_combobox(row_id, column_name, column_index, entry_id, current_value, x, y, width, height)
        else:
            self.edit_cell_entry(row_id, column_name, column_index, entry_id, current_value, x, y, width, height)

    def edit_cell_entry(self, row_id, column_name, column_index, entry_id, current_value, x, y, width, height):
        if column_name == 'Amount':
            current_value = str(current_value).replace('$', '').replace(',', '')

        edit_var = tk.StringVar(value=current_value)
        edit_entry = ttk.Entry(self.tree, textvariable=edit_var)
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.focus_set()
        edit_entry.select_range(0, tk.END)

        def save_edit(event=None):
            new_value = edit_var.get()
            edit_entry.destroy()
            self.update_transaction_field(entry_id, column_name, new_value)

        def cancel_edit(event=None):
            edit_entry.destroy()

        edit_entry.bind('<Return>', save_edit)
        edit_entry.bind('<Escape>', cancel_edit)
        edit_entry.bind('<FocusOut>', save_edit)

    def edit_cell_combobox(self, row_id, column_name, column_index, entry_id, current_value, x, y, width, height):
        edit_var = tk.StringVar(value=current_value)
        edit_combo = ttk.Combobox(self.tree, textvariable=edit_var)

        if column_name == 'Category':
            categories = self.db.get_categories()
            edit_combo['values'] = [cat['name'] for cat in categories]
        elif column_name == 'Account':
            accounts = self.db.get_accounts()
            edit_combo['values'] = [acc['name'] for acc in accounts]

        edit_combo.place(x=x, y=y, width=width, height=height)
        edit_combo.focus_set()

        def save_edit(event=None):
            if edit_combo.winfo_exists():
                new_value = edit_var.get()
                edit_combo.destroy()
                self.update_transaction_field(entry_id, column_name, new_value)

        def cancel_edit(event=None):
            if edit_combo.winfo_exists():
                edit_combo.destroy()

        edit_combo.bind('<<ComboboxSelected>>', save_edit)
        edit_combo.bind('<Return>', save_edit)
        edit_combo.bind('<Escape>', cancel_edit)

    def update_transaction_field(self, transaction_id, field_name, new_value):
        transactions = self.db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)

        if not transaction:
            return

        try:
            if field_name == 'Description':
                transaction['description'] = new_value
            elif field_name == 'Amount':
                transaction['amount'] = float(new_value)
            elif field_name == 'Category':
                transaction['category'] = new_value
            elif field_name == 'Account':
                transaction['account'] = new_value
            elif field_name == 'Notes':
                transaction['notes'] = new_value

            transaction_type = 'income' if transaction['amount'] > 0 else 'expense'

            self.db.update_transaction(
                transaction_id=transaction_id,
                date=transaction['date'],
                description=transaction['description'],
                amount=transaction['amount'],
                category=transaction['category'],
                account=transaction['account'],
                transaction_type=transaction_type,
                notes=transaction.get('notes', '')
            )

            self.refresh_transactions()
        except ValueError:
            messagebox.showerror("Error", "Invalid value entered")

class TransactionDialog:
    def __init__(self, parent, db: DatabaseManager, transaction=None, callback=None):
        self.db = db
        self.transaction = transaction
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Transaction" if not transaction else "Edit Transaction")
        self.dialog.geometry("400x400")
        self.dialog.transient(parent)
        
        ttk.Label(self.dialog, text="Date:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        if transaction:
            date_obj = datetime.strptime(transaction['date'], '%Y-%m-%d')
        else:
            date_obj = datetime.now()
        self.date_picker = DateEntry(self.dialog, width=18, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                    maxdate=datetime.now(), year=date_obj.year,
                                    month=date_obj.month, day=date_obj.day)
        self.date_picker.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Description:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.desc_var = tk.StringVar(value=transaction['description'] if transaction else '')
        ttk.Entry(self.dialog, textvariable=self.desc_var).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Amount:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.amount_var = tk.StringVar(value=str(transaction['amount']) if transaction else '')
        ttk.Entry(self.dialog, textvariable=self.amount_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Category:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.category_var = tk.StringVar(value=transaction['category'] if transaction else '')
        category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var)
        categories = self.db.get_categories()
        category_combo['values'] = [cat['name'] for cat in categories]
        category_combo.grid(row=3, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Account:").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.account_var = tk.StringVar(value=transaction['account'] if transaction else '')
        account_combo = ttk.Combobox(self.dialog, textvariable=self.account_var)
        accounts = self.db.get_accounts()
        account_combo['values'] = [acc['name'] for acc in accounts]
        account_combo.grid(row=4, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Notes:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=transaction['notes'] if transaction and transaction['notes'] else '')
        ttk.Entry(self.dialog, textvariable=self.notes_var).grid(row=5, column=1, padx=10, pady=10, sticky='ew')
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)
        
        self.dialog.columnconfigure(1, weight=1)

        center_window(self.dialog)
        self.dialog.deiconify()
        self.dialog.grab_set()
    
    def save(self):
        try:
            amount = float(self.amount_var.get())
            transaction_type = 'income' if amount > 0 else 'expense'
            
            if self.transaction:
                self.db.update_transaction(
                    self.transaction['id'],
                    date=self.date_picker.get(),
                    description=self.desc_var.get(),
                    amount=amount,
                    category=self.category_var.get(),
                    account=self.account_var.get(),
                    transaction_type=transaction_type,
                    notes=self.notes_var.get()
                )
            else:
                self.db.add_transaction(
                    date=self.date_picker.get(),
                    description=self.desc_var.get(),
                    amount=amount,
                    category=self.category_var.get(),
                    account=self.account_var.get(),
                    transaction_type=transaction_type,
                    notes=self.notes_var.get()
                )
            
            if self.callback:
                self.callback()
            
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
