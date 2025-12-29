import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager
from utils.helpers import center_window, validate_money_string

class BudgetTab:
    def __init__(self, parent, db: DatabaseManager):
        # Store the database manager and create a containing frame
        self.db = db
        self.frame = ttk.Frame(parent)

        # Build UI widgets for the Budget tab
        self.setup_ui()
    
    def setup_ui(self):
        # Top info label explaining the purpose of this tab
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(info_frame, text="Set monthly budget targets for each expense category").pack()
        
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview displays budget rows: category, monthly target and notes
        self.tree = ttk.Treeview(tree_frame, columns=('Category', 'Monthly Target', 'Notes'),
                    show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading('Category', text='Category')
        self.tree.heading('Monthly Target', text='Monthly Target')
        self.tree.heading('Notes', text='Notes')
        
        self.tree.column('Category', width=100, anchor='center')
        self.tree.column('Monthly Target', width=150, anchor='center')
        self.tree.column('Notes', width=300)
        
        self.tree.pack(fill='both', expand=True)
        
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add Budget", style='Accent.TButton', command=self.add_budget).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Budget", command=self.edit_budget).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Budget", command=self.delete_budget).pack(side='left', padx=5)
        
        self.refresh_budgets()
    
    def refresh_budgets(self):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Load budget targets from the database and populate the tree
        budgets = self.db.get_budget_targets()

        for budget in budgets:
            display_values = [
                budget['category'],
                f"${budget['monthly_target']:,}",
                budget['notes'] or ''
            ]
            # Store budget id in the item's tags for later lookup
            self.tree.insert('', 'end', values=display_values, tags=(budget['id'],))
    
    def add_budget(self):
        # Open dialog to create a new budget target; refresh after save
        BudgetDialog(self.frame, self.db, callback=self.refresh_budgets)
    
    def edit_budget(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a budget to edit")
            return
        
        budget_id = self.tree.item(selection[0])['tags'][0]
        budgets = self.db.get_budget_targets()
        budget = next((b for b in budgets if b['id'] == budget_id), None)
        
        if budget:
            # Open dialog pre-filled with the selected budget for editing
            BudgetDialog(self.frame, self.db, budget=budget, callback=self.refresh_budgets)
    
    def delete_budget(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a budget to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this budget target?"):
            budget_id = self.tree.item(selection[0])['tags'][0]
            self.db.delete_budget_target(budget_id)
            self.refresh_budgets()


class BudgetDialog:
    def __init__(self, parent, db: DatabaseManager, budget=None, callback=None):
        self.db = db
        self.budget = budget
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        # Toplevel dialog used for adding or editing a budget target
        self.dialog.title("Edit Budget" if budget else "Add Budget")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        
        vcmd_positive_whole_dollars = (self.dialog.register(validate_money_string),"%P",False,False) # Digit validation registration
        
        ttk.Label(self.dialog, text="Category:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.category_var = tk.StringVar(value=budget['category'] if budget else '')
        
        if budget:
            ttk.Label(self.dialog, text=budget['category']).grid(row=0, column=1, padx=10, pady=10, sticky='w')
        else:
            categories = [cat['name'] for cat in self.db.get_categories() if cat['type'] == 'expense']
            category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var, values=categories)
            category_combo.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # Input for the numeric monthly target amount
        ttk.Label(self.dialog, text="Monthly Target ($):").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.target_var = tk.StringVar(value=str(budget['monthly_target']) if budget else '')
        ttk.Entry(self.dialog, validate='all', validatecommand=vcmd_positive_whole_dollars, 
                textvariable=self.target_var).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(self.dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=budget['notes'] if budget and budget['notes'] else '')
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
        try:
            target = int(self.target_var.get())
            
            if self.budget:
                self.db.update_budget_target(
                    budget_id=self.budget['id'],
                    category=self.category_var.get(),
                    monthly_target=target,
                    notes=self.notes_var.get()
                )
            else:
                # Creating a new budget requires selecting a category
                if not self.category_var.get():
                    messagebox.showerror("Error", "Please select a category")
                    return

                # Insert new budget target into the database
                self.db.add_budget_target(
                    category=self.category_var.get(),
                    monthly_target=target,
                    notes=self.notes_var.get()
                )
            
            if self.callback:
                # Notify caller to refresh displayed data
                self.callback()
            
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid target amount")
