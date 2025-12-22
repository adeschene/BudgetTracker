import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager

class ImportTemplateManager:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Template Manager")
        self.dialog.geometry("1200x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        tk.Label(left_frame, text="Import Templates", font=('Roboto', 12, 'bold')).pack(pady=5)
        
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.template_tree = ttk.Treeview(tree_frame, columns=('Template', 'Account'), 
                                         show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.template_tree.yview)
        
        self.template_tree.heading('Template', text='Template Name')
        self.template_tree.heading('Account', text='Account')
        
        self.template_tree.column('Template', width=150, anchor='center')
        self.template_tree.column('Account', width=100, anchor='center')
        
        self.template_tree.pack(fill='both', expand=True)
        self.template_tree.bind('<<TreeviewSelect>>', self.on_template_select)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add Template", style='Accent.TButton', command=self.add_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Template", command=self.edit_template).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Template", command=self.delete_template).pack(side='left', padx=5)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        tk.Label(right_frame, text="Description Rules", font=('Roboto', 12, 'bold')).pack(pady=5)
        
        rules_tree_frame = ttk.Frame(right_frame)
        rules_tree_frame.pack(fill='both', expand=True)
        
        rules_scrollbar = ttk.Scrollbar(rules_tree_frame)
        rules_scrollbar.pack(side='right', fill='y')
        
        self.rules_tree = ttk.Treeview(rules_tree_frame, columns=('Order', 'Pattern', 'Replacement', 'Category'),
                                      show='headings', yscrollcommand=rules_scrollbar.set)
        rules_scrollbar.config(command=self.rules_tree.yview)
        
        self.rules_tree.heading('Order', text='#')
        self.rules_tree.heading('Pattern', text='Pattern (Regex)')
        self.rules_tree.heading('Replacement', text='Replacement')
        self.rules_tree.heading('Category', text='Category')
        
        self.rules_tree.column('Order', width=20, anchor='center')
        self.rules_tree.column('Pattern', width=300)
        self.rules_tree.column('Replacement', width=200, anchor='center')
        self.rules_tree.column('Category', width=100, anchor='center')
        
        self.rules_tree.pack(fill='both', expand=True)
        
        rules_button_frame = ttk.Frame(right_frame)
        rules_button_frame.pack(pady=10)
        
        ttk.Button(rules_button_frame, text="Add Rule", style='Accent.TButton', command=self.add_rule).pack(side='left', padx=5)
        ttk.Button(rules_button_frame, text="Edit Rule", command=self.edit_rule).pack(side='left', padx=5)
        ttk.Button(rules_button_frame, text="Delete Rule", command=self.delete_rule).pack(side='left', padx=5)
        ttk.Button(rules_button_frame, text="Move Up", command=self.move_rule_up).pack(side='left', padx=5)
        ttk.Button(rules_button_frame, text="Move Down", command=self.move_rule_down).pack(side='left', padx=5)
        
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)
        
        self.refresh_templates()
    
    def refresh_templates(self):
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)
        
        templates = self.db.get_import_templates()
        
        for template in templates:
            self.template_tree.insert('', 'end', values=(
                template['template_name'],
                template['account_name']
            ), tags=(template['id'],))
    
    def on_template_select(self, event):
        self.refresh_rules()
    
    def refresh_rules(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        selection = self.template_tree.selection()
        if not selection:
            return
        
        template_id = self.template_tree.item(selection[0])['tags'][0]
        rules = self.db.get_description_rules(template_id)
        
        for rule in rules:
            self.rules_tree.insert('', 'end', values=(
                rule['rule_order'] + 1,
                rule['pattern'],
                rule['replacement'],
                rule['category'] or ''
            ), tags=(rule['id'],))
    
    def add_template(self):
        TemplateDialog(self.dialog, self.db, callback=self.refresh_templates)
    
    def edit_template(self):
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template to edit")
            return
        
        template_id = self.template_tree.item(selection[0])['tags'][0]
        template = self.db.get_import_template(template_id)
        
        if template:
            TemplateDialog(self.dialog, self.db, template=template, callback=self.refresh_templates)
    
    def delete_template(self):
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete this template and all its rules?"):
            template_id = self.template_tree.item(selection[0])['tags'][0]
            self.db.delete_import_template(template_id)
            self.refresh_templates()
            self.refresh_rules()
    
    def add_rule(self):
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a template first")
            return
        
        template_id = self.template_tree.item(selection[0])['tags'][0]
        RuleDialog(self.dialog, self.db, template_id, callback=self.refresh_rules)
    
    def edit_rule(self):
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a rule to edit")
            return
        
        rule_id = self.rules_tree.item(selection[0])['tags'][0]
        template_selection = self.template_tree.selection()
        template_id = self.template_tree.item(template_selection[0])['tags'][0]
        
        rules = self.db.get_description_rules(template_id)
        rule = next((r for r in rules if r['id'] == rule_id), None)
        
        if rule:
            RuleDialog(self.dialog, self.db, template_id, rule=rule, callback=self.refresh_rules)
    
    def delete_rule(self):
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a rule to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete this rule?"):
            rule_id = self.rules_tree.item(selection[0])['tags'][0]
            self.db.delete_description_rule(rule_id)
            self.refresh_rules()
    
    def move_rule_up(self):
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        index = self.rules_tree.index(item)
        
        if index == 0:
            return
        
        template_selection = self.template_tree.selection()
        template_id = self.template_tree.item(template_selection[0])['tags'][0]
        
        rules = self.db.get_description_rules(template_id)
        rule_ids = [r['id'] for r in rules]
        
        rule_ids[index], rule_ids[index-1] = rule_ids[index-1], rule_ids[index]
        
        self.db.reorder_description_rules(template_id, rule_ids)
        self.refresh_rules()
        
        new_items = self.rules_tree.get_children()
        self.rules_tree.selection_set(new_items[index-1])
    
    def move_rule_down(self):
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        index = self.rules_tree.index(item)
        
        if index >= len(self.rules_tree.get_children()) - 1:
            return
        
        template_selection = self.template_tree.selection()
        template_id = self.template_tree.item(template_selection[0])['tags'][0]
        
        rules = self.db.get_description_rules(template_id)
        rule_ids = [r['id'] for r in rules]
        
        rule_ids[index], rule_ids[index+1] = rule_ids[index+1], rule_ids[index]
        
        self.db.reorder_description_rules(template_id, rule_ids)
        self.refresh_rules()
        
        new_items = self.rules_tree.get_children()
        self.rules_tree.selection_set(new_items[index+1])


class TemplateDialog:
    def __init__(self, parent, db: DatabaseManager, template=None, callback=None):
        self.db = db
        self.template = template
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Template" if template else "Add Template")
        self.dialog.geometry("500x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Template Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_var = tk.StringVar(value=template['template_name'] if template else '')
        ttk.Entry(self.dialog, textvariable=self.name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Account:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.account_var = tk.StringVar(value=template['account_name'] if template else '')
        accounts = [acc['name'] for acc in self.db.get_accounts()]
        account_combo = ttk.Combobox(self.dialog, textvariable=self.account_var, values=accounts)
        account_combo.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Date Column:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.date_col_var = tk.StringVar(value=template['date_column'] if template else 'Date')
        ttk.Entry(self.dialog, textvariable=self.date_col_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Description Column:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.desc_col_var = tk.StringVar(value=template['description_column'] if template else 'Description')
        ttk.Entry(self.dialog, textvariable=self.desc_col_var).grid(row=3, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Description 2 Column (optional):").grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.desc2_col_var = tk.StringVar(value=template['description2_column'] if template and template.get('description2_column') else '')
        ttk.Entry(self.dialog, textvariable=self.desc2_col_var).grid(row=4, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Description Delimiter:").grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.delimiter_var = tk.StringVar(value=template['description_delimiter'] if template and template.get('description_delimiter') else ' - ')
        delimiter_frame = tk.Frame(self.dialog)
        delimiter_frame.grid(row=5, column=1, padx=10, pady=10, sticky='ew')
        ttk.Entry(delimiter_frame, textvariable=self.delimiter_var, width=4).pack(side='left')
        tk.Label(delimiter_frame, text="(used when Description 2 is set)", fg='gray').pack(side='left', padx=5)

        ttk.Label(self.dialog, text="Amount Column Mode:").grid(row=6, column=0, padx=10, pady=10, sticky='w')
        self.amount_mode_var = tk.StringVar(value='single')
        mode_frame = ttk.Frame(self.dialog)
        mode_frame.grid(row=6, column=1, padx=10, pady=10, sticky='w')
        ttk.Radiobutton(mode_frame, text="Single Amount Column", variable=self.amount_mode_var, value='single', command=self.toggle_amount_mode).pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text="Separate Debit/Credit", variable=self.amount_mode_var, value='split', command=self.toggle_amount_mode).pack(side='left', padx=5)

        ttk.Label(self.dialog, text="Amount Column:").grid(row=7, column=0, padx=10, pady=10, sticky='w')
        self.amount_col_var = tk.StringVar(value=template['amount_column'] if template and template.get('amount_column') else 'Amount')
        self.amount_entry = ttk.Entry(self.dialog, textvariable=self.amount_col_var)
        self.amount_entry.grid(row=7, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Debit Column:").grid(row=8, column=0, padx=10, pady=10, sticky='w')
        self.debit_col_var = tk.StringVar(value=template['debit_column'] if template and template.get('debit_column') else 'Debit')
        self.debit_entry = ttk.Entry(self.dialog, textvariable=self.debit_col_var, state='disabled')
        self.debit_entry.grid(row=8, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Credit Column:").grid(row=9, column=0, padx=10, pady=10, sticky='w')
        self.credit_col_var = tk.StringVar(value=template['credit_column'] if template and template.get('credit_column') else 'Credit')
        self.credit_entry = ttk.Entry(self.dialog, textvariable=self.credit_col_var, state='disabled')
        self.credit_entry.grid(row=9, column=1, padx=10, pady=10, sticky='ew')

        if template and template.get('debit_column') and template.get('credit_column'):
            self.amount_mode_var.set('split')
            self.toggle_amount_mode()

        ttk.Label(self.dialog, text="Skip Rows:").grid(row=10, column=0, padx=10, pady=10, sticky='w')
        self.skip_rows_var = tk.IntVar(value=template['skip_rows'] if template else 0)
        skip_frame = ttk.Frame(self.dialog)
        skip_frame.grid(row=10, column=1, padx=10, pady=10, sticky='ew')
        ttk.Spinbox(skip_frame, from_=0, to=100, textvariable=self.skip_rows_var, width=4).pack(side='left')
        tk.Label(skip_frame, text="(rows to skip before header)", fg='gray').pack(side='left', padx=5)

        ttk.Label(self.dialog, text="Notes:").grid(row=11, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=template['notes'] if template and template['notes'] else '')
        ttk.Entry(self.dialog, textvariable=self.notes_var).grid(row=11, column=1, padx=10, pady=10, sticky='ew')

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

    def toggle_amount_mode(self):
        """Enable/disable amount fields based on selected mode (single vs split)."""
        if self.amount_mode_var.get() == 'single':
            self.amount_entry.config(state='normal')
            self.debit_entry.config(state='disabled')
            self.credit_entry.config(state='disabled')
        else:
            self.amount_entry.config(state='disabled')
            self.debit_entry.config(state='normal')
            self.credit_entry.config(state='normal')

    def save(self):
        if not self.name_var.get() or not self.account_var.get():
            messagebox.showerror("Error", "Template name and account are required")
            return

        amount_col = None
        debit_col = None
        credit_col = None

        if self.amount_mode_var.get() == 'single':
            amount_col = self.amount_col_var.get()
            if not amount_col:
                messagebox.showerror("Error", "Amount column is required")
                return
        else:
            debit_col = self.debit_col_var.get()
            credit_col = self.credit_col_var.get()
            if not debit_col or not credit_col:
                messagebox.showerror("Error", "Both debit and credit columns are required")
                return

        if self.template:
            self.db.update_import_template(
                template_id=self.template['id'],
                template_name=self.name_var.get(),
                account_name=self.account_var.get(),
                date_column=self.date_col_var.get(),
                description_column=self.desc_col_var.get(),
                description2_column=self.desc2_col_var.get() or None,
                description_delimiter=self.delimiter_var.get(),
                amount_column=amount_col,
                debit_column=debit_col,
                credit_column=credit_col,
                skip_rows=self.skip_rows_var.get(),
                notes=self.notes_var.get()
            )
        else:
            self.db.add_import_template(
                template_name=self.name_var.get(),
                account_name=self.account_var.get(),
                date_column=self.date_col_var.get(),
                description_column=self.desc_col_var.get(),
                description2_column=self.desc2_col_var.get() or None,
                description_delimiter=self.delimiter_var.get(),
                amount_column=amount_col,
                debit_column=debit_col,
                credit_column=credit_col,
                skip_rows=self.skip_rows_var.get(),
                notes=self.notes_var.get()
            )

        if self.callback:
            self.callback()

        self.dialog.destroy()


class RuleDialog:
    def __init__(self, parent, db: DatabaseManager, template_id: int, rule=None, callback=None):
        self.db = db
        self.template_id = template_id
        self.rule = rule
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Rule" if rule else "Add Rule")
        self.dialog.geometry("500x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Pattern (Regex):").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.pattern_var = tk.StringVar(value=rule['pattern'] if rule else '')
        ttk.Entry(self.dialog, textvariable=self.pattern_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Replacement:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.replacement_var = tk.StringVar(value=rule['replacement'] if rule else '')
        replacement_entry = ttk.Entry(self.dialog, textvariable=self.replacement_var)
        replacement_entry.grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Category (optional):").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.category_var = tk.StringVar(value=rule['category'] if rule and rule['category'] else '')
        categories = [cat['name'] for cat in self.db.get_categories()]
        category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var, values=[''] + categories)
        category_combo.grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        self.ignore_var = tk.IntVar(value=rule['ignore'] if rule and 'ignore' in rule else 0)
        ignore_check = ttk.Checkbutton(self.dialog, text="Ignore matching transactions (don't import)", variable=self.ignore_var, command=self.toggle_ignore)
        ignore_check.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='w')

        self.replacement_entry = replacement_entry
        self.category_combo = category_combo
        self.toggle_ignore()

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

    def toggle_ignore(self):
        if self.ignore_var.get():
            self.replacement_entry.config(state='disabled')
            self.category_combo.config(state='disabled')
        else:
            self.replacement_entry.config(state='normal')
            self.category_combo.config(state='readonly')

    def save(self):
        if not self.pattern_var.get():
            messagebox.showerror("Error", "Pattern is required")
            return

        if not self.ignore_var.get() and not self.replacement_var.get():
            messagebox.showerror("Error", "Replacement is required when not ignoring")
            return

        if self.rule:
            self.db.update_description_rule(
                rule_id=self.rule['id'],
                rule_order=self.rule['rule_order'],
                pattern=self.pattern_var.get(),
                replacement=self.replacement_var.get(),
                category=self.category_var.get() or None,
                ignore=self.ignore_var.get()
            )
        else:
            rules = self.db.get_description_rules(self.template_id)
            next_order = len(rules)

            self.db.add_description_rule(
                template_id=self.template_id,
                rule_order=next_order,
                pattern=self.pattern_var.get(),
                replacement=self.replacement_var.get(),
                category=self.category_var.get() or None,
                ignore=self.ignore_var.get()
            )

        if self.callback:
            self.callback()

        self.dialog.destroy()
