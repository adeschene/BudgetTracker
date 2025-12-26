import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from database.db_manager import DatabaseManager
from utils.helpers import fuzzy_match, exact_match

class VisualizationsTab:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        self.frame = ttk.Frame(parent)

        self.setup_ui()

    def setup_ui(self):
        # Shared controls above tabs
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=6)

        ttk.Label(control_frame, text='Period:').pack(side='left', padx=(4, 6))
        self.period_var = tk.StringVar(value='All Time')
        period_combo = ttk.Combobox(control_frame, textvariable=self.period_var, width=18, state='readonly')
        period_combo['values'] = ['This Month', 'Last Month', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left')
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.on_period_change(e))

        ttk.Separator(control_frame, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        # Custom date range pickers (toggled on/off based on period selection)
        ttk.Label(control_frame, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(control_frame, width=10, background='darkblue',
                                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                          state='disabled')
        self.start_date_picker.pack(side='left', padx=5)

        ttk.Label(control_frame, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(control_frame, width=10, background='darkblue',
                                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                        maxdate=datetime.now(), state='disabled')
        self.end_date_picker.pack(side='left', padx=5)

        ttk.Button(control_frame, text='Refresh', style='Accent.TButton', command=self.refresh_charts).pack(side='right', padx=5)

        # Create notebook to hold multiple chart tabs
        tabs = ttk.Notebook(self.frame)
        tabs.pack(fill='both', expand=True, padx=10, pady=4)

        # --- Net Worth Tab ---
        net_tab = ttk.Frame(tabs)
        tabs.add(net_tab, text='Net Worth Over Time')
        net_worth_frame = ttk.Frame(net_tab)
        net_worth_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure1 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax1 = self.figure1.add_subplot(111, facecolor='#444445')
        self.canvas1 = FigureCanvasTkAgg(self.figure1, net_worth_frame)
        self.canvas1.get_tk_widget().pack(fill='both', expand=True)

        # --- Income Over Time Tab ---
        income_tab = ttk.Frame(tabs)
        tabs.add(income_tab, text='Income Over Time')
        income_frame = ttk.Frame(income_tab)
        income_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure3 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax3 = self.figure3.add_subplot(111, facecolor='#444445')
        self.canvas3 = FigureCanvasTkAgg(self.figure3, income_frame)
        self.canvas3.get_tk_widget().pack(fill='both', expand=True)

        # --- Expenses Over Time Tab ---
        expenses_time_tab = ttk.Frame(tabs)
        tabs.add(expenses_time_tab, text='Expenses Over Time')
        expenses_time_frame = ttk.Frame(expenses_time_tab)
        expenses_time_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure4 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax4 = self.figure4.add_subplot(111, facecolor='#444445')
        self.canvas4 = FigureCanvasTkAgg(self.figure4, expenses_time_frame)
        self.canvas4.get_tk_widget().pack(fill='both', expand=True)

        # --- Savings Over Time Tab ---
        savings_tab = ttk.Frame(tabs)
        tabs.add(savings_tab, text='Savings Over Time')
        savings_frame = ttk.Frame(savings_tab)
        savings_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure5 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax5 = self.figure5.add_subplot(111, facecolor='#444445')
        self.canvas5 = FigureCanvasTkAgg(self.figure5, savings_frame)
        self.canvas5.get_tk_widget().pack(fill='both', expand=True)

        # --- Expense Breakdown Tab (pie) ---
        expense_tab = ttk.Frame(tabs)
        tabs.add(expense_tab, text='Expense Breakdown')
        expense_frame = ttk.Frame(expense_tab)
        expense_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure2 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax2 = self.figure2.add_subplot(111, facecolor='#444445')
        self.canvas2 = FigureCanvasTkAgg(self.figure2, expense_frame)
        self.canvas2.get_tk_widget().pack(fill='both', expand=True)

        # --- Category Drill Down Tab ---
        cat_tab = ttk.Frame(tabs)
        tabs.add(cat_tab, text='Category Drill Down')
        cat_control = ttk.Frame(cat_tab)
        cat_control.pack(fill='x', padx=5, pady=5)

        ttk.Label(cat_control, text='Category:').pack(side='left', padx=(4, 6))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(cat_control, textvariable=self.category_var, width=30, state='readonly')
        self.category_combo.pack(side='left')
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_category_drilldown_chart())

        cat_frame = ttk.Frame(cat_tab)
        cat_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure6 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax6 = self.figure6.add_subplot(111, facecolor='#444445')
        self.canvas6 = FigureCanvasTkAgg(self.figure6, cat_frame)
        self.canvas6.get_tk_widget().pack(fill='both', expand=True)

        # --- Keyword Drill Down Tab ---
        kw_tab = ttk.Frame(tabs)
        tabs.add(kw_tab, text='Keyword Drill Down')
        kw_control = ttk.Frame(kw_tab)
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

        kw_frame = ttk.Frame(kw_tab)
        kw_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.figure7 = Figure(figsize=(10, 4), dpi=100, tight_layout=True, facecolor='#313131')
        self.ax7 = self.figure7.add_subplot(111, facecolor='#444445')
        self.canvas7 = FigureCanvasTkAgg(self.figure7, kw_frame)
        self.canvas7.get_tk_widget().pack(fill='both', expand=True)

        # Initial draw of all charts using current default period (run after layout settles)
        self.frame.after_idle(self.refresh_charts)

    # Enable date pickers when using custom timeframe
    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='normal')
            self.end_date_picker.config(state='normal')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        # Regenerate report whenever the selected period changes
        self.refresh_charts()

    def get_date_range(self):
        # Determine start and end dates based on selected period or custom range
        today = datetime.now()
        period = self.period_var.get()

        if period == 'This Month':
            start = today.replace(day=1)
            end = today
        elif period == 'Last Month':
            first_of_this_month = today.replace(day=1)
            last_month_end = first_of_this_month - timedelta(days=1)
            start = last_month_end.replace(day=1)
            end = last_month_end
        elif period == 'This Year':
            start = today.replace(month=1, day=1)
            end = today
        elif period == 'Last Year':
            start = today.replace(year=today.year-1, month=1, day=1)
            end = today.replace(year=today.year-1, month=12, day=31)
        elif period == 'Custom':
            start_date = self.start_date_picker.get_date()
            end_date = self.end_date_picker.get_date()
            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        else:
            return None, None

        # Return ISO date strings useful for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    def refresh_charts(self):
        # Refresh each visualization panel. Each function queries the DB
        # and redraws its respective matplotlib axes and canvas.
        self.refresh_net_worth_chart()
        self.refresh_income_chart()
        self.refresh_expenses_over_time_chart()
        self.refresh_savings_chart()
        self.refresh_expense_chart()
        self.refresh_category_drilldown_chart()
        self.refresh_keyword_drilldown_chart()

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
                key = t['date'][:7]
                amt = float(t['amount'])
            except Exception:
                continue

            if kind == 'income' and amt <= 0:
                continue
            if kind == 'expense' and amt >= 0:
                continue

            # expenses stored negative; for expense chart use abs
            value = amt if kind != 'expense' else abs(amt)

            data[key] = data.get(key, 0.0) + value

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
            # keep current selection if valid, otherwise select first
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

            history = self.db.get_net_worth_history()

            # If a specific date range is selected, filter the month-level history
            if start_date and end_date and history:
                start_month = start_date[:7]
                end_month = end_date[:7]
                filtered = [h for h in history if start_month <= h.get('month', '') <= end_month]
                history = filtered

            if not history:
                self.ax1.text(0.5, 0.5, 'No net worth data available',
                            ha='center', va='center', transform=self.ax1.transAxes,
                            fontsize=14, color='gray')
                self.ax1.set_axis_off()
                self.canvas1.draw()
                return

            # `history` is expected to be list of dicts with 'month' and 'breakdown'
            months = [h['month'] for h in history]

            # compute assets, liabilities, and net for each month
            assets = []
            liabilities = []
            net = []
            for h in history:
                breakdown = h.get('breakdown', {}) or {}
                # assets: sum of non-negative values; liabilities: sum of negative values (keep negative)
                a = sum(float(v) for v in breakdown.values() if v and float(v) >= 0)
                l = sum(float(v) for v in breakdown.values() if v and float(v) < 0)
                assets.append(a)
                liabilities.append(l)  # l will be negative or 0
                # net: prefer provided total, otherwise sum of breakdown
                net_val = h.get('total')
                if net_val is None:
                    net_val = sum(float(v) for v in breakdown.values() if v)
                net.append(net_val)

            # labels
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

            # compute averages and draw dashed lines for each (liabilities average will be negative)
            avg_a = sum(assets) / len(assets) if assets else 0.0
            avg_l = sum(liabilities) / len(liabilities) if liabilities else 0.0
            avg_n = sum(net) / len(net) if net else 0.0

            # Average lines
            self.ax1.axhline(y=avg_a, color='tab:green', linestyle='--', linewidth=1)
            self.ax1.axhline(y=avg_l, color='tab:red', linestyle='--', linewidth=1)
            self.ax1.axhline(y=avg_n, color='tab:blue', linestyle='--', linewidth=1)

            # Origin line
            self.ax1.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

            self.ax1.set_xlabel('Month', fontsize=12, fontweight='bold')
            self.ax1.set_ylabel('Amount ($)', fontsize=12, fontweight='bold')
            self.ax1.set_title('Net Worth Breakdown Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')

            self.ax1.set_xticks(range(len(months)))
            self.ax1.set_xticklabels(month_labels, rotation=45, ha='right')

            # formatting
            self.ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            self.ax1.grid(True, axis='y', alpha=0.3, linestyle=':')
            self.ax1.legend(facecolor='#313131', edgecolor='whitesmoke', labelcolor='whitesmoke')

            # coloring
            self.ax1.spines['top'].set_color('whitesmoke')
            self.ax1.spines['left'].set_color('whitesmoke')
            self.ax1.tick_params(axis='x', colors='whitesmoke')
            self.ax1.tick_params(axis='y', colors='whitesmoke')
            self.ax1.xaxis.label.set_color("whitesmoke")
            self.ax1.yaxis.label.set_color("whitesmoke")

            # Annotate bar values
            for bar in bars_n:
                hgt = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width()/2., hgt, f'${hgt:,.0f}', ha='center', va='bottom' if hgt >= 0 else 'top', fontsize=8, color='whitesmoke')

            for bar in bars_l:
                hgt = bar.get_height()
                # Liabilities should be negative; place label below the bar
                self.ax1.text(bar.get_x() + bar.get_width()/2., hgt, f'${hgt:,.0f}', ha='center', va='top' if hgt < 0 else 'bottom', fontsize=8, color='whitesmoke')

            for bar in bars_a:
                hgt = bar.get_height()
                self.ax1.text(bar.get_x() + bar.get_width()/2., hgt, f'${hgt:,.0f}', ha='center', va='bottom' if hgt >= 0 else 'top', fontsize=8, color='whitesmoke')

            self.canvas1.draw()

    def refresh_income_chart(self):
        # Line/bar chart showing income totals per month
        self.ax3.clear()
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)
        monthly = self._aggregate_monthly(tx, kind='income')

        if not monthly:
            self.ax3.text(0.5, 0.5, 'No income data available', ha='center', va='center', transform=self.ax3.transAxes, fontsize=14, color='whitesmoke')
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

        self.ax3.set_xlabel('Month')
        self.ax3.set_ylabel('Income ($)')
        self.ax3.set_title('Income Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax3.set_xticks(range(len(months)))
        self.ax3.set_xticklabels(labels, rotation=45, ha='right')
        self.ax3.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax3.spines['top'].set_color('whitesmoke')
        self.ax3.spines['left'].set_color('whitesmoke')
        self.ax3.tick_params(axis='x', colors='whitesmoke')
        self.ax3.tick_params(axis='y', colors='whitesmoke')
        self.ax3.xaxis.label.set_color("whitesmoke")
        self.ax3.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        for bar in bars:
            hgt = bar.get_height()
            self.ax3.text(bar.get_x() + bar.get_width()/2., hgt/2, f'${hgt:,.0f}', ha='center', va='center', fontsize=8, color='whitesmoke')
        
        self.canvas3.draw()
    
    def refresh_expenses_over_time_chart(self):
        # Bar chart showing expense totals per month
        self.ax4.clear()
        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)
        monthly = self._aggregate_monthly(tx, kind='expense')

        if not monthly:
            self.ax4.text(0.5, 0.5, 'No expense data available', ha='center', va='center', transform=self.ax4.transAxes, fontsize=14, color='gray')
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

        self.ax4.set_xlabel('Month')
        self.ax4.set_ylabel('Expenses ($)')
        self.ax4.set_title('Expenses Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax4.set_xticks(range(len(months)))
        self.ax4.set_xticklabels(labels, rotation=45, ha='right')
        self.ax4.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax4.spines['top'].set_color('whitesmoke')
        self.ax4.spines['left'].set_color('whitesmoke')
        self.ax4.tick_params(axis='x', colors='whitesmoke')
        self.ax4.tick_params(axis='y', colors='whitesmoke')
        self.ax4.xaxis.label.set_color("whitesmoke")
        self.ax4.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        for bar in bars:
            hgt = bar.get_height()
            self.ax4.text(bar.get_x() + bar.get_width()/2., hgt/2, f'${hgt:,.0f}', ha='center', va='center', fontsize=8, color='whitesmoke')

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
            self.ax5.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=self.ax5.transAxes, fontsize=14, color='whitesmoke')
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

        self.ax5.set_xlabel('Month')
        self.ax5.set_ylabel('Savings ($)')
        self.ax5.set_title('Savings Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax5.set_xticks(range(len(months)))
        self.ax5.set_xticklabels(labels, rotation=45, ha='right')
        self.ax5.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax5.spines['top'].set_color('whitesmoke')
        self.ax5.spines['left'].set_color('whitesmoke')
        self.ax5.tick_params(axis='x', colors='whitesmoke')
        self.ax5.tick_params(axis='y', colors='whitesmoke')
        self.ax5.xaxis.label.set_color("whitesmoke")
        self.ax5.yaxis.label.set_color("whitesmoke")

        # Annotate bar values
        for bar in bars:
            hgt = bar.get_height()
            self.ax5.text(bar.get_x() + bar.get_width()/2., hgt/2, f'${hgt:,.0f}', ha='center', va='center', fontsize=8, color='whitesmoke')

        self.canvas5.draw()
    
    def refresh_expense_chart(self):
        self.ax2.clear()

        start_date, end_date = self.get_date_range()
        spending = self.db.get_spending_by_category(start_date, end_date)

        if not spending:
            self.ax2.text(0.5, 0.5, 'No expense data available for this period',
                        ha='center', va='center', transform=self.ax2.transAxes,
                        fontsize=14, color='whitesmoke')
            self.ax2.set_axis_off()
            self.canvas2.draw()
            return

        categories = list(spending.keys())
        amounts = list(spending.values())

        colors = plt.cm.Set3(range(len(categories)))

        wedges, texts, autotexts = self.ax2.pie(amounts, autopct='%1.1f%%', pctdistance=1.1,
                                                colors=colors, startangle=90)

        for autotext in autotexts:
            autotext.set_color('whitesmoke')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        period_label = self.period_var.get()
        self.ax2.set_title(f'Expenses by Category - {period_label}', fontsize=14, fontweight='bold', color='whitesmoke', pad=20)

        self.ax2.legend(categories, loc='center left', bbox_to_anchor=(1, 0.75), fontsize=12, facecolor='#444445', edgecolor='whitesmoke', labelcolor='whitesmoke')

        self.canvas2.draw()

    def refresh_category_drilldown_chart(self):
        # Draw a bar chart showing monthly totals for the selected category
        self.ax6.clear()
        # ensure category list is up-to-date
        try:
            self._update_category_list()
        except Exception:
            pass

        category = self.category_var.get()
        if not category:
            self.ax6.text(0.5, 0.5, 'No category selected', ha='center', va='center', transform=self.ax6.transAxes, fontsize=14, color='whitesmoke')
            self.ax6.set_axis_off()
            self.canvas6.draw()
            return

        start_date, end_date = self.get_date_range()
        tx = self._get_transactions_in_range(start_date, end_date)

        # filter by category (exact match)
        filtered = [t for t in tx if (t.get('category') or '') == category]

        monthly = self._aggregate_monthly(filtered, kind='all')

        if not monthly:
            self.ax6.text(0.5, 0.5, 'No data for selected category', ha='center', va='center', transform=self.ax6.transAxes, fontsize=14, color='whitesmoke')
            self.ax6.set_axis_off()
            self.canvas6.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        # Use absolute value for display (expenses may be negative in DB)
        values = [abs(monthly.get(m, 0.0)) for m in months]

        # Use a neutral color for category drilldown bars
        bars = self.ax6.bar(range(len(months)), values, color='gray', alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Average line
        self.ax6.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        # Add budget line if budget exists for this category
        try:
            budgets = self.db.get_budget_targets()
            budget = next((b for b in budgets if b['category'] == category), None)
            if budget:
                # budget is monthly target; draw as horizontal line
                monthly_budget = budget['monthly_target']
                self.ax6.axhline(y=monthly_budget, color='green', linestyle='-', linewidth=2, label=f'Budget: ${monthly_budget:,.2f}')
                self.ax6.legend(facecolor='#313131', edgecolor='whitesmoke', labelcolor='whitesmoke')
        except Exception:
            pass

        # Origin line
        self.ax6.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

        self.ax6.set_xlabel('Month')
        self.ax6.set_ylabel('Amount ($)')
        self.ax6.set_title(f'Category: {category} - Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax6.set_xticks(range(len(months)))
        self.ax6.set_xticklabels(labels, rotation=45, ha='right')
        self.ax6.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax6.spines['top'].set_color('whitesmoke')
        self.ax6.spines['left'].set_color('whitesmoke')
        self.ax6.tick_params(axis='x', colors='whitesmoke')
        self.ax6.tick_params(axis='y', colors='whitesmoke')
        self.ax6.xaxis.label.set_color("whitesmoke")
        self.ax6.yaxis.label.set_color("whitesmoke")

        for bar in bars:
            hgt = bar.get_height()
            self.ax6.text(bar.get_x() + bar.get_width()/2., hgt, f'${hgt:,.2f}', ha='center', va='bottom' if hgt >= 0 else 'top', fontsize=8, color='whitesmoke')

        self.canvas6.draw()

    def refresh_keyword_drilldown_chart(self):
        # Draw monthly totals for transactions that match the provided keyword
        self.ax7.clear()
        keyword = self.keyword_var.get().strip()
        if not keyword:
            self.ax7.text(0.5, 0.5, 'Enter a keyword to search', ha='center', va='center', transform=self.ax7.transAxes, fontsize=14, color='whitesmoke')
            self.ax7.set_axis_off()
            self.canvas7.draw()
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
            self.ax7.text(0.5, 0.5, 'No transactions match keyword', ha='center', va='center', transform=self.ax7.transAxes, fontsize=14, color='whitesmoke')
            self.ax7.set_axis_off()
            self.canvas7.draw()
            return

        if start_date and end_date:
            months = self._month_range(start_date, end_date)
        else:
            months = sorted(monthly.keys())

        values = [monthly.get(m, 0.0) for m in months]
        # Positive amounts shown green (income), negative red (expense)
        colors = ['green' if v >= 0 else 'red' for v in values]

        bars = self.ax7.bar(range(len(months)), values, color=colors, alpha=0.7, edgecolor='whitesmoke')
        avg = sum(values) / len(values) if values else 0.0

        # Average line
        self.ax7.axhline(y=avg, color='whitesmoke', linestyle='--', linewidth=1)

        # Origin line
        self.ax7.axhline(y=0, color='whitesmoke', linestyle='-', linewidth=1)

        self.ax7.set_xlabel('Month')
        self.ax7.set_ylabel('Amount ($)')
        self.ax7.set_title(f'Keyword: "{keyword}" - Over Time', fontsize=14, fontweight='bold', pad=12, color='whitesmoke')
        labels = [datetime.strptime(m + '-01', '%Y-%m-%d').strftime('%b %Y') for m in months]
        self.ax7.set_xticks(range(len(months)))
        self.ax7.set_xticklabels(labels, rotation=45, ha='right')
        self.ax7.grid(True, axis='y', alpha=0.3, linestyle=':')

        # coloring
        self.ax7.spines['top'].set_color('whitesmoke')
        self.ax7.spines['left'].set_color('whitesmoke')
        self.ax7.tick_params(axis='x', colors='whitesmoke')
        self.ax7.tick_params(axis='y', colors='whitesmoke')
        self.ax7.xaxis.label.set_color("whitesmoke")
        self.ax7.yaxis.label.set_color("whitesmoke")

        for bar in bars:
            hgt = bar.get_height()
            self.ax7.text(bar.get_x() + bar.get_width()/2., hgt, f'${hgt:,.2f}', ha='center', va='bottom' if hgt >= 0 else 'top', fontsize=8, color='whitesmoke')

        self.canvas7.draw()
