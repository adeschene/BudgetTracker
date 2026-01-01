import tkinter as tk
from tkinter import ttk

class EditableTree(ttk.Treeview):
    def __init__(self, master, **kwargs):
        # Extract custom arguments and provide defaults
        self.editable_columns = kwargs.pop('editable_columns', [])
        self.on_commit = kwargs.pop('on_commit_callback', None)
        self.get_options = kwargs.pop('get_options_callback', None)
        self.get_validation = kwargs.pop('get_validation_callback', None)

        # Pass only VALID ttk.Treeview arguments to the superclass
        super().__init__(master, **kwargs)
        
        # Setup bindings
        self.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region != "cell": return

        column_id = self.identify_column(event.x)
        row_id = self.identify_row(event.y)
        col_idx = int(column_id.replace('#', '')) - 1
        col_name = self["columns"][col_idx]

        if col_name not in self.editable_columns: return

        x, y, w, h = self.bbox(row_id, column_id)
        val = self.item(row_id)['values'][col_idx]
        
        # Logic to decide between Combobox and Entry
        options = self.get_options(col_name) if self.get_options else None
        if options:
            self._spawn_combo(row_id, col_name, val, options, x, y, w, h)
        else:
            self._spawn_entry(row_id, col_name, val, x, y, w, h)

    def _spawn_entry(self, row_id, col_name, value, x, y, w, h):
        if col_name == 'Amount' or 'Monthly Target' or 'Value':
            value = str(value).replace('$', '').replace(',', '')

        vcmd = None
        # Check if the parent provided validation info
        if hasattr(self, 'get_validation'):
            # Expecting a tuple: (function, allow_neg_str, allow_dec_str)
            validation_data = self.get_validation(col_name) if self.get_validation else None
            if validation_data:
                func, allow_neg, allow_dec = validation_data
                # Register with substitution codes: %P (value), then your two constants
                vcmd = (self.register(func), '%P', allow_neg, allow_dec)

        entry = ttk.Entry(self, validate='key' if vcmd else 'none', validatecommand=vcmd)
        entry.insert(0, value)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def save(e=None):
            if entry.winfo_exists():
                new_val = entry.get()
                entry.destroy()
                if self.on_commit:
                    self.after_idle(lambda: self.on_commit(row_id, col_name, new_val))

        entry.bind('<Return>', save)
        entry.bind('<FocusOut>', save)
        entry.bind('<Escape>', lambda e: entry.destroy())

    def _spawn_combo(self, row_id, col_name, value, options, x, y, w, h):
        # Create the combobox with provided options
        combo = ttk.Combobox(self, values=options, state="readonly")
        combo.set(value)
        combo.place(x=x, y=y, width=w, height=h)
        combo.focus_set()

        def save(e=None):
            if not combo.winfo_exists():
                return
            # Small delay to let the focus transition settle
            self.after(100, check_focus)

        def check_focus():
            if not combo.winfo_exists():
                return
            
            # Use 'focus_get' and wrap it in a try/except to handle Tcl's 
            # external popdown window names safely
            try:
                focused = self.focus_get()
            except KeyError:
                # If focus_get fails with a KeyError, it usually means 
                # focus is on the Tcl popdown list. Keep the widget alive.
                return

            # If the focus is None (clicked outside window) or not on the combo
            if focused is None or (focused != combo):
                # Verify it's not a 'popdown' string manually
                # (Focus_get might return None if the click was on the dropdown arrow)
                focused_str = str(self.tk.call('focus', '-displayof', self))
                if 'popdown' in focused_str:
                    return

                new_val = combo.get()
                combo.destroy()
                if self.on_commit:
                    self.on_commit(row_id, col_name, new_val)

        def force_save(e=None):
            # Immediate save specifically for the Return key
            if combo.winfo_exists():
                new_val = combo.get()
                combo.destroy()
                if self.on_commit:
                    self.after_idle(lambda: self.on_commit(row_id, col_name, new_val))
            return "break" # Prevents the Combobox from opening its dropdown

        # Bindings
        combo.bind('<<ComboboxSelected>>', lambda e: save())
        combo.bind('<KeyPress-Return>', force_save)
        combo.bind('<FocusOut>', save)
        combo.bind('<Escape>', lambda e: combo.destroy())
