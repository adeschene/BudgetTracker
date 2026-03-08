import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from decimal import Decimal, InvalidOperation
from utils.editable_tree import EditableTree
from database.db_manager import DatabaseManager
from utils.csv_importer import CSVImporter, ImportDialog
from utils.import_template_manager import ImportTemplateManager
from utils.helpers import center_window, fuzzy_match, exact_match, validate_money_string, DP_COLORS

class TransactionsTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs) # Initialize tab frame
        # Database manager and reference to parent and top-level root
        self.db = db
        self.parent = parent
        self.root = parent.winfo_toplevel()
        self.csv_importer = CSVImporter(self.db) # CSV import helper

        # Sorting state
        self.sort_column = None
        self.sort_reverse = False

        # Build UI and populate data
        self.setup_ui()
    
    def setup_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(padx=10, pady=10)

        ttk.Label(top_frame, text="Filters:").pack(side='left', padx=5)

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        #ttk.Label(top_frame, text='Period:').pack(side='left', padx=5)
        self.period_var = tk.StringVar(value='All Time')
        period_combo = ttk.Combobox(top_frame, textvariable=self.period_var, width=11, state='readonly')
        period_combo['values'] = ['This Month', 'Last Month', 'Last Two Months', 'Last Three Months', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.on_period_change())

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        ttk.Label(top_frame, text="Start:").pack(side='left', padx=(5,0))
        self.start_date_picker = DateEntry(top_frame, width=10, firstweekday='sunday',
                                        background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                        headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                        othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                        weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                        othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                        normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                        disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                        bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now(), day=1)
        self.start_date_picker.pack(side='left', padx=5)
        self.start_date_picker.bind("<<DateEntrySelected>>", lambda e: self.refresh_transactions())

        ttk.Label(top_frame, text="End:").pack(side='left', padx=(5,0))
        self.end_date_picker = DateEntry(top_frame, width=10, firstweekday='sunday',
                                        background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                        headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                        othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                        weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                        othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                        normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                        disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                        bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=5)
        self.end_date_picker.bind("<<DateEntrySelected>>", lambda e: self.refresh_transactions())

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        # Filter by category
        ttk.Label(top_frame, text="Category:").pack(side='left', padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top_frame, textvariable=self.category_var, width=12, state='readonly')
        self.category_combo.pack(side='left', padx=5)
        self.update_category_list()
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_transactions())

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        # Filter by keyword in description (exact or fuzzy match)
        ttk.Label(top_frame, text='Keyword:').pack(side='left', padx=(4, 6))
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(top_frame, textvariable=self.keyword_var, width=10)
        self.keyword_entry.pack(side='left', padx=5)
        self.keyword_entry.bind('<KeyRelease>', lambda e: self.refresh_transactions())

        self.search_label_var = tk.StringVar(value='Exact')

        # Exact match enabled by default; fuzzy match optional with configurable threshold
        self.use_exact_keyword_filter_var = tk.BooleanVar(value=True)
        exact_filter_check = ttk.Checkbutton(top_frame, style='Switch',
                                          variable=self.use_exact_keyword_filter_var,
                                          command=self.toggle_search_method)
        exact_filter_check.pack(side='left', padx=(5,0))
        exact_filter_label = ttk.Label(top_frame, textvariable=self.search_label_var, width=6)
        exact_filter_label.pack(side='left')

        # Fuzzy threshold control (disabled unless fuzzy match enabled)
        self.fuzzy_threshold_var = tk.DoubleVar(value=0.9)
        self.fuzzy_threshold_scale = ttk.Scale(top_frame, from_=0.1, to=1.0, orient='horizontal', variable=self.fuzzy_threshold_var)
        self.fuzzy_threshold_scale.pack(side='left', padx=(3, 5))
        self.fuzzy_threshold_scale.configure(length=55, state='disabled')
        self.fuzzy_threshold_label = ttk.Label(top_frame, text=f'Threshold: {self.fuzzy_threshold_var.get():.2f}')
        self.fuzzy_threshold_label.pack(side='left', padx=(4, 0))

        def _update_threshold_label(val):
            try:
                self.fuzzy_threshold_label.config(text=f'Threshold: {float(val):.2f}')
            except Exception:
                pass

        self.fuzzy_threshold_scale.configure(command=_update_threshold_label)
        self.fuzzy_threshold_scale.bind('<ButtonRelease-1>', lambda e: self.refresh_transactions())

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=10, pady=2)

        # Filter clear button
        ttk.Button(top_frame, text="Clear", command=self.clear_filters).pack(side='left', padx=5)
        
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Main treeview showing transactions with clickable column headers
        self.tree = EditableTree(tree_frame, columns=('Date', 'Description', 'Amount', 'Category', 'Account', 'Notes'),
                    editable_columns=['Description', 'Amount', 'Category', 'Account', 'Notes'],
                    on_commit_callback=self.handle_db_update, get_options_callback=self.get_dd_values,
                    get_validation_callback=self.provide_validation, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Date', text='Date', command=lambda: self.sort_by_column('Date'))
        self.tree.heading('Description', text='Description', command=lambda: self.sort_by_column('Description'))
        self.tree.heading('Amount', text='Amount', command=lambda: self.sort_by_column('Amount'))
        self.tree.heading('Category', text='Category', command=lambda: self.sort_by_column('Category'))
        self.tree.heading('Account', text='Account', command=lambda: self.sort_by_column('Account'))
        self.tree.heading('Notes', text='Notes', command=lambda: self.sort_by_column('Notes'))

        self.tree.column('Date', width=60, anchor='center')
        self.tree.column('Description', width=150)
        self.tree.column('Amount', width=60, anchor='center')
        self.tree.column('Category', width=60, anchor='center')
        self.tree.column('Account', width=60, anchor='center')
        self.tree.column('Notes', width=100)

        self.tree.pack(fill='both', expand=True)
        
        self.tree.bind("<Delete>", lambda e: self.delete_transaction()) # Enable delete key to remove items
        
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=5)
        
        # Define grid columns: Col 0 (Left spacer), Col 1 (Tabs), Col 2 (Buttons)
        button_frame.columnconfigure(0, weight=1, uniform='group1') # Left spacer
        button_frame.columnconfigure(1, weight=0) # Centered button container (shrink to fit)
        button_frame.columnconfigure(2, weight=1, uniform='group1') # Right container for count

        center_btn_container = ttk.Frame(button_frame)
        center_btn_container.grid(row=0, column=1)

        # Action buttons
        ttk.Button(center_btn_container, text="Import CSV", style='Accent.TButton', command=self.import_csv).pack(side='left', padx=(0,5))
        ttk.Button(center_btn_container, text="Manage Templates", command=self.manage_import_templates).pack(side='left', padx=5)

        ttk.Separator(center_btn_container, orient='vertical').pack(side='left', fill='y', padx=10, pady=2)

        ttk.Button(center_btn_container, text="Add Transaction", style='Accent.TButton', command=self.add_transaction).pack(side='left', padx=5)
        ttk.Button(center_btn_container, text="Edit Transaction", command=self.edit_transaction).pack(side='left', padx=5)
        ttk.Button(center_btn_container, text="Delete Transaction", command=self.delete_transaction).pack(side='left', padx=(5,0))

        # Small container frame for the buttons to keep them together on the right
        count_container = ttk.Frame(button_frame)
        count_container.grid(row=0, column=2, sticky='e', padx=16)

        # Display current transaction count to user
        self.count_var = tk.StringVar()
        self.count_label = ttk.Label(count_container, textvariable=self.count_var, style='Count.TLabel', width=14, anchor='e')
        self.count_label.pack(side='left')
        ttk.Label(count_container, text=' Transactions', style='Count.TLabel').pack(side='left')

    def on_tab_opened(self): # Trigger refresh when switching to tab from another
        # Update category list in filters combobox, assuming they may have been changed
        self.update_category_list()
        self.refresh_transactions()

    # Enable date pickers when using custom timeframe
    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='readonly')
            self.end_date_picker.config(state='readonly')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        self.refresh_transactions()

    def manage_import_templates(self):
        ImportTemplateManager(self, self.db)
    
    def update_category_list(self):
        categories = self.db.get_categories()
        category_names = [''] + [cat['name'] for cat in categories]
        self.category_combo['values'] = category_names
        self.category_combo.set('') # Reset selection to blank when category list is updated

    # Report timeframe picker logic
    def get_date_range(self):
        period = self.period_var.get()
        today = datetime.now()

        match period:
            case 'This Month':
                start = today.replace(day=1)
                end = today
            case 'Last Month':
                first_this_month = today.replace(day=1)
                end = first_this_month - timedelta(days=1)
                start = end.replace(day=1)
            case 'Last Two Months':
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                start = last_month_end.replace(day=1)
                end = today
            case 'Last Three Months':
                this_month = today.month
                this_year = today.year
                match this_month:
                    case 2: start_month = 12
                    case 1: start_month = 11
                    case _: start_month = this_month - 2
                start_year = this_year - 1 if start_month == 12 or 11 else this_year
                start = today.replace(year=start_year, month=start_month, day=1)
                end = today
            case 'This Year':
                start = today.replace(month=1, day=1)
                end = today
            case 'Last Year':
                start = today.replace(year=today.year-1, month=1, day=1)
                end = today.replace(year=today.year-1, month=12, day=31)
            case 'Custom':
                start = self.start_date_picker.get_date()
                end = self.end_date_picker.get_date()
            case _: # All Time chosen, show everything
                return None, None

        # Return start and end dates as ISO strings for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    def refresh_transactions(self):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Prepare filter arguments
        start_date, end_date = self.get_date_range()
        category = self.db.get_category_id_by_name(self.category_var.get()) or None

        # Fetch transactions from DB and insert into the treeview
        transactions = self.db.get_transactions(start_date, end_date, category)

        keyword = self.keyword_var.get().strip()

        if keyword != '':
            # Filter by exact or fuzzy match on description based on checkbox
            search_exact = self.use_exact_keyword_filter_var.get()
            if search_exact:
                filtered = [t for t in transactions if exact_match(keyword, t.get('description', ''))]
            else:
                thresh = float(self.fuzzy_threshold_var.get())
                filtered = [t for t in transactions if fuzzy_match(keyword, t.get('description', ''), threshold=thresh)]
        else:
            filtered = transactions

        # Update transaction count label
        self.count_var.set(f'{len(filtered):,}')

        for trans in filtered:
            # Format amount for display, show negative amounts with a leading '-'
            if trans['amount'] < 0:
                amount_str = f"-${abs(Decimal(trans['amount'])/100):.2f}"
            else:
                amount_str = f"${Decimal(trans['amount'])/100:.2f}"

            # Display dates in mm-dd-yyyy format
            converted_date = datetime.strptime(trans['date'],"%Y-%m-%d").strftime("%m-%d-%Y")
            
            # Store transaction id in tags for later edits/deletes
            self.tree.insert('', 'end', values=(
                converted_date,
                trans['description'],
                amount_str,
                self.db.get_category_name_by_id(trans['category_id']) or '',
                self.db.get_account_name_by_id(trans['account_id']) or '',
                trans['notes'] or ''
            ), tags=(trans['id'],))
        self.apply_current_sort()
    
    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        # If user selected a file, open the import dialog which handles mapping
        if not file_path:
            return

        dialog = ImportDialog(self.root, self.db, self.csv_importer, file_path)
        # Wait for the import dialog to close before continuing
        self.root.wait_window(dialog.dialog)

        if dialog.success:
            # Refresh the transactions view and inform the user
            self.refresh_transactions()
            messagebox.showinfo("Success", f"Imported {dialog.count} transactions")

    def toggle_search_method(self):
        state = 'disabled' if self.use_exact_keyword_filter_var.get() else 'normal'
        self.fuzzy_threshold_scale.configure(state=state)
        self.search_label_var.set('Exact' if state == 'disabled' else 'Fuzzy')
        self.refresh_transactions()

    def clear_filters(self):
        self.period_var.set('All Time')
        self.start_date_picker.set_date(datetime.now())
        self.end_date_picker.set_date(datetime.now())
        self.start_date_picker.configure(state='disabled')
        self.end_date_picker.configure(state='disabled')
        self.category_var.set('')
        self.keyword_var.set('')
        self.use_exact_keyword_filter_var.set(True)
        self.fuzzy_threshold_scale.configure(state='disabled')
        self.search_label_var.set('Exact')
        self.fuzzy_threshold_var.set(0.9)
        self.fuzzy_threshold_label.config(text=f'Threshold: {float(self.fuzzy_threshold_var.get()):.2f}')
        self.refresh_transactions()

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Build a list of (value, item_id) tuples for sorting
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        # Choose sorting strategy depending on column type
        if column == 'Amount':
            # Parse formatted currency strings back to floats for numeric sort
            items.sort(key=lambda x: Decimal(x[0].replace('$', '').replace(',', '').replace('-', '-')), reverse=self.sort_reverse)
        elif column == 'Date':
            items.sort(key=lambda x: datetime.strptime(x[0], "%m-%d-%Y"), reverse=self.sort_reverse)
        else:
            # Case-insensitive string sort for other columns
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        # Reorder the tree items according to sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def apply_current_sort(self):
        if not self.sort_column:
            return

        # Build a list of (value, item_id) tuples for sorting
        items = [(self.tree.set(item, self.sort_column), item) for item in self.tree.get_children('')]

        # Choose sorting strategy depending on column type
        if self.sort_column == 'Amount':
            # Parse formatted currency strings back to floats for numeric sort
            items.sort(key=lambda x: Decimal(x[0].replace('$', '').replace(',', '').replace('-', '-')), reverse=self.sort_reverse)
        elif self.sort_column == 'Date':
            items.sort(key=lambda x: datetime.strptime(x[0], "%m-%d-%Y"), reverse=self.sort_reverse)
        else:
            # Case-insensitive string sort for other columns
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        # Reorder the tree items according to sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def add_transaction(self):
        # Open a dialog to add a new transaction; refresh on save
        TransactionDialog(self, self.db, callback=self.refresh_transactions)

    def edit_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a transaction to edit")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Error", "Only one transaction can be edited at a time")
            return

        transaction_id = self.tree.item(selection[0])['tags'][0]
        transactions = self.db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)

        if transaction:
            # Edit the selected transaction using the dialog
            TransactionDialog(self, self.db, transaction=transaction, callback=self.refresh_transactions)

    def delete_transaction(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select transaction(s) to delete")
            return

        count = len(selection)
        message = f"Delete {count} transactions?" if count > 1 else "Delete this transaction?"

        if messagebox.askyesno("Confirm", message):
            # Delete each selected transaction and refresh view
            for item in selection:
                transaction_id = self.tree.item(item)['tags'][0]
                self.db.delete_transaction(transaction_id)
            self.refresh_transactions()

    def provide_validation(self, column_name):
        if column_name == 'Amount':
            return (validate_money_string, 'True', 'True')
        return None

    def get_dd_values(self, column_name):
        # Provides values for inline combobox editing
        if column_name == 'Category':
            categories = self.db.get_categories()
            return [cat['name'] for cat in categories]
        elif column_name == 'Account':
            accounts = self.db.get_accounts()
            return [acc['name'] for acc in accounts]
        return None # Entry field
    
    def handle_db_update(self, row_id, column_name, new_value):
        # Get db ID from tags
        entry_id = self.tree.item(row_id)['tags'][0]
        self.update_transaction_field(entry_id, column_name, new_value)

    def update_transaction_field(self, transaction_id, field_name, new_value):
        transactions = self.db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        if not transaction:
            return

        try:
            # Update the in-memory transaction dict then persist
            if field_name == 'Description':
                if not new_value:
                    messagebox.showerror("Error", "Description is required")
                    return
                transaction['description'] = new_value
            elif field_name == 'Amount':
                transaction['amount'] = int(Decimal(new_value)*100)  # Convert from Decimal to int
            elif field_name == 'Category':
                transaction['category_id'] = self.db.get_category_id_by_name(new_value)
            elif field_name == 'Account':
                transaction['account_id'] = self.db.get_account_id_by_name(new_value)
            elif field_name == 'Notes':
                transaction['notes'] = new_value

            # Determine transaction type from amount sign and persist changes
            transaction_type = 'income' if Decimal(transaction['amount']) > 0 else 'expense'

            self.db.update_transaction(
                transaction_id=transaction_id,
                date=transaction['date'],
                description=transaction['description'],
                amount=transaction['amount'],
                category_id=transaction['category_id'],
                account_id=transaction['account_id'],
                transaction_type=transaction_type,
                notes=transaction.get('notes', '')
            )

            # Refresh view to show updated values
            self.refresh_transactions()
        except (ValueError, InvalidOperation):
            messagebox.showerror("Error", "Invalid value entered")

class TransactionDialog:
    def __init__(self, parent, db: DatabaseManager, transaction=None, callback=None):
        self.db = db
        self.transaction = transaction
        self.callback = callback
        
        # Dialog used to add or edit a single transaction record
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Transaction" if not transaction else "Edit Transaction")
        self.dialog.geometry("400x420")
        self.dialog.transient(parent)
        
        vcmd_decimal_dollar = (self.dialog.register(validate_money_string), "%P", True, True) # Digit validation registration
        
        ttk.Label(self.dialog, text="Date:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        if transaction:
            date_obj = datetime.strptime(transaction['date'], '%Y-%m-%d')
        else:
            date_obj = datetime.now()
        self.date_picker = DateEntry(self.dialog, width=18, firstweekday='sunday',
                                    background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                    headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                    othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                    weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                    othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                    normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                    disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                    bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                    maxdate=datetime.now(), year=date_obj.year,
                                    month=date_obj.month, day=date_obj.day, state='readonly')
        self.date_picker.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Description:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.desc_var = tk.StringVar(value=transaction['description'] if transaction else '')
        ttk.Entry(self.dialog, textvariable=self.desc_var).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Amount:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.amount_var = tk.StringVar(value=str(Decimal(transaction['amount'])/100) if transaction else '') # Convert to decimal
        ttk.Entry(self.dialog, validate='all', validatecommand=vcmd_decimal_dollar, textvariable=self.amount_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        tk.Label(self.dialog, text='Please enter negative values for expenses\n(purchases, withdrawals, etc.)', fg='gray').grid(row=3, column=1, padx=5, sticky='ew')
        
        ttk.Label(self.dialog, text="Category:").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.category_var = tk.StringVar(value=self.db.get_category_name_by_id(transaction['category_id']) if transaction else '')
        category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var, state='readonly')
        categories = self.db.get_categories()
        category_combo['values'] = [cat['name'] for cat in categories]
        category_combo.grid(row=4, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Account:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.account_var = tk.StringVar(value=self.db.get_account_name_by_id(transaction['account_id']) if transaction else '')
        account_combo = ttk.Combobox(self.dialog, textvariable=self.account_var, state='readonly')
        accounts = self.db.get_accounts()
        account_combo['values'] = [acc['name'] for acc in accounts]
        account_combo.grid(row=5, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Notes:").grid(row=6, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=transaction['notes'] if transaction and transaction['notes'] else '')
        ttk.Entry(self.dialog, textvariable=self.notes_var).grid(row=6, column=1, padx=10, pady=10, sticky='ew')
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)
        
        self.dialog.columnconfigure(1, weight=1)

        center_window(self.dialog)
        self.dialog.deiconify()
        self.dialog.grab_set()
    
    def save(self):
        try:
            amount = int(Decimal(self.amount_var.get()) * 100) # Convert from decimal
            transaction_type = 'income' if amount > 0 else 'expense'
            description = self.desc_var.get()

            if not description: # Make sure transaction has a description
                messagebox.showerror("Error", "Description is required")
                return
            if self.transaction:
                self.db.update_transaction(
                    self.transaction['id'],
                    date=self.date_picker.get_date(),
                    description=description,
                    amount=amount,
                    category_id=self.db.get_category_id_by_name(self.category_var.get()),
                    account_id=self.db.get_account_id_by_name(self.account_var.get()),
                    transaction_type=transaction_type,
                    notes=self.notes_var.get()
                )
            else:
                self.db.add_transaction(
                    date=self.date_picker.get_date(),
                    description=description,
                    amount=amount,
                    category_id=self.db.get_category_id_by_name(self.category_var.get()),
                    account_id=self.db.get_account_id_by_name(self.account_var.get()),
                    transaction_type=transaction_type,
                    notes=self.notes_var.get()
                )
            
            if self.callback:
                self.callback()
            
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
