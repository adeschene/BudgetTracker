import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager

class ReportsTab:
    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        self.frame = tk.Frame(parent)

        self.setup_ui()

    def setup_ui(self):
        control_frame = tk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(control_frame, text="Report Period:").pack(side='left', padx=5)

        self.period_var = tk.StringVar(value='This Month')
        period_combo = ttk.Combobox(control_frame, textvariable=self.period_var, width=15)
        period_combo['values'] = ['This Month', 'Last Month', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)

        tk.Label(control_frame, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(control_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                          maxdate=datetime.now())
        self.start_date_picker.pack(side='left', padx=5)

        tk.Label(control_frame, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(control_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=5)

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        tk.Button(control_frame, text="Generate Report", command=self.generate_report).pack(side='left', padx=5)

        report_frame = tk.Frame(self.frame)
        report_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(report_frame)
        scrollbar.pack(side='right', fill='y')

        self.report_text = tk.Text(report_frame, wrap='word', yscrollcommand=scrollbar.set,
                                   font=('Courier', 10))
        scrollbar.config(command=self.report_text.yview)
        self.report_text.pack(fill='both', expand=True)

        self.generate_report()

    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='normal')
            self.end_date_picker.config(state='normal')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        self.generate_report()

    def get_date_range(self):
        period = self.period_var.get()
        today = datetime.now()

        if period == 'This Month':
            start = today.replace(day=1)
            end = today
        elif period == 'Last Month':
            first_this_month = today.replace(day=1)
            end = first_this_month - timedelta(days=1)
            start = end.replace(day=1)
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

        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    def generate_report(self):
        self.report_text.delete('1.0', 'end')
        
        start_date, end_date = self.get_date_range()
        
        self.report_text.insert('end', "=" * 80 + "\n")
        self.report_text.insert('end', "FINANCIAL REPORT\n")
        self.report_text.insert('end', "=" * 80 + "\n\n")
        
        if start_date and end_date:
            self.report_text.insert('end', f"Period: {start_date} to {end_date}\n\n")
        else:
            self.report_text.insert('end', "Period: All Time\n\n")
        
        transactions = self.db.get_transactions(start_date, end_date)
        
        total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_expenses = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
        net_income = total_income - total_expenses
        
        self.report_text.insert('end', "-" * 80 + "\n")
        self.report_text.insert('end', "INCOME & EXPENSES SUMMARY\n")
        self.report_text.insert('end', "-" * 80 + "\n")
        self.report_text.insert('end', f"Total Income:        ${total_income:>15,.2f}\n")
        self.report_text.insert('end', f"Total Expenses:      ${total_expenses:>15,.2f}\n")
        self.report_text.insert('end', f"Net Income:          ${net_income:>15,.2f}\n\n")
        
        spending_by_category = self.db.get_spending_by_category(start_date, end_date)

        if spending_by_category:
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', "SPENDING BY CATEGORY\n")
            self.report_text.insert('end', "-" * 80 + "\n")

            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)

            for category, amount in sorted_categories:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                self.report_text.insert('end', f"{category:<30} ${amount:>12,.2f}  ({percentage:>5.1f}%)\n")

            self.report_text.insert('end', "\n")

        budget_targets = self.db.get_budget_targets()
        if budget_targets:
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', "BUDGET VS ACTUAL\n")
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', f"{'Category':<30} {'Budget':>12}  {'Actual':>12}  {'Difference':>12}  {'Status':>8}\n")
            self.report_text.insert('end', "-" * 80 + "\n")

            total_budget = 0
            total_actual = 0

            for budget in budget_targets:
                category = budget['category']
                budget_amount = budget['monthly_target']
                actual_amount = spending_by_category.get(category, 0)
                difference = budget_amount - actual_amount

                total_budget += budget_amount
                total_actual += actual_amount

                if difference >= 0:
                    status = "✓ Under"
                    status_color = ""
                else:
                    status = "✗ Over"
                    status_color = ""

                self.report_text.insert('end', f"{category:<30} ${budget_amount:>11,.2f}  ${actual_amount:>11,.2f}  ${difference:>11,.2f}  {status:>8}\n")

            self.report_text.insert('end', "-" * 80 + "\n")
            total_diff = total_budget - total_actual
            self.report_text.insert('end', f"{'TOTAL':<30} ${total_budget:>11,.2f}  ${total_actual:>11,.2f}  ${total_diff:>11,.2f}\n")
            self.report_text.insert('end', "\n")

        income_transactions = [t for t in transactions if t['amount'] > 0]
        if income_transactions:
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', "INCOME BY CATEGORY\n")
            self.report_text.insert('end', "-" * 80 + "\n")
            
            income_by_category = {}
            for trans in income_transactions:
                category = trans['category'] or 'Uncategorized'
                income_by_category[category] = income_by_category.get(category, 0) + trans['amount']
            
            sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_income:
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                self.report_text.insert('end', f"{category:<30} ${amount:>12,.2f}  ({percentage:>5.1f}%)\n")
            
            self.report_text.insert('end', "\n")
        
        accounts = self.db.get_accounts()
        if accounts:
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', "ACCOUNT BALANCES\n")
            self.report_text.insert('end', "-" * 80 + "\n")
            
            total_balance = sum(acc['balance'] for acc in accounts)
            
            for account in accounts:
                self.report_text.insert('end', f"{account['name']:<30} ({account['type']:<15}) ${account['balance']:>12,.2f}\n")
            
            self.report_text.insert('end', f"\n{'Total:':<30} {'':<15} ${total_balance:>12,.2f}\n\n")
        
        net_worth_summary = self.db.get_net_worth_summary(start_date, end_date)
        if net_worth_summary:
            self.report_text.insert('end', "-" * 80 + "\n")
            self.report_text.insert('end', "NET WORTH SUMMARY\n")
            self.report_text.insert('end', "-" * 80 + "\n")
            
            total_net_worth = sum(net_worth_summary.values())
            
            for asset_type, value in sorted(net_worth_summary.items(), key=lambda x: x[1], reverse=True):
                self.report_text.insert('end', f"{asset_type:<30} ${value:>15,.2f}\n")
            
            self.report_text.insert('end', f"\n{'Total Net Worth:':<30} ${total_net_worth:>15,.2f}\n\n")
        
        self.report_text.insert('end', "=" * 80 + "\n")
        self.report_text.insert('end', "END OF REPORT\n")
        self.report_text.insert('end', "=" * 80 + "\n")
