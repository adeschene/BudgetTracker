import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager

class BudgetTab:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        self.frame = tk.Frame(parent)
        
        self.setup_ui()
    
    def setup_ui(self):
        info_frame = tk.Frame(self.frame)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(info_frame, text="Set monthly budget targets for each expense category", 
                font=('Arial', 10)).pack()
        
        tree_frame = tk.Frame(self.frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(tree_frame, columns=('Category', 'Monthly Target', 'Notes'),
                                show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading('Category', text='Category')
        self.tree.heading('Monthly Target', text='Monthly Target')
        self.tree.heading('Notes', text='Notes')
        
        self.tree.column('Category', width=200)
        self.tree.column('Monthly Target', width=150)
        self.tree.column('Notes', width=300)
        
        self.tree.pack(fill='both', expand=True)
        
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Add Budget", command=self.add_budget).pack(side='left', padx=5)
        tk.Button(button_frame, text="Edit Budget", command=self.edit_budget).pack(side='left', padx=5)
        tk.Button(button_frame, text="Delete Budget", command=self.delete_budget).pack(side='left', padx=5)
        
        self.refresh_budgets()
    
    def refresh_budgets(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        budgets = self.db.get_budget_targets()
        
        for budget in budgets:
            display_values = [
                budget['category'],
                f"${budget['monthly_target']:.2f}",
                budget['notes'] or ''
            ]
            self.tree.insert('', 'end', values=display_values, tags=(budget['id'],))
    
    def add_budget(self):
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
        self.dialog.title("Edit Budget" if budget else "Add Budget")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="Category:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.category_var = tk.StringVar(value=budget['category'] if budget else '')
        
        if budget:
            tk.Label(self.dialog, text=budget['category'], font=('Arial', 10, 'bold')).grid(row=0, column=1, padx=10, pady=10, sticky='w')
        else:
            categories = [cat['name'] for cat in self.db.get_categories() if cat['type'] == 'expense']
            category_combo = ttk.Combobox(self.dialog, textvariable=self.category_var, values=categories)
            category_combo.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        tk.Label(self.dialog, text="Monthly Target:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.target_var = tk.StringVar(value=str(budget['monthly_target']) if budget else '0')
        tk.Entry(self.dialog, textvariable=self.target_var).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        tk.Label(self.dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.notes_var = tk.StringVar(value=budget['notes'] if budget and budget['notes'] else '')
        tk.Entry(self.dialog, textvariable=self.notes_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Save", command=self.save, width=10).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)
        
        self.dialog.columnconfigure(1, weight=1)
    
    def save(self):
        try:
            target = float(self.target_var.get())
            
            if self.budget:
                self.db.update_budget_target(
                    budget_id=self.budget['id'],
                    category=self.category_var.get(),
                    monthly_target=target,
                    notes=self.notes_var.get()
                )
            else:
                if not self.category_var.get():
                    messagebox.showerror("Error", "Please select a category")
                    return
                
                self.db.add_budget_target(
                    category=self.category_var.get(),
                    monthly_target=target,
                    notes=self.notes_var.get()
                )
            
            if self.callback:
                self.callback()
            
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid target amount")
