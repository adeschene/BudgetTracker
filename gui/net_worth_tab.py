import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from calendar import monthrange
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager
from utils.helpers import center_window, validate_money_string

class NetWorthTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs) # Initialize tab frame
        self.db = db

        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year

        self.setup_ui()

    def setup_ui(self):
        month_selector_frame = ttk.Frame(self)
        month_selector_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(month_selector_frame, text="Month:", font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        ttk.Button(month_selector_frame, text="◀", width=3, command=self.previous_month).pack(side='left', padx=2)

        self.month_label = tk.Label(month_selector_frame, text="", font=('Roboto', 12, 'bold'), width=16, anchor='center')
        self.month_label.pack(side='left', padx=2)

        ttk.Button(month_selector_frame, text="▶", width=3, command=self.next_month).pack(side='left', padx=10)

        ttk.Button(month_selector_frame, text="Current Month", command=self.go_to_current_month).pack(side='left', padx=10)

        self.update_month_label()

        summary_frame = ttk.Labelframe(self, text="Net Worth Summary")
        summary_frame.pack(fill='x', padx=10, pady=10)

        self.total_label = tk.Label(summary_frame, text="Total Net Worth: $0",
                                    font=('Roboto', 16, 'bold'), fg='#217346')
        self.total_label.pack(pady=10)

        breakdown_frame = ttk.Frame(summary_frame)
        breakdown_frame.pack(fill='x', padx=20, pady=10)

        self.breakdown_text = tk.Text(breakdown_frame, height=5, width=50, state='disabled')
        self.breakdown_text.pack()

        entries_frame = ttk.Labelframe(self, text="Net Worth Entries for Selected Month")
        entries_frame.pack(fill='both', expand=True, padx=10, pady=10)

        tree_frame = ttk.Frame(entries_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.tree = ttk.Treeview(tree_frame, columns=('Date', 'Asset', 'Type', 'Value', 'Notes'),
                                 show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Date', text='Date')
        self.tree.heading('Asset', text='Asset/Liability Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Value', text='Value')
        self.tree.heading('Notes', text='Notes')

        self.tree.column('Date', width=100, anchor='center')
        self.tree.column('Asset', width=200, anchor='center')
        self.tree.column('Type', width=150, anchor='center')
        self.tree.column('Value', width=120, anchor='center')
        self.tree.column('Notes', width=200)

        # Double-click allows inline editing of entries (asset/type/value/notes)
        self.tree.bind('<Double-Button-1>', self.on_double_click)

        self.tree.pack(fill='both', expand=True)

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

    def add_entry(self):
        start_date, end_date = self.get_month_date_range()
        NetWorthDialog(self, self.db, callback=self.refresh_data, start_date=start_date, end_date=end_date,
                      default_month=self.current_month, default_year=self.current_year)

    def edit_entry(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to edit")
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
            messagebox.showwarning("Warning", "Please select an entry to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
            entry_id = self.tree.item(selection[0])['tags'][0]
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
        TemplateManagerDialog(self, self.db)

    def on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)

        if not row_id:
            return

        column_index = int(column.replace('#', '')) - 1
        column_names = ['Date', 'Asset', 'Type', 'Value', 'Notes']
        column_name = column_names[column_index]

        # Allow editing of asset name, type, value and notes
        if column_name not in ['Asset', 'Type', 'Value', 'Notes']:
            return

        entry_id = self.tree.item(row_id)['tags'][0]
        current_value = self.tree.item(row_id)['values'][column_index]

        x, y, width, height = self.tree.bbox(row_id, column)

        if column_name == 'Type':
            self.edit_cell_combobox(row_id, column_name, column_index, entry_id, current_value, x, y, width, height)
        else:
            self.edit_cell_entry(row_id, column_name, column_index, entry_id, current_value, x, y, width, height)

    def edit_cell_entry(self, row_id, column_name, column_index, entry_id, current_value, x, y, width, height):
        if column_name == 'Value':
            vcmd_decimal_dollar = (self.tree.register(validate_money_string), "%P", True, False) # Digit validation registration
            current_value = str(current_value).replace('$', '').replace(',', '')

        edit_var = tk.StringVar(value=current_value)
        if column_name == 'Value':
            edit_entry = ttk.Entry(self.tree, validate='key', validatecommand=vcmd_decimal_dollar, textvariable=edit_var)
        else:
            edit_entry = ttk.Entry(self.tree, textvariable=edit_var)
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.focus_set()
        edit_entry.select_range(0, tk.END)

        # Commit the inline edit to the DB via update_entry_field
        def save_edit(event=None):
            new_value = edit_var.get()
            edit_entry.destroy()
            self.update_entry_field(entry_id, column_name, new_value)

        def cancel_edit(event=None):
            edit_entry.destroy()

        edit_entry.bind('<Return>', save_edit)
        edit_entry.bind('<Escape>', cancel_edit)
        edit_entry.bind('<FocusOut>', save_edit)

    def edit_cell_combobox(self, row_id, column_name, column_index, entry_id, current_value, x, y, width, height):
        edit_var = tk.StringVar(value=current_value)
        edit_combo = ttk.Combobox(self.tree, textvariable=edit_var, state='readonly')
        edit_combo['values'] = ['Cash', 'Checking', 'Savings', 'Investment', 'Real Estate', 'Vehicle', 'Other Asset', 'Credit Card', 'Loan', 'Other Liability']
        edit_combo.place(x=x, y=y, width=width, height=height)
        edit_combo.focus_set()

        # Commit combobox selection to update the entry
        def save_edit(event=None):
            if edit_combo.winfo_exists():
                new_value = edit_var.get()
                edit_combo.destroy()
                self.update_entry_field(entry_id, column_name, new_value)

        def cancel_edit(event=None):
            if edit_combo.winfo_exists():
                edit_combo.destroy()

        edit_combo.bind('<<ComboboxSelected>>', save_edit)
        edit_combo.bind('<Return>', save_edit)
        edit_combo.bind('<Escape>', cancel_edit)

    def update_entry_field(self, entry_id, field_name, new_value):
        start_date, end_date = self.get_month_date_range()
        entries = self.db.get_net_worth_entries(start_date, end_date)
        entry = next((e for e in entries if e['id'] == entry_id), None)

        if not entry:
            return

        try:
            # Update the in-memory entry and persist change
            if field_name == 'Asset':
                # Check for duplicate names before saving
                entry_names = [e['asset_name'] for e in entries]
                if new_value != entry['asset_name'] and new_value in entry_names:
                    messagebox.showerror("Error", "An entry already exists by that name")
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
                asset_type=entry['asset_type'],
                value=entry['value'],
                notes=entry['notes']
            )

            # Refresh display after successful update
            self.refresh_data()
        except ValueError:
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
        
        vcmd_whole_dollars = (self.dialog.register(validate_money_string), "%P", True, False) # Digit validation registration

        if entry:
            default_date = entry['date']
        elif default_month and default_year:
            default_date = f"{default_year}-{default_month:02d}-01"
        else:
            default_date = datetime.now().strftime('%Y-%m-%d')

        date_obj = datetime.strptime(default_date, '%Y-%m-%d')

        ttk.Label(self.dialog, text="Date:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.date_picker = DateEntry(self.dialog, width=18, firstweekday='sunday',
                                    background='#232323', foreground='whitesmoke',
                                    headersbackground='#454545', headersforeground='whitesmoke',
                                    othermonthwebackground='#565656', othermonthweforeground='whitesmoke',
                                    weekendbackground='#666666', weekendforeground='whitesmoke',
                                    othermonthbackground='#777777', othermonthforeground='#232323',
                                    normalbackground='#888888', normalforeground='black',
                                    disableddaybackground='#454545', disableddayforeground='#888888',
                                    bordercolor='#343434', borderwidth=2, date_pattern='mm-dd-yyyy',
                                    maxdate=datetime.now(), year=date_obj.year,
                                    month=date_obj.month, day=date_obj.day)
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

    def save(self):
        entries = self.db.get_net_worth_entries(self.start_date, self.end_date)
        entry_names = [n['asset_name'] for n in entries]
        new_name = self.asset_var.get()
        try:
            # Persist the new or updated entry
            if self.entry:
                # Check for duplicate name before saving
                if self.entry['asset_name'] != new_name and new_name in entry_names:
                    messagebox.showerror("Error", "An entry with that name already exists for this month")
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
                if new_name in entry_names:
                    messagebox.showerror("Error", "An entry with that name already exists for this month")
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
            messagebox.showerror("Error", "Invalid value")

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

        info_label = ttk.Label(self.dialog,
                             text="Enter values for each asset to add to this month:"
                             )
        info_label.pack(padx=10, pady=10)

        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for i, template in enumerate(templates):
            frame = ttk.Frame(scrollable_frame, relief='ridge', borderwidth=1)
            frame.pack(fill='x', padx=5, pady=5, )

            ttk.Label(frame, text=template['asset_name']).grid(row=0, column=0, padx=10, pady=5, sticky='w')
            ttk.Label(frame, text=f"({template['asset_type'] or 'No Type'})").grid(row=0, column=1, padx=5, pady=5, sticky='w')

            vcmd_decimal_dollar = (frame.register(validate_money_string), "%P", True, False) # Digit validation registration

            ttk.Label(frame, text="Current Value:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
            value_var = tk.StringVar(value='')
            self.value_vars[template['id']] = value_var
            entry = ttk.Entry(frame, validate='key', validatecommand=vcmd_decimal_dollar, textvariable=value_var, width=20)
            entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

            if template['notes']:
                ttk.Label(frame, text=f"Note: {template['notes']}").grid(row=2, column=0, columnspan=2, padx=10, pady=2, sticky='w')

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Apply All", style='Accent.TButton', command=self.apply, width=12).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=12).pack(side='left', padx=5)

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    def apply(self):
        try:
            template_values = {}
            for template_id, value_var in self.value_vars.items():
                value = int(value_var.get())
                template_values[template_id] = value

            self.db.apply_templates_to_month(self.year, self.month, template_values)

            if self.callback:
                self.callback()

            messagebox.showinfo("Success", f"Templates applied to {datetime(self.year, self.month, 1).strftime('%B %Y')}!")
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all assets")

class TemplateManagerDialog:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db

        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Manage Asset Template")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)

        info_label = tk.Label(self.dialog,
                             text="This template is used to quickly add recurring assets/liabilities to each month.\nClick 'Apply Template' in the Net Worth tab to add these to the current month.",
                             font=('Roboto', 9), fg='white', justify='left')
        info_label.pack(padx=10, pady=10, anchor='w')

        tree_frame = ttk.Frame(self.dialog)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.tree = ttk.Treeview(tree_frame, columns=('Asset', 'Type', 'Notes'),
                                show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)

        self.tree.heading('Asset', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Notes', text='Notes')

        self.tree.column('Asset', width=250)
        self.tree.column('Type', width=200)
        self.tree.column('Notes', width=220)

        self.tree.pack(fill='both', expand=True)

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
        TemplateDialog(self.dialog, self.db, callback=self.refresh_templates)

    def edit_template(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to edit")
            return

        template_id = self.tree.item(selection[0])['tags'][0]
        templates = self.db.get_asset_templates()
        template = next((t for t in templates if t['id'] == template_id), None)

        if template:
            TemplateDialog(self.dialog, self.db, template=template, callback=self.refresh_templates)

    def delete_template(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
            template_id = self.tree.item(selection[0])['tags'][0]
            self.db.delete_asset_template(template_id)
            self.refresh_templates()

class TemplateDialog:
    def __init__(self, parent, db: DatabaseManager, template=None, callback=None):
        self.db = db
        self.template = template
        self.callback = callback

        # Dialog to add or edit an asset template (used when applying recurring assets)
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Add Template Entry" if not template else "Edit Template Entry")
        self.dialog.geometry("300x230")
        self.dialog.transient(parent)

        ttk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.asset_var = tk.StringVar(value=template['asset_name'] if template else '')
        ttk.Entry(self.dialog, textvariable=self.asset_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=template['asset_type'] if template else 'Cash')
        type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, state='readonly')
        type_combo['values'] = ['Cash', 'Checking', 'Savings', 'Investment', 'Real Estate', 'Vehicle', 'Other Asset', 'Credit Card', 'Loan', 'Other Liability']
        type_combo.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=template['notes'] if template and template['notes'] else '')
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
        curr_names = [n['asset_name'] for n in self.db.get_asset_templates()]
        new_name = self.asset_var.get()
        # Persist template changes and refresh caller view
        if self.template:
            if new_name != self.template['asset_name'] and new_name in curr_names:
                messagebox.showerror("Error", "An entry with that name already exists")
                return
            self.db.update_asset_template(
                template_id=self.template['id'],
                asset_name=new_name,
                asset_type=self.type_var.get(),
                notes=self.notes_var.get()
            )
        else:
            if new_name in curr_names:
                messagebox.showerror("Error", "An entry with that name already exists")
                return
            self.db.add_asset_template(
                asset_name=new_name,
                asset_type=self.type_var.get(),
                notes=self.notes_var.get()
            )

        if self.callback:
            self.callback()

        self.dialog.destroy()
