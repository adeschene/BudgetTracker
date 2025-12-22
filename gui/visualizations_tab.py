import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from database.db_manager import DatabaseManager

class VisualizationsTab:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        self.frame = tk.Frame(parent)

        self.setup_ui()

    def setup_ui(self):
        control_frame = tk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(control_frame, text="Net Worth Over Time", font=('Arial', 12, 'bold')).pack(side='left', padx=5)
        tk.Button(control_frame, text="Refresh", command=self.refresh_charts).pack(side='right', padx=5)

        net_worth_frame = tk.Frame(self.frame)
        net_worth_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.figure1 = Figure(figsize=(10, 4), dpi=100)
        self.ax1 = self.figure1.add_subplot(111)

        self.canvas1 = FigureCanvasTkAgg(self.figure1, net_worth_frame)
        self.canvas1.get_tk_widget().pack(fill='both', expand=True)

        expense_control_frame = tk.Frame(self.frame)
        expense_control_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(expense_control_frame, text="Expense Breakdown by Category", font=('Arial', 12, 'bold')).pack(side='left', padx=5)

        tk.Label(expense_control_frame, text="Period:").pack(side='left', padx=(20, 5))
        self.period_var = tk.StringVar(value='This Month')
        period_combo = ttk.Combobox(expense_control_frame, textvariable=self.period_var, width=15, state='readonly')
        period_combo['values'] = ['This Month', 'Last Month', 'This Year', 'Last Year', 'All Time']
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_expense_chart())

        expense_frame = tk.Frame(self.frame)
        expense_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.figure2 = Figure(figsize=(10, 4), dpi=100)
        self.ax2 = self.figure2.add_subplot(111)

        self.canvas2 = FigureCanvasTkAgg(self.figure2, expense_frame)
        self.canvas2.get_tk_widget().pack(fill='both', expand=True)

        self.refresh_charts()

    def get_date_range(self):
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
        else:
            return None, None

        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    def refresh_charts(self):
        self.refresh_net_worth_chart()
        self.refresh_expense_chart()

    def refresh_net_worth_chart(self):
        self.ax1.clear()

        history = self.db.get_net_worth_history()

        if not history:
            self.ax1.text(0.5, 0.5, 'No net worth data available',
                        ha='center', va='center', transform=self.ax1.transAxes,
                        fontsize=14, color='gray')
            self.canvas1.draw()
            return

        months = [h['month'] for h in history]
        totals = [h['total'] for h in history]

        month_labels = []
        for month in months:
            year, month_num = month.split('-')
            date_obj = datetime(int(year), int(month_num), 1)
            month_labels.append(date_obj.strftime('%b %Y'))

        colors = ['green' if total >= 0 else 'red' for total in totals]

        bars = self.ax1.bar(range(len(months)), totals, color=colors, alpha=0.7, edgecolor='black')

        self.ax1.set_xlabel('Month', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('Net Worth ($)', fontsize=12, fontweight='bold')
        self.ax1.set_title('Net Worth Over Time', fontsize=14, fontweight='bold', pad=20)

        self.ax1.set_xticks(range(len(months)))
        self.ax1.set_xticklabels(month_labels, rotation=45, ha='right')

        self.ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

        self.ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        self.ax1.grid(True, axis='y', alpha=0.3, linestyle='--')

        for i, (bar, total) in enumerate(zip(bars, totals)):
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'${total:,.0f}',
                        ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9, fontweight='bold')

        self.figure1.tight_layout()
        self.canvas1.draw()

    def refresh_expense_chart(self):
        self.ax2.clear()

        start_date, end_date = self.get_date_range()
        spending = self.db.get_spending_by_category(start_date, end_date)

        if not spending:
            self.ax2.text(0.5, 0.5, 'No expense data available for this period',
                        ha='center', va='center', transform=self.ax2.transAxes,
                        fontsize=14, color='gray')
            self.canvas2.draw()
            return

        categories = list(spending.keys())
        amounts = list(spending.values())

        colors = plt.cm.Set3(range(len(categories)))

        wedges, texts, autotexts = self.ax2.pie(amounts, labels=categories, autopct='%1.1f%%',
                                                colors=colors, startangle=90, textprops={'fontsize': 10})

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)

        period_label = self.period_var.get()
        self.ax2.set_title(f'Expenses by Category - {period_label}', fontsize=14, fontweight='bold', pad=20)

        self.figure2.tight_layout()
        self.canvas2.draw()
