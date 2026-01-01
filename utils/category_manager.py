import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from utils.editable_tree import EditableTree
from utils.helpers import center_window

class CategoryManager:
    def __init__(self, parent, db):
        self.db = db
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Manage Categories")
        self.window.geometry("700x500")
        self.window.transient(parent)

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
    
    def add_category(self):
        dialog = tk.Toplevel(self.window)
        dialog.withdraw()
        dialog.title("Add Category")
        dialog.geometry("300x210")
        
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        type_var = tk.StringVar(value='Expense')
        ttk.Combobox(dialog, textvariable=type_var, values=['Income', 'Expense'], state='readonly').grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        keywords_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        # Save new category to the database and refresh the list
        def save():
            cats = self.db.get_categories()
            current_cat_names = [c['name'] for c in cats]
            if name_var.get() in current_cat_names:
                messagebox.showerror("Error", "Category already exists")
                return
            self.db.add_category(name_var.get(), type_var.get().lower(), keywords_var.get())
            self.refresh_categories()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", style='Accent.TButton', command=save).grid(row=3, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)
        
        dialog.update_idletasks()
        center_window(dialog)
        dialog.deiconify()
        dialog.grab_set()

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

        if not category:
            return

        dialog = tk.Toplevel(self.window)
        dialog.withdraw()
        dialog.title("Edit Category")
        dialog.geometry("300x250")

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_var = tk.StringVar(value=category['name'])
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        type_var = tk.StringVar(value=category['type'].title())
        ttk.Combobox(dialog, textvariable=type_var, values=['Income', 'Expense'], state='readonly').grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        keywords_var = tk.StringVar(value=category.get('keywords', ''))
        ttk.Entry(dialog, textvariable=keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        # Update selected category and handle unique-name constraint
        def save_edit():
            # Check for duplicate category names
            current_cat_names = [c['name'] for c in categories]
            new_name = name_var.get()
            if new_name != category['name'] and new_name in current_cat_names:
                messagebox.showerror("Error", "Category already exists")
                return
            try:
                self.db.update_category(category_id, name_var.get(), type_var.get().lower(), keywords_var.get())
                self.refresh_categories()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category name must be unique") # Should be removed TODO

        tk.Label(dialog, text="Enter keywords separated by commas.", fg='gray').grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(dialog, text="Save", style='Accent.TButton', command=save_edit).grid(row=4, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)

        dialog.update_idletasks()
        center_window(dialog)
        dialog.deiconify()
        dialog.grab_set()

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
        except (ValueError):
            messagebox.showerror("Error", "Invalid value entered")
