import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager

class ReportsTab:
    # Class variables
    top_btm_separator_mult = 80 # The number of hyphens used to separate sections in reports
    inner_separator_mult = 160 # The number of '=' used to signal top and bottom of reports

    def __init__(self, parent, db: DatabaseManager):
        self.db = db
        self.frame = ttk.Frame(parent)

        self.setup_ui()

    def setup_ui(self):
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        # Time period selection logic
        ttk.Label(control_frame, text="Report Period:").pack(side='left', padx=5)

        self.period_var = tk.StringVar(value='This Month')
        period_combo = ttk.Combobox(control_frame, textvariable=self.period_var, width=15)
        period_combo['values'] = ['This Month', 'Last Month', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)

        # Custom time-frame labels and date pickers (disabled unless using custom timeframe)
        ttk.Label(control_frame, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(control_frame, width=12, background='darkblue',
                                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                          maxdate=datetime.now())
        self.start_date_picker.pack(side='left', padx=5)

        ttk.Label(control_frame, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(control_frame, width=12, background='darkblue',
                                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=5)

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        self.generate_button = ttk.Button(control_frame, text="Generate Report", style='Accent.TButton', command=self.generate_report).pack(side='left', padx=5)

        report_frame = ttk.Frame(self.frame)
        report_frame.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(report_frame)
        scrollbar.pack(side='right', fill='y')

        self.report_text = tk.Text(report_frame, wrap='word', yscrollcommand=scrollbar.set,
                                   font=('Roboto', 10))
        scrollbar.config(command=self.report_text.yview)
        self.report_text.pack(fill='both', expand=True)

        # Automatically generate an initial report on launch
        self.generate_report()

    # Enable date pickers when using custom timeframe
    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='normal')
            self.end_date_picker.config(state='normal')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        # Regenerate report whenever the selected period changes
        self.generate_report()

    # Report timeframe picker logic
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

        # Return start and end dates as ISO strings for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    # Generates a simple text-based financial report for the user
    def generate_report(self):
        # Clear previous report text, if any
        self.report_text.delete('1.0', 'end')
        
        start_date, end_date = self.get_date_range()
        
        self.report_text.insert('end', "=" * self.top_btm_separator_mult + "\n")
        # Header
        self.report_text.insert('end', "FINANCIAL REPORT\n")
        self.report_text.insert('end', "=" * self.top_btm_separator_mult + "\n\n")
        
        if start_date and end_date:
            self.report_text.insert('end', f"Period: {start_date} to {end_date}\n\n")
        else:
            self.report_text.insert('end', "Period: All Time\n\n")
        
        # Fetch transactions within the requested date range
        transactions = self.db.get_transactions(start_date, end_date)
        
        # Aggregate simple totals for the report
        total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_expenses = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
        net_income = total_income - total_expenses
        
        self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
        self.report_text.insert('end', "INCOME & EXPENSES SUMMARY\n")
        self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
        self.report_text.insert('end', f"Total Income:        ${total_income:>15,.2f}\n")
        self.report_text.insert('end', f"Total Expenses:      ${total_expenses:>15,.2f}\n")
        self.report_text.insert('end', f"Net Income:          ${net_income:>15,.2f}\n\n")
        
        # Breakdown expenses by category for reporting and charts
        spending_by_category = self.db.get_spending_by_category(start_date, end_date)

        if spending_by_category:
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', "SPENDING BY CATEGORY\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")

            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)

            for category, amount in sorted_categories:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                self.report_text.insert('end', f"{category:<30} ${amount:>12,.2f}  ({percentage:>5.1f}%)\n")

            self.report_text.insert('end', "\n")

        # Compare configured budget targets against actual spending
        budget_targets = self.db.get_budget_targets()
        if budget_targets:
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', "BUDGET VS ACTUAL\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', f"{'Category':<30} {'Budget':>12}  {'Actual':>12}  {'Difference':>12}  {'Status':>8}\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")

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

            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            total_diff = total_budget - total_actual
            self.report_text.insert('end', f"{'TOTAL':<30} ${total_budget:>11,.2f}  ${total_actual:>11,.2f}  ${total_diff:>11,.2f}\n")
            self.report_text.insert('end', "\n")

        # Prepare income section
        income_transactions = [t for t in transactions if t['amount'] > 0]
        if income_transactions:
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', "INCOME BY CATEGORY\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            
            income_by_category = {}
            for trans in income_transactions:
                category = trans['category'] or 'Uncategorized'
                income_by_category[category] = income_by_category.get(category, 0) + trans['amount']
            
            sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_income:
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                self.report_text.insert('end', f"{category:<30} ${amount:>12,.2f}  ({percentage:>5.1f}%)\n")
            
            self.report_text.insert('end', "\n")
        
        # Include net worth (asset/liability) snapshot information
        net_worth_entries = self.db.get_net_worth_entries(start_date, end_date)
        allowed_types = ['Cash', 'Checking', 'Savings', 'Investment', 'Credit Card']

        if net_worth_entries:
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', "ACCOUNT BALANCES\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            
            total_balance = 0
            totals_by_type = {}

            for account in net_worth_entries:
                atype = account.get('asset_type') or 'Other'
                value = account.get('value', 0)
                totals_by_type[atype] = totals_by_type.get(atype, 0) + value

                if atype not in allowed_types:
                    continue

                total_balance += value
                self.report_text.insert('end', f"{account.get('asset_name','Unknown'):<30} ({atype:<15}) ${value:>12,.2f}\n")

            self.report_text.insert('end', f"\n{'Total:':<30} {'':<15} ${total_balance:>12,.2f}\n\n")

            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")
            self.report_text.insert('end', "NET WORTH SUMMARY\n")
            self.report_text.insert('end', "-" * self.inner_separator_mult + "\n")

            total_assets = 0
            total_liabilities = 0
            assets_by_type = {}
            liabilities_by_type = {}

            for asset_type, value in totals_by_type.items():
                if value >= 0:
                    total_assets += value
                    assets_by_type[asset_type] = value
                else:
                    total_liabilities += abs(value)
                    liabilities_by_type[asset_type] = value

            if assets_by_type:
                self.report_text.insert('end', "-- ASSETS --\n\n")
                for asset_type, value in sorted(assets_by_type.items(), key=lambda x: x[1], reverse=True):
                    self.report_text.insert('end', f"{asset_type:<30} ${value:>15,.2f}\n")
                self.report_text.insert('end', f"\n{'-> Total Assets:':<30} ${total_assets:>15,.2f}\n\n")

            if liabilities_by_type:
                self.report_text.insert('end', "-- LIABILITIES --\n\n")
                for liability_type, value in sorted(liabilities_by_type.items(), key=lambda x: abs(x[1]), reverse=True):
                    self.report_text.insert('end', f"{liability_type:<30} ${value:>15,.2f}\n")
                self.report_text.insert('end', f"\n{'-> Total Liabilities:':<30} ${-total_liabilities:>15,.2f}\n\n")

            # Final net worth calculation and display
            total_net_worth = total_assets - total_liabilities
            self.report_text.insert('end', f"{'TOTAL NET WORTH:':<30} ${total_net_worth:>15,.2f}\n\n")
        
        self.report_text.insert('end', "=" * self.top_btm_separator_mult + "\n")
        self.report_text.insert('end', "END OF REPORT\n")
        self.report_text.insert('end', "=" * self.top_btm_separator_mult + "\n")
