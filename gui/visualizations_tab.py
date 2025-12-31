import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from decimal import Decimal
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from database.db_manager import DatabaseManager
from utils.helpers import fuzzy_match, exact_match

class VisualizationsTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs) # Initialize tab frame
        self.db = db

        self.setup_ui()

    def setup_ui(self):
        # Shared controls above tabs
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=10, pady=6)

        ttk.Label(control_frame, text='Period:').pack(side='left', padx=(4, 6))
        self.period_var = tk.StringVar(value='All Time')
        period_combo = ttk.Combobox(control_frame, textvariable=self.period_var, width=18, state='readonly')
        period_combo['values'] = ['This Month', 'Last Month', 'Last Two Months', 'Last Three Months', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left')
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.on_period_change())

        ttk.Separator(control_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        # Custom date range pickers (toggled on/off based on period selection)
        ttk.Label(control_frame, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(control_frame, width=10, firstweekday='sunday',
                                        background='#232323', foreground='whitesmoke',
                                        headersbackground='#454545', headersforeground='whitesmoke',
                                        othermonthwebackground='#565656', othermonthweforeground='whitesmoke',
                                        weekendbackground='#666666', weekendforeground='whitesmoke',
                                        othermonthbackground='#777777', othermonthforeground='#232323',
                                        normalbackground='#888888', normalforeground='black',
                                        disableddaybackground='#454545', disableddayforeground='#888888',
                                        bordercolor='#343434', borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now(), day=1)
        self.start_date_picker.pack(side='left', padx=5)
        self.start_date_picker.bind("<<DateEntrySelected>>", lambda e: self.on_inner_tab_change(None))

        ttk.Label(control_frame, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(control_frame, width=10, firstweekday='sunday',
                                        background='#232323', foreground='whitesmoke',
                                        headersbackground='#454545', headersforeground='whitesmoke',
                                        othermonthwebackground='#565656', othermonthweforeground='whitesmoke',
                                        weekendbackground='#666666', weekendforeground='whitesmoke',
                                        othermonthbackground='#777777', othermonthforeground='#232323',
                                        normalbackground='#888888', normalforeground='black',
                                        disableddaybackground='#454545', disableddayforeground='#888888',
                                        bordercolor='#343434', borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=5)
        self.end_date_picker.bind("<<DateEntrySelected>>", lambda e: self.on_inner_tab_change(None))

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        # Create notebook to hold multiple chart tabs
        self.inner_notebook = ttk.Notebook(self)
        self.inner_notebook.pack(fill='both', expand=True, padx=10, pady=4)

        self.chart_map = {} # Tab-to-function mapping dictionary

        # --- Net Worth Tab ---
        net_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(net_tab, text='Net Worth Over Time')
        net_worth_frame = ttk.Frame(net_tab)
        net_worth_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure1 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax1 = self.figure1.add_subplot(111, facecolor='#444445')
        self.canvas1 = FigureCanvasTkAgg(self.figure1, net_worth_frame)
        self.canvas1.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(net_tab)] = self.refresh_net_worth_chart

        # --- Income, Expenses, & Savings Tab ---
        mixed_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(mixed_tab, text='Money In/Out')
        mixed_frame = ttk.Frame(mixed_tab)
        mixed_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure2 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax2 = self.figure2.add_subplot(111, facecolor='#444445')
        self.canvas2 = FigureCanvasTkAgg(self.figure2, mixed_frame)
        self.canvas2.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(mixed_tab)] = self.refresh_mixed_chart

        # --- Income Over Time Tab ---
        income_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(income_tab, text='Income')
        income_frame = ttk.Frame(income_tab)
        income_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure3 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax3 = self.figure3.add_subplot(111, facecolor='#444445')
        self.canvas3 = FigureCanvasTkAgg(self.figure3, income_frame)
        self.canvas3.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(income_tab)] = self.refresh_income_chart

        # --- Expenses Over Time Tab ---
        expenses_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(expenses_tab, text='Expenses')
        expenses_time_frame = ttk.Frame(expenses_tab)
        expenses_time_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure4 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax4 = self.figure4.add_subplot(111, facecolor='#444445')
        self.canvas4 = FigureCanvasTkAgg(self.figure4, expenses_time_frame)
        self.canvas4.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(expenses_tab)] = self.refresh_expenses_chart

        # --- Savings Over Time Tab ---
        savings_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(savings_tab, text='Savings')
        savings_frame = ttk.Frame(savings_tab)
        savings_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure5 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax5 = self.figure5.add_subplot(111, facecolor='#444445')
        self.canvas5 = FigureCanvasTkAgg(self.figure5, savings_frame)
        self.canvas5.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(savings_tab)] = self.refresh_savings_chart

        # --- Expense Breakdown Tab (pie) ---
        expense_bd_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(expense_bd_tab, text='Expense Breakdown')
        expense_frame = ttk.Frame(expense_bd_tab)
        expense_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure6 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax6 = self.figure6.add_subplot(111, facecolor='#444445')
        self.canvas6 = FigureCanvasTkAgg(self.figure6, expense_frame)
        self.canvas6.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(expense_bd_tab)] = self.refresh_expense_breakdown_chart

        # --- Income Breakdown Tab (pie) ---
        income_bd_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(income_bd_tab, text='Income Breakdown')
        income_pie_frame = ttk.Frame(income_bd_tab)
        income_pie_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure7 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax7 = self.figure7.add_subplot(111, facecolor='#444445')
        self.canvas7 = FigureCanvasTkAgg(self.figure7, income_pie_frame)
        self.canvas7.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(income_bd_tab)] = self.refresh_income_breakdown_chart

        # --- Category Drill Down Tab ---
        cat_bd_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(cat_bd_tab, text='Category Drill Down')
        cat_control = ttk.Frame(cat_bd_tab)
        cat_control.pack(fill='x', padx=5, pady=5)

        ttk.Label(cat_control, text='Category:').pack(side='left', padx=(4, 6))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_control, textvariable=self.category_var, width=30, state='readonly')
        self.category_combo.pack(side='left')
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_category_drilldown_chart())

        cat_frame = ttk.Frame(cat_bd_tab)
        cat_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure8 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax8 = self.figure8.add_subplot(111, facecolor='#444445')
        self.canvas8 = FigureCanvasTkAgg(self.figure8, cat_frame)
        self.canvas8.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(cat_bd_tab)] = self.refresh_category_drilldown_chart

        # --- Keyword Drill Down Tab ---
        kw_bd_tab = ttk.Frame(self.inner_notebook)
        self.inner_notebook.add(kw_bd_tab, text='Keyword Drill Down')
        kw_control = ttk.Frame(kw_bd_tab)
        kw_control.pack(fill='x', padx=5, pady=5)

        ttk.Label(kw_control, text='Keyword:').pack(side='left', padx=(4, 6))
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(kw_control, textvariable=self.keyword_var, width=40)
        self.keyword_entry.pack(side='left')
        self.keyword_entry.bind('<Return>', lambda e: self.refresh_keyword_drilldown_chart())

        # Exact match enabled by default; fuzzy match optional with configurable threshold
        self.exact_match_var = tk.BooleanVar(value=True)
        self.fuzzy_match_var = tk.BooleanVar(value=False)

        def _on_fuzzy_toggle():
            if self.fuzzy_match_var.get():
                self.exact_match_var.set(False)
                try:
                    self.fuzzy_threshold_scale.configure(state='normal')
                    self.refresh_keyword_drilldown_chart()
                except Exception:
                    pass
            else:
                self.exact_match_var.set(True)
                try:
                    self.fuzzy_threshold_scale.configure(state='disabled')
                except Exception:
                    pass

        def _on_exact_toggle():
            if self.exact_match_var.get():
                self.fuzzy_match_var.set(False)
                try:
                    self.fuzzy_threshold_scale.configure(state='disabled')
                    self.refresh_keyword_drilldown_chart()
                except Exception:
                    pass

        ttk.Checkbutton(kw_control, text='Exact Match', variable=self.exact_match_var, command=_on_exact_toggle).pack(side='left', padx=(10, 5))
        ttk.Checkbutton(kw_control, text='Fuzzy Match', variable=self.fuzzy_match_var, command=_on_fuzzy_toggle).pack(side='left', padx=(6, 5))

        # Fuzzy threshold control (disabled unless fuzzy match enabled)
        self.fuzzy_threshold_var = tk.DoubleVar(value=0.9)
        self.fuzzy_threshold_scale = ttk.Scale(kw_control, from_=0.1, to=1.0, orient='horizontal', variable=self.fuzzy_threshold_var)
        self.fuzzy_threshold_scale.pack(side='left', padx=(6, 5))
        self.fuzzy_threshold_scale.configure(length=140, state='disabled')
        self.fuzzy_threshold_label = ttk.Label(kw_control, text=f'Threshold: {self.fuzzy_threshold_var.get():.2f}')
        self.fuzzy_threshold_label.pack(side='left', padx=(4, 0))

        # Dynamic update of threshold label as the user adjusts the scale
        def _update_threshold_label(val):
            try:
                self.fuzzy_threshold_label.config(text=f'Threshold: {float(val):.2f}')
            except Exception:
                pass

        # Refreshes the chart when the user releases the mouse after adjusting the scale
        def _on_fuzzy_threshold_release(event):
            self.refresh_keyword_drilldown_chart()

        self.fuzzy_threshold_scale.configure(command=_update_threshold_label)
        self.fuzzy_threshold_scale.bind('<ButtonRelease-1>', _on_fuzzy_threshold_release)

        ttk.Button(kw_control, text='Clear', command=self._clear_keyword_drilldown_vals).pack(side='right', padx=5)

        kw_frame = ttk.Frame(kw_bd_tab)
        kw_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure9 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax9 = self.figure9.add_subplot(111, facecolor='#444445')
        self.canvas9 = FigureCanvasTkAgg(self.figure9, kw_frame)
        self.canvas9.get_tk_widget().pack(fill='both', expand=True)
        self.chart_map[str(kw_bd_tab)] = self.refresh_keyword_drilldown_chart

        self.inner_notebook.bind("<<NotebookTabChanged>>", self.on_inner_tab_change)

    # Refresh only the currently visible chart
    def on_inner_tab_change(self, event):
        selected_tab_id = self.inner_notebook.select()
        # Look up the refresh function in the map and run it
        if selected_tab_id in self.chart_map:
            refresh_function = self.chart_map[selected_tab_id]
            refresh_function()

    # Initial draw of all charts using current default period
    def on_tab_opened(self): # Trigger refresh when switching to tab from another
        self.on_inner_tab_change(None)

    # Enable date pickers when using custom timeframe
    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='normal')
            self.end_date_picker.config(state='normal')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        # Refresh active chart whenever the selected period changes
        self.on_inner_tab_change(None)

    def get_date_range(self):
        # Determine start and end dates based on selected period or custom range
        today = datetime.now()
        period = self.period_var.get()

        match period:
            case 'This Month':
                start = today.replace(day=1)
                end = today
            case 'Last Month':
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                start = last_month_end.replace(day=1)
                end = last_month_end
            case 'Last Two Months':
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                start = last_month_end.replace(day=1)
                end = today
            case 'Last Three Months':
                this_month = today.month
                this_year = today.year
                match this_month:
                    case 2: start_month = 12
                    case 1: start_month = 11
                    case _: start_month = this_month - 2
                start_year = this_year - 1 if start_month == (12 or 11) else this_year
                start = today.replace(year=start_year, month=start_month, day=1)
                end = today
            case 'This Year':
                start = today.replace(month=1, day=1)
                end = today
            case 'Last Year':
                start = today.replace(year=today.year-1, month=1, day=1)
                end = today.replace(year=today.year-1, month=12, day=31)
            case 'Custom':
                start = self.start_date_picker.get_date()
                end = self.end_date_picker.get_date()
            case _: # All Time chosen, handled case-by-case in refresh methods
                return None, None

        # Return ISO date strings useful for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    def _month_range(self, start_date: str, end_date: str):
        # return list of YYYY-MM strings from start to end inclusive
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        months = []
        cur = start.replace(day=1)
        while cur <= end:
            months.append(cur.strftime('%Y-%m'))
            if cur.month == 12:
                cur = cur.replace(year=cur.year+1, month=1)
            else:
                cur = cur.replace(month=cur.month+1)
        return months

    def _aggregate_monthly(self, transactions, kind='all'):
        # Aggregate transactions into monthly buckets (YYYY-MM) and sum amounts.
        # `kind` can be 'income', 'expense' or 'all' to filter by sign.
        data = {}
        for t in transactions:
            try:
                raw_date = t['date']

                # Normalize date data regardless of format
                try:
                    dt = datetime.strptime(raw_date, '%Y-%m-%d')
                except ValueError:
                    dt = datetime.strptime(raw_date, '%m-%d-%Y')

                key = dt.strftime('%Y-%m')

                amt = Decimal(t['amount'])/100
            except Exception:
                continue

            # Kind filtering, also skipping $0 transactions
            if kind == 'income' and amt <= 0:
                continue
            if kind == 'expense' and amt >= 0:
                continue

            # Expenses stored negative; for expense chart use abs
            value = amt if kind != 'expense' else abs(amt)

            data[key] = Decimal(data.get(key, 0.0)) + value

        return data

    def _get_transactions_in_range(self, start_date, end_date):
        # Use db.get_transactions to retrieve transactions in range
        if start_date and end_date:
            return self.db.get_transactions(start_date, end_date)
        else:
            return self.db.get_transactions()

    def _update_category_list(self):
        cats = self.db.get_categories()
        names = [c['name'] for c in cats]
        self.category_combo['values'] = names
        if names:
            # Keep current selection if valid, otherwise select first
            cur = self.category_var.get()
            if cur not in names:
                self.category_var.set(names[0])

    def _clear_keyword_drilldown_vals(self):
        self.keyword_var.set('')
        self.fuzzy_threshold_var.set(0.9)
        self.fuzzy_threshold_label.config(text=f'Threshold: {self.fuzzy_threshold_var.get():.2f}')
        self.exact_match_var.set(True)
        self.fuzzy_match_var.set(False)
        self.fuzzy_threshold_scale.configure(state='disabled')
        self.refresh_keyword_drilldown_chart()

    def refresh_net_worth_chart(self):
            # Grouped bar chart showing assets, liabilities and net worth over time
            self.ax1.clear()

            # Respect selected period (start/end) if provided; otherwise use all history
            start_date, end_date = self.get_date_range()

            history = self.db.get_net_worth_history() # Get all net worth entries in DB

            if not start_date and not end_date and history: # All Time handling
                first_entry_partial_date = history[0]['month']
                start_date = f'{first_entry_partial_date[:4]}-{first_entry_partial_date[5:7]}-1'
                end_date = datetime.now().strftime('%Y-%m-%d')

            # If a specific date range is selected, filter the month-level history
            if start_date and end_date and history:
                start_month = start_date[:7]
                end_month = end_date[:7]
                filtered = [h for h in history if start_month <= h.get('month', '') <= end_month]
                if filtered:
                    # Add in months with no entries
                    months_in_range = self._month_range(start_date, end_date)
                    all_month_dicts = [{'month': m, 'total': 0.0, 'breakdown': {}} for m in months_in_range]
                    lookup = {d['month']: d for d in filtered}
                    missing_added = [lookup.get(d['month'], d) for d in all_month_dicts]
                    history = missing_added
                else: # Don't draw graph unless we have at least one entry to show
                    history = filtered

            if not history:
                self.ax1.text(0.5, 0.5, 'No data available for selected period',
                            ha='center', va='center', transform=self.ax1.transAxes,
                            fontsize=14, color='whitesmoke')
                self.ax1.set_axis_off()
                self.canvas1.draw()
                return

            # `History` is expected to be list of dicts with 'month' and 'breakdown'
            months = [h['month'] for h in history]

            # Compute assets, liabilities, and net for each month
            assets = []
            liabilities = []
            net = []
            for h in history:
                breakdown = h.get('breakdown', {}) or {}
                # Assets: sum of non-negative values; liabilities: sum of negative values (keep negative)
                a = sum(v for v in breakdown.values() if v and v >= 0)
                l = sum(v for v in breakdown.values() if v and v < 0)
                assets.append(a)
                liabilities.append(l)  # l will be negative or 0
                # Net: prefer provided total, otherwise sum of breakdown
                net_val = h.get('total')
                if net_val is None:
                    net_val = sum(v for v in breakdown.values() if v)
                net.append(net_val)

            # Labels
            month_labels = []
            for month in months:
                year, month_num = month.split('-')
                date_obj = datetime(int(year), int(month_num), 1)
                month_labels.append(date_obj.strftime('%b %Y'))

            x = range(len(months))
            width =0.2

            # Plot grouped bars: assets, liabilities, net
            bars_a = self.ax1.bar([i - width for i in x], assets, width=width, color='tab:green', label='Assets', edgecolor='whitesmoke', alpha=0.8)
            bars_l = self.ax1.bar(x, liabilities, width=width, color='tab:red', label='Liabilities', edgecolor='whitesmoke', alpha=0.8)
            bars_n = self.ax1.bar([i + width for i in x], net, width=width, color='tab:blue', label='Net Worth', edgecolor='whitesmoke', alpha=0.8)
            
            # Compute averages and draw dashed lines for each (liabilities average will be negative)
            avg_a = sum(assets) / len(assets) if assets else 0.0
            avg_l = sum(liabilities) / len(liabilities) if liabilities else 0.0
            avg_n = sum(net) / len(net) if net else 0.0

            # Average lines
            self.ax1.axhline(y=avg_a, color='tab:green', linestyle='--', linewidth=1)
            self.ax1.axhline(y=avg_l, color='tab:red', linestyle='--', linewidth=1)
            self.ax1.axhline(y=avg_n, color='tab:blue', linestyle='--', linewidth=1)

            # Origin line
            self.ax1.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

            if start_date and end_date:
                formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
                formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            self.ax1.set_title('Net Worth Breakdown\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')

            self.ax1.set_xticks(range(len(months)))
            self.ax1.set_xticklabels(month_labels, rotation=90) # Use vertical month labels

            # Formatting
            self.ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            self.ax1.grid(True, axis='y', alpha=0.3, linestyle=':')
            self.ax1.legend(facecolor='#313131', edgecolor='whitesmoke', labelcolor='whitesmoke')

            # Coloring
            self.ax1.spines['top'].set_color('whitesmoke')
            self.ax1.spines['left'].set_color('whitesmoke')
            self.ax1.tick_params(axis='x', colors='whitesmoke')
            self.ax1.tick_params(axis='y', colors='whitesmoke')
            self.ax1.xaxis.label.set_color("whitesmoke")
            self.ax1.yaxis.label.set_color("whitesmoke")

            # Annotate bar values
            padding = 6 # Additional space between bars and $ labels

            for bar in bars_a:
                hgt = bar.get_height()
                if hgt > 0: # Don't label zero values, assets should always be positive, place label above bar
                    self.ax1.text(bar.get_x() + bar.get_width()/2., hgt + padding, f'${hgt:,.0f}', ha='center', va='bottom', fontsize=8, color='whitesmoke')

            for bar in bars_l:
                hgt = bar.get_height()
                if hgt < 0: # Liabilities should be negative; place label below the bar
                    self.ax1.text(bar.get_x() + bar.get_width()/2., hgt - padding, f'${hgt:,.0f}', ha='center', va='top', fontsize=8, color='whitesmoke')

            for bar in bars_n:
                hgt = bar.get_height()
                y_pos = hgt + padding if hgt > 0 else hgt - padding
                if hgt != 0: # Net value varies, place label according to value, but don't label zeroes regardless
                    self.ax1.text(bar.get_x() + bar.get_width()/2., y_pos, f'${hgt:,.0f}', ha='center', va='bottom' if hgt > 0 else 'top', fontsize=8, color='whitesmoke')

            self.canvas1.draw()

    # Shows income, expenses, and savings in a bar chart, adjusted for the chosen period
    def refresh_mixed_chart(self):
        # Grouped bar chart showing assets, liabilities and net worth over time
        self.ax2.clear()

        # Respect selected period (start/end) if provided; otherwise use all history
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)

        if not tx:
            self.ax2.text(0.5, 0.5, 'No data available for selected period', ha='center', va='center', transform=self.ax2.transAxes, fontsize=14, color='whitesmoke')
            self.ax2.set_axis_off()
            self.canvas2.draw()
            return

        # Get dollar value lists for income, expenses, and both mixed together
        income = [Decimal(t['amount'])/100 for t in tx if t['transaction_type'] == 'income']
        expenses = [Decimal(t['amount'])/100 for t in tx if t['transaction_type'] == 'expense']
        all_vals = income + expenses

        # Get total values for bars
        total_income = sum(income)
        total_expenses = sum(expenses)
        total_savings = sum(all_vals)

        # Bar variables
        values = [total_income,total_expenses,total_savings]
        width = 1.0
        colors = ['tab:green','tab:red','tab:blue']

        # Plot bars for income, expenses, and savings
        bars = self.ax2.bar(range(len(values)), values, width=width, color=colors, edgecolor='whitesmoke', alpha=0.8)

        # Origin line
        self.ax2.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax2.set_title('Total Income, Expenses & Savings\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        # Label setup
        labels = ['Income','Expenses','Savings']
        self.ax2.set_xticks(range(len(labels)))
        self.ax2.set_xticklabels(labels)

        # Formatting
        self.ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax2.grid(True, axis='y', alpha=0.3, linestyle=':')
        #self.ax2.legend(facecolor='#313131', edgecolor='whitesmoke', labelcolor='whitesmoke')

        # Coloring
        self.ax2.spines['top'].set_color('whitesmoke')
        self.ax2.spines['left'].set_color('whitesmoke')
        self.ax2.tick_params(axis='x', colors='whitesmoke')
        self.ax2.tick_params(axis='y', colors='whitesmoke')
        self.ax2.xaxis.label.set_color("whitesmoke")
        self.ax2.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        padding = 80 # Additional space between bars and $ labels

        for bar in bars:
            hgt = bar.get_height()
            y_pos = hgt + padding if hgt > 0 else hgt - padding
            if hgt != 0: # Value sign varies, place label according to value, but don't label zeroes regardless
                self.ax2.text(bar.get_x() + bar.get_width()/2., y_pos, f'${hgt:,.0f}', ha='center', va='bottom' if hgt > 0 else 'top', fontsize=8, color='whitesmoke')

        self.canvas2.draw()


    def refresh_income_chart(self):
        # Line/bar chart showing income totals per month
        self.ax3.clear()
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)
        monthly = self._aggregate_monthly(tx, kind='income')

        if not monthly:
            self.ax3.text(0.5, 0.5, 'No data available for selected period', ha='center', va='center', transform=self.ax3.transAxes, fontsize=14, color='whitesmoke')
            self.ax3.set_axis_off()
            self.canvas3.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        values = [monthly.get(m, 0.0) for m in months]
        
        # Formatting/Creating bars
        bars = self.ax3.bar(range(len(months)), values, color='green', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Average line
        self.ax3.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax3.set_title('Income Over Time\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')

        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax3.set_xticks(range(len(months)))
        self.ax3.set_xticklabels(labels, rotation=90) # Use vertical month labels

        # Formatting
        self.ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax3.grid(True, axis='y', alpha=0.3, linestyle=':')

        # Coloring
        self.ax3.spines['top'].set_color('whitesmoke')
        self.ax3.spines['left'].set_color('whitesmoke')
        self.ax3.tick_params(axis='x', colors='whitesmoke')
        self.ax3.tick_params(axis='y', colors='whitesmoke')
        self.ax3.xaxis.label.set_color("whitesmoke")
        self.ax3.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        ignore_zeroes = [f'${v:,.2f}' if v > 0 else '' for v in values]
        self.ax3.bar_label(bars, labels=ignore_zeroes, padding=3, color='whitesmoke', fontsize=8)

        self.canvas3.draw() # Redraw canvas with updated chart
    
    def refresh_expenses_chart(self):
        # Bar chart showing expense totals per month
        self.ax4.clear()
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)
        monthly = self._aggregate_monthly(tx, kind='expense')

        if not monthly:
            self.ax4.text(0.5, 0.5, 'No data available for selected period', ha='center', va='center', transform=self.ax4.transAxes, fontsize=14, color='whitesmoke')
            self.ax4.set_axis_off()
            self.canvas4.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        values = [monthly.get(m, 0.0) for m in months]

        bars = self.ax4.bar(range(len(months)), values, color='red', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0
        self.ax4.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)
        
        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax4.set_title('Expenses Over Time\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax4.set_xticks(range(len(months)))
        self.ax4.set_xticklabels(labels, rotation=90) # Use vertical month labels

        # Formatting
        self.ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax4.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax4.spines['top'].set_color('whitesmoke')
        self.ax4.spines['left'].set_color('whitesmoke')
        self.ax4.tick_params(axis='x', colors='whitesmoke')
        self.ax4.tick_params(axis='y', colors='whitesmoke')
        self.ax4.xaxis.label.set_color("whitesmoke")
        self.ax4.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        ignore_zeroes = [f'${v:,.2f}' if v > 0 else '' for v in values]
        self.ax4.bar_label(bars, labels=ignore_zeroes, padding=3, color='whitesmoke', fontsize=8)

        self.canvas4.draw()

    def refresh_savings_chart(self):
        # Savings = income - expenses per month
        self.ax5.clear()
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)

        # aggregate incomes and expenses per month
        income_monthly = self._aggregate_monthly(tx, kind='income')
        expense_monthly = self._aggregate_monthly(tx, kind='expense')

        if not income_monthly and not expense_monthly:
            self.ax5.text(0.5, 0.5, 'No data available for selected period', 
                          ha='center', va='center', transform=self.ax5.transAxes, 
                          fontsize=14, color='whitesmoke')
            self.ax5.set_axis_off()
            self.canvas5.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(set(list(income_monthly.keys()) + list(expense_monthly.keys())))

        values = [(income_monthly.get(m, 0.0) - expense_monthly.get(m, 0.0)) for m in months]
        bars = self.ax5.bar(range(len(months)), values, color=['green' if v>=0 else 'red' for v in values], alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Origin line
        self.ax5.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)
        # Average line
        self.ax5.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax5.set_title('Savings Over Time\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax5.set_xticks(range(len(months)))
        self.ax5.set_xticklabels(labels, rotation=90) # Use vertical month labels

        # Formatting
        self.ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax5.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax5.spines['top'].set_color('whitesmoke')
        self.ax5.spines['left'].set_color('whitesmoke')
        self.ax5.tick_params(axis='x', colors='whitesmoke')
        self.ax5.tick_params(axis='y', colors='whitesmoke')
        self.ax5.xaxis.label.set_color("whitesmoke")
        self.ax5.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        padding = 10 # Additional space between bars and $ labels
        for bar in bars:
            hgt = bar.get_height()
            y_pos = hgt + padding if hgt > 0 else hgt - padding
            if hgt != 0: # Place label according to value, don't label zeroes
                self.ax5.text(bar.get_x() + bar.get_width()/2., y_pos, f'${hgt:,.0f}', ha='center', va='bottom' if hgt > 0 else 'top', fontsize=8, color='whitesmoke')

        self.canvas5.draw()
    
    def refresh_expense_breakdown_chart(self):
        self.ax6.clear()
        start_date, end_date = self.get_date_range()
        expenses = self.db.get_category_totals_by_type(start_date, end_date, type='expense')
        cat_dict = self.db.get_categories(cat_type='expense') 

        if not expenses or not cat_dict:
            self.ax6.text(0.5, 0.5, 'No data available for selected period',
                        ha='center', va='center', transform=self.ax6.transAxes,
                        fontsize=14, color='whitesmoke')
            self.ax6.set_axis_off()
            self.canvas6.draw()
            return

        categories = [c['name'] for c in cat_dict]
        sorted_cats = sorted(categories, key=lambda c: expenses.get(c, 0.0), reverse=True)

        values = [Decimal(expenses.get(c, 0.0))/100 for c in sorted_cats]
        bars = self.ax6.bar(sorted_cats, values, color='red', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(list(filter(None, values))) / len(list(filter(None, values))) if values else 0.0

        # Average line
        self.ax6.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax6.set_title('Expenses Breakdown\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        self.ax6.set_xticks(range(len(sorted_cats)))
        self.ax6.set_xticklabels(sorted_cats, rotation=45, ha='right') # Use tilted category labels

        # Formatting
        self.ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax6.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax6.spines['top'].set_color('whitesmoke')
        self.ax6.spines['left'].set_color('whitesmoke')
        self.ax6.tick_params(axis='x', colors='whitesmoke')
        self.ax6.tick_params(axis='y', colors='whitesmoke')
        self.ax6.xaxis.label.set_color("whitesmoke")
        self.ax6.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        ignore_zeroes = [f'${v:,.2f}' if v > 0 else '' for v in values]
        self.ax6.bar_label(bars, labels=ignore_zeroes, padding=3, color='whitesmoke', fontsize=8)

        self.canvas6.draw()
    
    def refresh_income_breakdown_chart(self):
        self.ax7.clear()

        start_date, end_date = self.get_date_range()
        income = self.db.get_category_totals_by_type(start_date, end_date, type='income')
        cat_dict = self.db.get_categories(cat_type='income') 

        if not income or not cat_dict:
            self.ax7.text(0.5, 0.5, 'No data available for selected period',
                        ha='center', va='center', transform=self.ax7.transAxes,
                        fontsize=14, color='whitesmoke')
            self.ax7.set_axis_off()
            self.canvas7.draw()
            return

        categories = [c['name'] for c in cat_dict]
        sorted_cats = sorted(categories, key=lambda c: income.get(c, 0.0), reverse=True)

        values = [Decimal(income.get(c, 0.0))/100 for c in sorted_cats]
        bars = self.ax7.bar(sorted_cats, values, color='green', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(list(filter(None, values))) / len(list(filter(None, values))) if values else 0.0

        # Average line
        self.ax7.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax7.set_title('Income Breakdown\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        self.ax7.set_xticks(range(len(sorted_cats)))
        self.ax7.set_xticklabels(sorted_cats, rotation=45, ha='right') # Use tilted category labels

        # Formatting
        self.ax7.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax7.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax7.spines['top'].set_color('whitesmoke')
        self.ax7.spines['left'].set_color('whitesmoke')
        self.ax7.tick_params(axis='x', colors='whitesmoke')
        self.ax7.tick_params(axis='y', colors='whitesmoke')
        self.ax7.xaxis.label.set_color("whitesmoke")
        self.ax7.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        ignore_zeroes = [f'${v:,.2f}' if v > 0 else '' for v in values]
        self.ax7.bar_label(bars, labels=ignore_zeroes, padding=3, color='whitesmoke', fontsize=8)

        self.canvas7.draw()

    def refresh_category_drilldown_chart(self):
        # Draw a bar chart showing monthly totals for the selected category
        self.ax8.clear()
        # ensure category list is up-to-date
        try:
            self._update_category_list()
        except Exception:
            pass

        category = self.category_var.get()
        if not category:
            self.ax8.text(0.5, 0.5, 'Select a category to view spending data', ha='center', va='center', transform=self.ax8.transAxes, fontsize=14, color='whitesmoke')
            self.ax8.set_axis_off()
            self.canvas8.draw()
            return

        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)

        # filter by category (exact match)
        filtered = [t for t in tx if (t.get('category') or '') == category]

        monthly = self._aggregate_monthly(filtered, kind='all')

        if not monthly:
            self.ax8.text(0.5, 0.5, 'No data available for selected category', ha='center', va='center', transform=self.ax8.transAxes, fontsize=14, color='whitesmoke')
            self.ax8.set_axis_off()
            self.canvas8.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        # Use absolute value for display (expenses may be negative in DB)
        values = [abs(monthly.get(m, 0.0)) for m in months]

        # Use a neutral color for category drilldown bars
        bars = self.ax8.bar(range(len(months)), values, color='gray', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Average line
        self.ax8.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        # Add budget line if budget exists for this category
        try:
            budgets = self.db.get_budget_targets()
            budget = next((b for b in budgets if b['category'] == category), None)
            if budget:
                # budget is monthly target; draw as horizontal line
                monthly_budget = budget['monthly_target']
                self.ax8.axhline(y=monthly_budget, color='green', linestyle='-', linewidth=2, label=f'Budget: ${monthly_budget:,.2f}')
                self.ax8.legend(facecolor='#313131', edgecolor='whitesmoke', labelcolor='whitesmoke')
        except Exception:
            pass

        # Origin line
        self.ax8.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax8.set_title(f'Category: {category}\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax8.set_xticks(range(len(months)))
        self.ax8.set_xticklabels(labels, rotation=90) # Use vertical month labels

        # Formatting
        self.ax8.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax8.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax8.spines['top'].set_color('whitesmoke')
        self.ax8.spines['left'].set_color('whitesmoke')
        self.ax8.tick_params(axis='x', colors='whitesmoke')
        self.ax8.tick_params(axis='y', colors='whitesmoke')
        self.ax8.xaxis.label.set_color("whitesmoke")
        self.ax8.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        ignore_zeroes = [f'${v:,.2f}' if v > 0 else '' for v in values]
        self.ax8.bar_label(bars, labels=ignore_zeroes, padding=3, color='whitesmoke', fontsize=8)

        self.canvas8.draw()

    def refresh_keyword_drilldown_chart(self):
        # Draw monthly totals for transactions that match the provided keyword
        self.ax9.clear()
        keyword = self.keyword_var.get().strip()
        if not keyword:
            self.ax9.text(0.5, 0.5, 'Enter a keyword to search transactions', ha='center', va='center', transform=self.ax9.transAxes, fontsize=14, color='whitesmoke')
            self.ax9.set_axis_off()
            self.canvas9.draw()
            return

        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)

        # filter by exact or fuzzy match on description based on checkbox
        use_fuzzy = self.fuzzy_match_var.get()
        if use_fuzzy:
            thresh = float(self.fuzzy_threshold_var.get())
            filtered = [t for t in tx if fuzzy_match(keyword, t.get('description', ''), threshold=thresh)]
        else:
            filtered = [t for t in tx if exact_match(keyword, t.get('description', ''))]

        monthly = self._aggregate_monthly(filtered, kind='all')

        if not monthly:
            self.ax9.text(0.5, 0.5, 'No transactions match keyword', ha='center', va='center', transform=self.ax9.transAxes, fontsize=14, color='whitesmoke')
            self.ax9.set_axis_off()
            self.canvas9.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        values = [monthly.get(m, 0.0) for m in months]
        # Positive amounts shown green (income), negative red (expense)
        colors = ['green' if v >= 0 else 'red' for v in values]

        bars = self.ax9.bar(range(len(months)), values, color=colors, alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Average line
        self.ax9.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        # Origin line
        self.ax9.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

        if start_date and end_date:
            formatted_start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
        self.ax9.set_title(f'Keyword: {keyword}\n' + (f'({formatted_start_date} - {formatted_end_date})' if start_date else '(All Time)'), fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax9.set_xticks(range(len(months)))
        self.ax9.set_xticklabels(labels, rotation=90) # Use vertical month labels

        # Formatting
        self.ax9.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        self.ax9.grid(True, axis='y', alpha=0.3, linestyle=':')

        # Coloring
        self.ax9.spines['top'].set_color('whitesmoke')
        self.ax9.spines['left'].set_color('whitesmoke')
        self.ax9.tick_params(axis='x', colors='whitesmoke')
        self.ax9.tick_params(axis='y', colors='whitesmoke')
        self.ax9.xaxis.label.set_color("whitesmoke")
        self.ax9.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        padding = 5 # Additional space between bars and $ labels
        for bar in bars:
            hgt = bar.get_height()
            y_pos = hgt + padding if hgt > 0 else hgt - padding
            if hgt != 0: # Place label according to value, don't label zeroes
                self.ax9.text(bar.get_x() + bar.get_width()/2., y_pos, f'${hgt:,.0f}', ha='center', va='bottom' if hgt > 0 else 'top', fontsize=8, color='whitesmoke')

        self.canvas9.draw()
