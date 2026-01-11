import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager
from utils.editable_tree import EditableTree
from utils.helpers import center_window, validate_money_string

class BudgetTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db

        self.sort_state = {} # Track sorting state for both trees independently
        self.total_labels = {} # Maps a tree to its specific total label

        self.setup_ui()
    
    def setup_ui(self):
        # Header with Instructions
        info_frame = ttk.Frame(self)
        info_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        ttk.Label(info_frame, 
                  text="Set monthly targets for Income and Expense categories.",
                  font=('Roboto', 10, 'bold')).pack(side='left', anchor='w')
        
        # Double-click edit instruction
        ttk.Label(info_frame, 
                  text="Tips: Double-click any 'Monthly Target' or 'Notes' cell to edit its value. Click on headers to sort data.",
                  foreground="gray").pack(side='left', anchor='w', padx=(30,0))
        
        # Horizontal container for the two trees
        main_container = ttk.Frame(self)
        main_container.pack(fill='both', expand=True, padx=10)

        # 1. Expense Side (Left)
        expense_frame = ttk.LabelFrame(main_container, text="Expense Budgets")
        expense_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self.expense_tree = self.create_budget_tree(expense_frame)
        self.sort_state[self.expense_tree] = {'column': None, 'reverse': False}
        # Footer for Expense Totals
        self.expense_total_lbl = ttk.Label(expense_frame, text="Total: $0 / $0", font=('TkDefaultFont', 9, 'bold'))
        self.expense_total_lbl.pack(pady=5)
        self.total_labels[self.expense_tree] = self.expense_total_lbl

        # 2. Income Side (Right)
        income_frame = ttk.LabelFrame(main_container, text="Income Targets")
        income_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        self.income_tree = self.create_budget_tree(income_frame)
        self.sort_state[self.income_tree] = {'column': None, 'reverse': False}
        # Footer for Income Totals
        self.income_total_lbl = ttk.Label(income_frame, text="Total: $0 / $0", font=('TkDefaultFont', 9, 'bold'))
        self.income_total_lbl.pack(pady=5)
        self.total_labels[self.income_tree] = self.income_total_lbl

        # Shared Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Clear Selected", command=self.clear_budget).pack(side='left', padx=5)

    def create_budget_tree(self, parent):
        tree_container = ttk.Frame(parent)
        tree_container.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side='right', fill='y')
        
        tree = EditableTree(
            tree_container, 
            columns=('Category', 'Monthly Target', 'Implied', 'Notes'), 
            editable_columns=['Monthly Target', 'Notes'],
            get_validation_callback=self.provide_validation, 
            show='headings', 
            yscrollcommand=scrollbar.set
        )
        
        # Pass the tree instance into the handler so it knows which tree was edited
        tree.on_commit = lambda r, c, v: self.handle_db_update(tree, r, c, v)
        
        scrollbar.config(command=tree.yview)
        
        # Configure headings with sorting and widths
        cols = {'Category': 100, 'Monthly Target': 120, 'Implied': 120, 'Notes': 250}
        for col, width in cols.items():
            text = 'Implied Annual' if col == 'Implied' else col
            # Configure the Header (heading)
            h_anchor = 'w' if col == 'Notes' else 'center'
            tree.heading(col, text=text, anchor=h_anchor,
                         command=lambda c=col, t=tree: self.sort_by_column(t, c))
            # Configure the Data (column)
            d_anchor = 'w' if col == 'Notes' else 'center'
            tree.column(col, width=width, anchor=d_anchor)
        
        tree.pack(fill='both', expand=True)
        return tree

    def on_tab_opened(self):
        self.refresh_budgets()

    def sort_by_column(self, tree, column):
        state = self.sort_state[tree]
        if state['column'] == column:
            state['reverse'] = not state['reverse']
        else:
            state['column'] = column
            state['reverse'] = False
        self.apply_current_sort(tree)

    def apply_current_sort(self, tree):
        state = self.sort_state[tree]
        column = state['column']
        if not column: return

        items = [(tree.set(item, column), item) for item in tree.get_children('')]

        if column in ('Monthly Target', 'Implied'):
            items.sort(
                key=lambda x: int(str(x[0]).replace('$', '').replace(',', '').replace('-', '0') or 0), 
                reverse=state['reverse']
            )
        else:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=state['reverse'])

        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)
    
    def refresh_budgets(self):
        self._populate_tree(self.expense_tree, 'expense')
        self._populate_tree(self.income_tree, 'income')

    def _populate_tree(self, tree, cat_type):
        for item in tree.get_children():
            tree.delete(item)
        
        budgets = self.db.get_all_category_budgets(cat_type)
        total_monthly = 0

        for b in budgets:
            target = b['monthly_target']
            total_monthly += target

            display_values = [
                b['category_name'],
                f"${target:,}",
                f"${target * 12:,}", 
                b['notes'] or ''
            ]
            tree.insert('', 'end', values=display_values, tags=(b['category_id'], b['budget_id']))
        # Update the summary text for this specific section
        total_annual = total_monthly * 12
        label = self.total_labels[tree]
        label.config(text=f"Total: ${total_monthly:,} (Monthly) / ${total_annual:,} (Annual)")

        self.apply_current_sort(tree)
    
    def clear_budget(self):
        # Check both trees for selections
        selections = [(self.expense_tree, self.expense_tree.selection()), 
                      (self.income_tree, self.income_tree.selection())]
        
        to_delete = []
        for tree, items in selections:
            for item in items:
                # budget_id is index 1 of the tags tuple
                tags = tree.item(item)['tags']
                budget_id = tags[1] if len(tags) > 1 else None
                if budget_id and str(budget_id) != 'None':
                    to_delete.append(budget_id)

        if not to_delete:
            messagebox.showwarning("Warning", "Please select existing budget target(s) to clear")
            return

        if messagebox.askyesno("Confirm", f"Clear {len(to_delete)} budget targets?"):
            for b_id in to_delete:
                self.db.delete_budget_target(int(b_id))
            self.refresh_budgets()

    def provide_validation(self, column_name):
        if column_name == 'Monthly Target':
            return (validate_money_string, 'False', 'False')
        return None
    
    def handle_db_update(self, tree, row_id, column_name, new_value):
        if not tree.exists(row_id):
            return
        
        tags = tree.item(row_id)['tags']
        category_id, budget_id = tags[0], tags[1]
        current_values = tree.item(row_id)['values']
        
        try:
            if column_name == 'Monthly Target':
                clean_val = str(new_value).replace('$', '').replace(',', '')
                target = int(clean_val) if clean_val else 0
                notes = current_values[3]
            else:
                target = int(str(current_values[1]).replace('$', '').replace(',', ''))
                notes = new_value

            if budget_id is None or str(budget_id) == 'None':
                if target > 0 or notes:
                    self.db.add_budget_target(category_id, target, notes)
            else:
                self.db.update_budget_target(int(budget_id), category_id, target, notes)
            
            self.refresh_budgets()

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
            self.refresh_budgets()