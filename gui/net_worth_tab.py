import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from calendar import monthrange
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager
from utils.editable_tree import EditableTree
from utils.helpers import center_window, validate_money_string, DP_COLORS

class NetWorthTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs) # Initialize tab frame
        self.db = db

        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year

        self.asset_types = ['Cash', 'Checking', 'Savings', 'Investment', 'Real Estate', 'Vehicle', 'Other Asset', 'Credit Card', 'Loan', 'Other Liability']

        # Sorting state
        self.sort_column = None
        self.sort_reverse = False

        self.setup_ui()

    def setup_ui(self):
        month_selector_frame = ttk.Frame(self)
        month_selector_frame.pack(fill='x', padx=10, pady=10)

        centered_container = ttk.Frame(month_selector_frame)
        centered_container.pack(expand=True, pady=(12,0))

        ttk.Button(centered_container, text="◀", width=3, style='Big.Accent.TButton', command=self.previous_month).pack(side='left', padx=(0,2))

        self.month_label = tk.Label(centered_container, text="", font=('Roboto', 14, 'bold'), width=14, anchor='center')
        self.month_label.pack(side='left', padx=0)

        ttk.Button(centered_container, text="▶", width=3, style='Big.Accent.TButton', command=self.next_month).pack(side='left', padx=2)

        ttk.Button(centered_container, text="⭮", width=3, style='Big.TButton', command=self.go_to_current_month).pack(side='left', padx=(10,0))

        self.update_month_label()

        summary_frame = ttk.Labelframe(self, text="Net Worth Summary", labelanchor='n')
        summary_frame.pack(fill='x', padx=10, pady=10)

        self.total_label = tk.Label(summary_frame, text="Total Net Worth: $0",
                                    font=('Roboto', 16, 'bold'), fg='#217346')
        self.total_label.pack(pady=10)

        breakdown_frame = ttk.Frame(summary_frame)
        breakdown_frame.pack(fill='x', padx=20, pady=(0,10))

        self.breakdown_text = tk.Text(breakdown_frame, height=5, width=30, relief='ridge', padx=4, pady=4, state='disabled')
        self.breakdown_text.pack()

        entries_frame = ttk.Labelframe(self, text="Net Worth Entries for Selected Month", labelanchor='n')
        entries_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_frame = ttk.Frame(entries_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.tree = EditableTree(tree_frame, columns=('Date', 'Asset', 'Type', 'Value', 'Notes'), editable_columns=['Asset', 'Type', 'Value', 'Notes'],
                    on_commit_callback=self.handle_db_update, get_options_callback=self.get_dd_values, get_validation_callback=self.provide_validation,
                    show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Date', text='Date', command=lambda: self.sort_by_column('Date'))
        self.tree.heading('Asset', text='Asset/Liability Name', command=lambda: self.sort_by_column('Asset'))
        self.tree.heading('Type', text='Type', command=lambda: self.sort_by_column('Type'))
        self.tree.heading('Value', text='Value', command=lambda: self.sort_by_column('Value'))
        self.tree.heading('Notes', text='Notes', command=lambda: self.sort_by_column('Notes'))

        self.tree.column('Date', width=100, anchor='center')
        self.tree.column('Asset', width=200, anchor='center')
        self.tree.column('Type', width=150, anchor='center')
        self.tree.column('Value', width=120, anchor='center')
        self.tree.column('Notes', width=200)

        self.tree.pack(fill='both', expand=True)
        
        self.tree.bind("<Delete>", lambda e: self.delete_entry()) # Enable delete key to remove items

        button_frame = ttk.Frame(entries_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Apply Template", style='Accent.TButton', command=self.apply_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Manage Template", command=self.manage_templates).pack(side='left', padx=5)

        ttk.Separator(button_frame, orient='vertical').pack(side='left', fill='y', padx=10, pady=2)

        ttk.Button(button_frame, text="Add Entry", style='Accent.TButton', command=self.add_entry).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Entry", command=self.edit_entry).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Entry", command=self.delete_entry).pack(side='left', padx=5)

    def on_tab_opened(self): # Trigger refresh when switching to tab from another
        self.refresh_data()

    def update_month_label(self):
        month_name = datetime(self.current_year, self.current_month, 1).strftime('%B %Y')
        self.month_label.config(text=month_name)

    def previous_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_month_label()
        self.refresh_data()

    def next_month(self):
        now = datetime.now()
        # Don't allow navigating beyond current month
        if self.current_year > now.year or (self.current_year == now.year and self.current_month >= now.month):
            return

        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_month_label()
        self.refresh_data()

    def go_to_current_month(self):
        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year
        self.update_month_label()
        self.refresh_data()

    def get_month_date_range(self):
        start_date = f"{self.current_year}-{self.current_month:02d}-01"
        last_day = monthrange(self.current_year, self.current_month)[1]
        end_date = f"{self.current_year}-{self.current_month:02d}-{last_day:02d}"
        return start_date, end_date
    
    def refresh_data(self):
        # Reload entries for the currently selected month and display summary
        for item in self.tree.get_children():
            self.tree.delete(item)

        start_date, end_date = self.get_month_date_range()

        entries = self.db.get_net_worth_entries(start_date, end_date)

        for entry in entries:
            # Display positive values as $value and negatives as -$value
            if entry['value'] < 0:
                value_str = f"-${abs(entry['value']):,}"
            else:
                value_str = f"${entry['value']:,}"

            # Display dates in mm-dd-yyyy format
            converted_date = datetime.strptime(entry['date'],"%Y-%m-%d").strftime("%m-%d-%Y")

            display_values = [
                converted_date,
                entry['asset_name'],
                entry['asset_type'] or '',
                value_str,
                entry['notes'] or ''
            ]

            # Store entry id in tags for edits/deletes
            self.tree.insert('', 'end', values=display_values, tags=(entry['id'],))

        # Build a summary grouping by asset type for the small summary box
        summary = self.db.get_net_worth_summary(start_date, end_date)
        total = sum(summary.values())

        self.total_label.config(text=f"Total Net Worth: ${total:,}")

        self.breakdown_text.config(state='normal')
        self.breakdown_text.delete('1.0', 'end')

        if summary:
            for asset_type, value in summary.items():
                self.breakdown_text.insert('end', f"{asset_type}: {'-' if value < 0 else ''}${abs(value):,}\n")
        else:
            self.breakdown_text.insert('end', "No entries yet")

        self.breakdown_text.config(state='disabled')

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Build a list of (value, item_id) tuples for sorting
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        # Choose sorting strategy depending on column type
        if column == 'Value':
            # Parse formatted currency strings back to ints for numeric sort
            items.sort(key=lambda x: int(x[0].replace('$', '').replace(',', '').replace('-', '-')), reverse=self.sort_reverse)
        elif column == 'Date':
            items.sort(key=lambda x: x[0], reverse=self.sort_reverse)
        else:
            # Case-insensitive string sort for other columns
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        # Reorder the tree items according to sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)

    def add_entry(self):
        start_date, end_date = self.get_month_date_range()
        NetWorthDialog(self, self.db, callback=self.refresh_data, start_date=start_date, end_date=end_date,
                      default_month=self.current_month, default_year=self.current_year)

    def edit_entry(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to edit")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Error", "Only one entry can be edited at a time")
            return

        entry_id = self.tree.item(selection[0])['tags'][0]
        start_date, end_date = self.get_month_date_range()
        entries = self.db.get_net_worth_entries(start_date, end_date)
        entry = next((e for e in entries if e['id'] == entry_id), None)

        if entry:
            NetWorthDialog(self, self.db, entry=entry, callback=self.refresh_data, start_date=start_date, end_date=end_date,
                          default_month=self.current_month, default_year=self.current_year)

    def delete_entry(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select entry(s) to delete")
            return

        count = len(selection)
        message = f"Delete {count} entries?" if count > 1 else "Delete this entry?"

        if messagebox.askyesno("Confirm", message):
            for item in selection:
                entry_id = self.tree.item(item)['tags'][0]
                self.db.delete_net_worth_entry(entry_id)
            self.refresh_data()

    def apply_template(self):
        templates = self.db.get_asset_templates()

        if not templates:
            messagebox.showinfo("No Templates", "No templates found. Please create templates first using 'Manage Templates'.")
            return

        start_date, end_date = self.get_month_date_range()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT asset_name FROM net_worth_entries
            WHERE date >= ? AND date <= ?
        ''', (start_date, end_date))
        existing_assets = {row[0] for row in cursor.fetchall()}
        conn.close()

        # Filter templates to only ones not already present for the month
        templates_to_add = [t for t in templates if t['asset_name'] not in existing_assets]

        if not templates_to_add:
            messagebox.showinfo("Already Applied",
                              f"All templates have already been added to {datetime(self.current_year, self.current_month, 1).strftime('%B %Y')}")
            return

        # Open a dialog to enter initial values and apply selected templates
        ApplyTemplateDialog(self, self.db, templates_to_add, self.current_year, self.current_month, self.refresh_data)

    def manage_templates(self):
        TemplateManagerDialog(self, self.db, asset_types=self.asset_types)

    def provide_validation(self, column_name):
        if column_name == 'Value':
            return (validate_money_string, 'True', 'False')
        return None
            
    def get_dd_values(self, column_name):
        # Provides values for inline combobox editing
        if column_name == 'Type':
            return self.asset_types
        return None # Entry field
    
    def handle_db_update(self, row_id, column_name, new_value):
        # Get db ID from tags
        entry_id = self.tree.item(row_id)['tags'][0]
        self.update_entry_field(entry_id, column_name, new_value)

    def update_entry_field(self, entry_id, field_name, new_value):
        start_date, end_date = self.get_month_date_range()
        entries = self.db.get_net_worth_entries(start_date, end_date)
        entry = next((e for e in entries if e['id'] == entry_id), None)
        if not entry:
            return

        try:
            # Update the in-memory category dict then persist
            if field_name == 'Asset':
                entry_names = [e['asset_name'].lower() for e in entries]
                if new_value.lower() != entry['asset_name'].lower() and new_value.lower() in entry_names:
                    messagebox.showerror("Error", "An entry already exists by that name")
                    return
                if not new_value:
                    messagebox.showerror("Error", "Entry name is required")
                    return
                entry['asset_name'] = new_value
            elif field_name == 'Type':
                entry['asset_type'] = new_value
            elif field_name == 'Value':
                entry['value'] = int(new_value)
            elif field_name == 'Notes':
                entry['notes'] = new_value

            self.db.update_net_worth_entry(
                entry_id=entry_id,
                date=entry['date'],
                asset_name=entry['asset_name'],
                value=entry['value'],
                asset_type=entry['asset_type'],
                notes=entry['notes']
            )
            # Refresh view to show updated values
            self.refresh_data()
        except (ValueError):
            messagebox.showerror("Error", "Invalid value entered")

class NetWorthDialog:
    def __init__(self, parent, db: DatabaseManager, entry=None, callback=None, start_date=None, end_date=None, default_month=None, default_year=None):
        self.db = db
        self.entry = entry
        self.callback = callback
        self.start_date = start_date
        self.end_date = end_date

        # Dialog for adding or editing a net worth entry (asset value)
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Net Worth Entry" if not entry else "Edit Net Worth Entry")
        self.dialog.geometry("400x370")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        vcmd_whole_dollars = (self.dialog.register(validate_money_string), "%P", True, False) # Digit validation registration

        if entry:
            default_date = entry['date']
        elif default_month and default_year:
            # default to the last day of the specified month rather than the first
            last_day = monthrange(default_year, default_month)[1]
            default_date = f"{default_year}-{default_month:02d}-{last_day:02d}"
        else:
            default_date = datetime.now().strftime('%Y-%m-%d')

        date_obj = datetime.strptime(default_date, '%Y-%m-%d')

        ttk.Label(self.dialog, text="Date:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.date_picker = DateEntry(self.dialog, width=18, firstweekday='sunday',
                                    background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                    headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                    othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                    weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                    othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                    normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                    disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                    bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                    maxdate=datetime.now(), year=date_obj.year, month=date_obj.month, day=date_obj.day, state='readonly')
        self.date_picker.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Asset Name:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.asset_var = tk.StringVar(value=entry['asset_name'] if entry else '')
        ttk.Entry(self.dialog, textvariable=self.asset_var).grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Asset Type:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=entry['asset_type'] if entry else 'Cash')
        type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, state='readonly')
        type_combo['values'] = ['Cash', 'Checking', 'Savings', 'Investment', 'Real Estate', 'Vehicle', 'Other Asset', 'Credit Card', 'Loan', 'Other Liability']
        type_combo.grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Value:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.value_var = tk.StringVar(value=str(entry['value']) if entry else '')
        ttk.Entry(self.dialog, validate='all', validatecommand=vcmd_whole_dollars, textvariable=self.value_var).grid(row=3, column=1, padx=10, pady=10, sticky='ew')
        tk.Label(self.dialog, text='Please enter negative values for liabilities\n(loans, credit card balances, etc.)', fg='gray').grid(row=4, column=1, padx=5, sticky='ew')

        ttk.Label(self.dialog, text="Notes:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=entry['notes'] if entry and entry['notes'] else '')
        ttk.Entry(self.dialog, textvariable=self.notes_var).grid(row=5, column=1, padx=10, pady=10, sticky='ew')

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    def on_closing(self):
        self.dialog.grab_release()
        self.dialog.destroy()

    def save(self):
        entries = self.db.get_net_worth_entries(self.start_date, self.end_date)
        entry_names = [n['asset_name'].lower() for n in entries]
        new_name = self.asset_var.get()
        try:
            # Persist the new or updated entry
            if self.entry:
                # Check for duplicate name before saving
                if new_name.lower() != self.entry['asset_name'].lower() and new_name.lower() in entry_names:
                    messagebox.showerror("Error", "An entry with that name already exists for this month")
                    return
                if not new_name:
                    messagebox.showerror("Error", "Entry name is required")
                    return
                self.db.update_net_worth_entry(
                    entry_id=self.entry['id'],
                    date=self.date_picker.get_date(),
                    asset_name=new_name,
                    asset_type=self.type_var.get(),
                    value=int(self.value_var.get()),
                    notes=self.notes_var.get()
                )
            else:
                # Check for duplicate name before saving
                if new_name.lower() in entry_names:
                    messagebox.showerror("Error", "An entry with that name already exists for this month")
                    return
                if not new_name:
                    messagebox.showerror("Error", "Entry name is required")
                    return
                self.db.add_net_worth_entry(
                    date=self.date_picker.get_date(),
                    asset_name=self.asset_var.get(),
                    asset_type=self.type_var.get(),
                    value=int(self.value_var.get()),
                    notes=self.notes_var.get()
                )

            if self.callback:
                self.callback()

            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid value entered")

class ApplyTemplateDialog:
    def __init__(self, parent, db: DatabaseManager, templates, year, month, callback):
        self.db = db
        self.templates = templates
        self.year = year
        self.month = month
        self.callback = callback
        self.value_vars = {}

        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title(f"Apply Templates to {datetime(year, month, 1).strftime('%B %Y')}")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        info_label = ttk.Label(self.dialog,
                             text="Enter values for each asset to add to this month:"
                             )
        info_label.pack(padx=10, pady=10)

        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        scrollable_frame = ttk.Frame(self.canvas)

        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        scrollable_frame.grid_columnconfigure(0, weight=1)

        container_id = self.canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(container_id, width=e.width))

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.dialog.bind_all("<MouseWheel>", self._on_mousewheel) # Bind to entire dialog
        # Future Linux support
        #self.dialog.bind_all("<Button-4>", self._on_mousewheel)
        #self.dialog.bind_all("<Button-5>", self._on_mousewheel)

        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for i, template in enumerate(templates):
            frame = ttk.LabelFrame(scrollable_frame, text=f" {template['asset_name']} ", style="NWTE.TLabelframe")
            frame.grid(row=i, column=0, sticky='ew', padx=10, pady=8, ipadx=5, ipady=5)

            frame.grid_columnconfigure(1, weight=1)

            ttk.Label(frame, text="Value:", font=('Roboto', 10, 'bold')).grid(row=0, column=0, padx=10, pady=20, sticky='w')

            vcmd_decimal_dollar = (frame.register(validate_money_string), "%P", True, False) # Digit validation registration

            value_var = tk.StringVar(value='')
            self.value_vars[template['id']] = value_var

            entry = ttk.Entry(frame, validate='key', validatecommand=vcmd_decimal_dollar, textvariable=value_var)
            entry.grid(row=0, column=1, padx=5, pady=20, sticky='w')
            
            type_text = f"Category: {template['asset_type'] or 'None'}"
            ttk.Label(frame, text=type_text, font=('Roboto', 9, 'italic')).grid(row=0, column=2, padx=20, sticky='e')

            if template['notes']:
                ttk.Label(frame, text=f"Note: {template['notes']}").grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky='w')

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Apply", style='Accent.TButton', command=self.apply, width=12).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy_dialog, width=12).pack(side='left', padx=5)

        self.dialog.protocol("WM_DELETE_WINDOW", self.destroy_dialog)

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    def _on_mousewheel(self, event):
        # Windows/macOS: use event.delta (Potential update: use event.num if Linux)
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def destroy_dialog(self):
        self.dialog.unbind_all("<MouseWheel>")
        self.dialog.destroy()

    def apply(self):
        try:
            template_values = {}
            for template_id, value_var in self.value_vars.items():
                value_str = value_var.get().strip()
                if value_str:
                    value = int(value_str)
                    template_values[template_id] = value

            if not template_values:
                messagebox.showwarning("Warning", "No values entered. Please enter at least one value to apply templates.")
                return

            self.db.apply_templates_to_month(self.year, self.month, template_values)

            if self.callback:
                self.callback()

            self.destroy_dialog()
            messagebox.showinfo("Success", f"Templates applied to {datetime(self.year, self.month, 1).strftime('%B %Y')}!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values for the assets you wish to apply")

class TemplateManagerDialog:
    def __init__(self, parent, db: DatabaseManager, asset_types):
        self.db = db
        self.asset_types = asset_types

        # Sorting state
        self.sort_column = None
        self.sort_reverse = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Manage Asset Template")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        info_label = tk.Label(self.dialog,
                             text="This template is used to quickly add recurring assets/liabilities to each month.\nClick 'Apply Template' in the Net Worth tab to add these to the current month.",
                             font=('Roboto', 9), fg='white', justify='left')
        info_label.pack(padx=10, pady=10, anchor='w')

        tree_frame = ttk.Frame(self.dialog)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.tree = EditableTree(tree_frame, columns=('Asset', 'Type', 'Notes'), editable_columns=['Asset', 'Type', 'Notes'],
                    on_commit_callback=self.handle_db_update, get_options_callback=self.get_dd_values,
                    show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Asset', text='Name', command=lambda: self.sort_by_column('Asset'))
        self.tree.heading('Type', text='Type', command=lambda: self.sort_by_column('Type'))
        self.tree.heading('Notes', text='Notes', command=lambda: self.sort_by_column('Notes'))

        self.tree.column('Asset', width=250)
        self.tree.column('Type', width=200)
        self.tree.column('Notes', width=220)

        self.tree.pack(fill='both', expand=True)
        
        self.tree.bind("<Delete>", lambda e: self.delete_template()) # Enable delete key to remove items

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Add Entry", style='Accent.TButton', command=self.add_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Entry", command=self.edit_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Entry", command=self.delete_template).pack(side='left', padx=5)

        # Load templates into the list when dialog opens
        self.refresh_templates()

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Build a list of (value, item_id) tuples for sorting
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        # Case-insensitive string sort
        items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)

        # Reorder the tree items according to sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)

    def refresh_templates(self):
        # Refresh the displayed list of asset templates from the DB
        for item in self.tree.get_children():
            self.tree.delete(item)

        templates = self.db.get_asset_templates()

        for template in templates:
            display_values = [
                template['asset_name'],
                template['asset_type'] or '',
                template['notes'] or ''
            ]
            self.tree.insert('', 'end', values=display_values, tags=(template['id'],))

    def add_template(self):
        entries = self.db.get_asset_templates()
        # Modal stack handling (reacquires set after dialog is destroyed)
        dialog_window = TemplateDialog(self.dialog, self.db, asset_types=self.asset_types, entries=entries, callback=self.refresh_templates)
        self.dialog.wait_window(dialog_window.dialog)
        if self.dialog.winfo_exists():
            self.dialog.grab_set()

    def edit_template(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to edit")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Error", "Only one entry can be edited at a time")
            return

        entry_id = self.tree.item(selection[0])['tags'][0]
        entries = self.db.get_asset_templates()
        entry = next((t for t in entries if t['id'] == entry_id), None)

        if entry: # Modal stack handling (reacquires set after dialog is destroyed)
            dialog_window = TemplateDialog(self.dialog, self.db, asset_types=self.asset_types, entries=entries, entry=entry, callback=self.refresh_templates)
            self.dialog.wait_window(dialog_window.dialog)
            if self.dialog.winfo_exists():
                self.dialog.grab_set()

    def delete_template(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select entry(s) to delete")
            return

        count = len(selection)
        message = f"Delete {count} entries?" if count > 1 else "Delete this entry?"

        if messagebox.askyesno("Confirm", message):
            for item in selection:
                template_id = self.tree.item(item)['tags'][0]
                self.db.delete_asset_template(template_id)
            self.refresh_templates()
            
    def get_dd_values(self, column_name):
        # Provides values for inline combobox editing
        if column_name == 'Type':
            return self.asset_types
        return None # Entry field
    
    def handle_db_update(self, row_id, column_name, new_value):
        # Get db ID from tags
        entry_id = self.tree.item(row_id)['tags'][0]
        self.update_budget_field(entry_id, column_name, new_value)

    def update_budget_field(self, entry_id, field_name, new_value):
        entries = self.db.get_asset_templates()
        entry = next((e for e in entries if e['id'] == entry_id), None)
        if not entry:
            return

        # Update the in-memory asset dict then persist
        if field_name == 'Asset':
            # Unique name checking vars
            curr_names = [n['asset_name'].lower() for n in self.db.get_asset_templates()]
            if new_value.lower() != entry['asset_name'].lower() and new_value.lower() in curr_names:
                messagebox.showerror("Error", "An entry with that name already exists")
                return
            if not new_value: # Reject empty name entry
                messagebox.showerror("Error", "Entry name is required")
                return
            entry['asset_name'] = new_value
        elif field_name == 'Type':
            entry['asset_type'] = new_value
        elif field_name == 'Notes':
            entry['notes'] = new_value

        self.db.update_asset_template(
            template_id=entry_id,
            asset_name=entry['asset_name'],
            asset_type=entry['asset_type'],
            notes=entry['notes']
        )
        # Refresh view to show updated values
        self.refresh_templates()

class TemplateDialog:
    def __init__(self, parent, db: DatabaseManager, asset_types, entries, entry=None, callback=None):
        self.db = db
        self.asset_types = asset_types
        self.entries = entries
        self.entry = entry
        self.callback = callback

        # Dialog to add or edit an asset template (used when applying recurring assets)
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Template Entry" if not entry else "Edit Template Entry")
        self.dialog.geometry("300x230")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.asset_var = tk.StringVar(value=entry['asset_name'] if entry else '')
        ttk.Entry(self.dialog, textvariable=self.asset_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=entry['asset_type'] if entry else 'Cash')
        type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, state='readonly')
        type_combo['values'] = self.asset_types
        type_combo.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=entry['notes'] if entry and entry['notes'] else '')
        ttk.Entry(self.dialog, textvariable=self.notes_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    def save(self):
        # Unique name checking vars
        curr_names = [n['asset_name'].lower() for n in self.entries]
        new_name = self.asset_var.get()
        # Persist template changes and refresh caller view
        if self.entry:
            if new_name.lower() != self.entry['asset_name'].lower() and new_name.lower() in curr_names:
                messagebox.showerror("Error", "An entry with that name already exists")
                return
            if not new_name: # Reject empty name entry
                messagebox.showerror("Error", "Entry name is required")
                return
            self.db.update_asset_template(
                template_id=self.entry['id'],
                asset_name=new_name,
                asset_type=self.type_var.get(),
                notes=self.notes_var.get()
            )
        else:
            if new_name.lower() in curr_names:
                messagebox.showerror("Error", "An entry with that name already exists")
                return
            if not new_name: # Reject empty name entry
                messagebox.showerror("Error", "Entry name is required")
                return
            self.db.add_asset_template(
                asset_name=new_name,
                asset_type=self.type_var.get(),
                notes=self.notes_var.get()
            )

        if self.callback:
            self.callback()

        self.dialog.destroy()
