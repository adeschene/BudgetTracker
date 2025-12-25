import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from utils.shared_functions import center_window

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
        
        self.tree = ttk.Treeview(frame, columns=('Name', 'Type', 'Keywords'), show='headings')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Keywords', text='Keywords')
        # Keep Name and Type fixed; let Keywords expand when window is resized
        self.tree.column('Name', width=120, minwidth=75, stretch=False)
        self.tree.column('Type', anchor='center', width=80, minwidth=50, stretch=False)
        self.tree.column('Keywords', width=375, minwidth=100, stretch=True)
        self.tree.pack(fill='both', expand=True)
        
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Add Category", style='Accent.TButton', command=self.add_category).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Edit Category", command=self.edit_category).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Category", command=self.delete_category).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", command=self.window.destroy).pack(side='left', padx=5)
        
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
            self.tree.insert('', 'end', values=(cat['name'], cat['type'], cat['keywords']), tags=(cat['id'],))
    
    def add_category(self):
        dialog = tk.Toplevel(self.window)
        dialog.withdraw()
        dialog.title("Add Category")
        dialog.geometry("300x210")
        
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(dialog, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        type_var = tk.StringVar(value='expense')
        ttk.Combobox(dialog, textvariable=type_var, values=['income', 'expense']).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Label(dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        keywords_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        # Save new category to the database and refresh the list
        def save():
            self.db.add_category(name_var.get(), type_var.get(), keywords_var.get())
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
        type_var = tk.StringVar(value=category['type'])
        ttk.Combobox(dialog, textvariable=type_var, values=['income', 'expense']).grid(row=1, column=1, padx=10, pady=10, sticky='ew')

        ttk.Label(dialog, text="Keywords:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        keywords_var = tk.StringVar(value=category.get('keywords', ''))
        ttk.Entry(dialog, textvariable=keywords_var).grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        # Update selected category and handle unique-name constraint
        def save_edit():
            try:
                self.db.update_category(category_id, name_var.get(), type_var.get(), keywords_var.get())
                self.refresh_categories()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category name must be unique")

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
            messagebox.showwarning("Warning", "Please select a category to delete")
            return

        category_id = int(self.tree.item(selection[0])['tags'][0])
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this category?"):
            self.db.delete_category(category_id)
            self.refresh_categories()
