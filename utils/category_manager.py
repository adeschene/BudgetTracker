import tkinter as tk
from tkinter import ttk, messagebox
from database.db_manager import DatabaseManager
from utils.editable_tree import EditableTree
from utils.helpers import center_window

class CategoryManager:
    def __init__(self, parent, db, callback=None):
        self.db = db
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Manage Categories")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree = EditableTree(frame, columns=('Name', 'Type', 'Keywords'), editable_columns=['Name', 'Type', 'Keywords'],
                    on_commit_callback=self.handle_db_update, get_options_callback=self.get_dd_values, show='headings')
        
        self.tree.heading('Name', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Keywords', text='Keywords')

        # Keep Name and Type fixed; let Keywords expand when window is resized
        self.tree.column('Name', width=120, minwidth=75, stretch=False)
        self.tree.column('Type', anchor='center', width=100, minwidth=50, stretch=False)
        self.tree.column('Keywords', width=375, minwidth=100, stretch=True)
        
        self.tree.pack(fill='both', expand=True)
        
        self.tree.bind("<Delete>", lambda e: self.delete_category()) # Enable delete key to remove items
        
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add Category", style='Accent.TButton', command=self.add_category).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Category", command=self.edit_category).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Category", command=self.delete_category).pack(side='left', padx=5)
        
        self.refresh_categories()
        
        self.window.update_idletasks()
        center_window(self.window)
        self.window.deiconify()
    
    def refresh_categories(self):
        # Reload categories from DB and repopulate the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        categories = self.db.get_categories()
        for cat in categories:
            self.tree.insert('', 'end', values=(cat['name'], cat['type'].title(), cat['keywords']), tags=(cat['id'],))
    
    def _on_category_change(self):
        self.refresh_categories()
        if self.callback:
            self.callback()
    
    def add_category(self):
        categories = self.db.get_categories()
        # Modal stack handling (reacquires set after dialog is destroyed)
        dialog_window = CategoryDialog(self.window, self.db, categories=categories, callback=self._on_category_change)
        self.window.wait_window(dialog_window.dialog)
        if self.window.winfo_exists():
            self.window.grab_set()

    def edit_category(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to edit")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Error", "Only one category can be edited at a time")
            return

        category_id = int(self.tree.item(selection[0])['tags'][0])
        categories = self.db.get_categories()
        category = next((c for c in categories if c['id'] == category_id), None)

        if category:  # Modal stack handling (reacquires set after dialog is destroyed)
            dialog_window = CategoryDialog(self.window, self.db, categories=categories, category=category, callback=self._on_category_change)
            self.window.wait_window(dialog_window.dialog)
            if self.window.winfo_exists():
                self.window.grab_set()
        

    def delete_category(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select category(s) to delete")
            return

        count = len(selection)
        message = f"Delete {count} categories?" if count > 1 else "Delete this category?"

        if messagebox.askyesno("Confirm", message):
            # Delete each selected category and refresh view
            for item in selection:
                category_id = self.tree.item(item)['tags'][0]
                self.db.delete_category(category_id)
            self.refresh_categories()
            if self.callback:
                self.callback()

    def get_dd_values(self, column_name):
        # Provides values for inline combobox editing
        if column_name == 'Type':
            return ['Income','Expense']
        return None # Entry field
    
    def handle_db_update(self, row_id, column_name, new_value):
        # Get db ID from tags
        entry_id = self.tree.item(row_id)['tags'][0]
        self.update_category_field(entry_id, column_name, new_value)

    def update_category_field(self, category_id, field_name, new_value):
        categories = self.db.get_categories()
        category = next((t for t in categories if t['id'] == category_id), None)
        if not category:
            return

        try:
            # Update the in-memory category dict then persist
            if field_name == 'Name':
                # Make sure category name is unique
                current_cat_names = [c['name'].lower() for c in categories]
                if new_value.lower() != category['name'].lower() and new_value.lower() in current_cat_names:
                    messagebox.showerror("Error", "Category already exists")
                    return
                if not new_value: # Reject if entered empty name
                    messagebox.showerror("Error", "Category name is required")
                    return
                category['name'] = new_value
            elif field_name == 'Type':
                category['type'] = new_value
            elif field_name == 'Keywords':
                category['keywords'] = new_value

            self.db.update_category(
                category_id=category_id,
                name=category['name'],
                cat_type=category['type'],
                keywords=category['keywords']
            )
            # Refresh view to show updated values
            self.refresh_categories()
            if self.callback:
                self.callback()
        except (ValueError):
            messagebox.showerror("Error", "Invalid value entered")

class CategoryDialog:
    def __init__(self, parent, db: DatabaseManager, categories, category=None, callback=None):
        self.db = db
        self.categories = categories
        self.category = category
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Edit Category")
        self.dialog.geometry("300x250")
        
        self.dialog.transient(parent)
        self.dialog.grab_set() # Make window modal

        ttk.Label(self.dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_var = tk.StringVar(value=category['name'] if category else '')
        ttk.Entry(self.dialog, textvariable=self.name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.type_var = tk.StringVar(value=category['type'].title() if category else 'Expense')
        ttk.Combobox(self.dialog, textvariable=self.type_var, values=['Income', 'Expense'], state='readonly').grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(self.dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.keywords_var = tk.StringVar(value=category.get('keywords', '') if category else '')
        ttk.Entry(self.dialog, textvariable=self.keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        tk.Label(self.dialog, text="Enter keywords separated by commas.", fg='gray').grid(row=3, column=0, columnspan=2, pady=5)

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", style='Accent.TButton', command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)

        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()

    # Update or create category and handle unique-name constraints
    def save(self):
        current_cat_names = [c['name'].lower() for c in self.categories]
        new_name = self.name_var.get()
        if self.category: # Updated and existing category
            # Check for duplicate category names
            if new_name.lower() != self.category['name'].lower() and new_name.lower() in current_cat_names:
                messagebox.showerror("Error", "Category already exists")
                return
            if not new_name: # Reject if entered empty name
                messagebox.showerror("Error", "Category name is required")
                return
            self.db.update_category(
                category_id=self.category['id'],
                name=new_name,
                cat_type=self.type_var.get().lower(),
                keywords=self.keywords_var.get()
            )
        else: # Adding new category
            if new_name.lower() in current_cat_names:
                messagebox.showerror("Error", "Category already exists")
                return
            if not new_name: # Reject if entered empty name
                messagebox.showerror("Error", "Category name is required")
                return
            self.db.add_category(
                name=new_name,
                cat_type=self.type_var.get().lower(),
                keywords=self.keywords_var.get()
            )
            
        if self.callback:
            self.callback()
            
        self.dialog.destroy()
