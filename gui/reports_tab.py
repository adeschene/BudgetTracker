import tkinter as tk
from tkinter import ttk
from tkinterweb import HtmlFrame
from datetime import datetime, timedelta
from decimal import Decimal
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager

class ReportsTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db

        self.setup_ui()

    def setup_ui(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=10, pady=10)

        centered_container = ttk.Frame(control_frame)
        centered_container.pack(expand=True, pady=(2,0))

        # Time period selection logic
        ttk.Label(centered_container, text="Report Period:").pack(side='left', padx=(0,5))

        self.period_var = tk.StringVar(value='This Month')
        period_combo = ttk.Combobox(centered_container, textvariable=self.period_var, width=15, state='readonly')
        period_combo['values'] = ['This Month', 'Last Month', 'Last Two Months', 'Last Three Months', 'This Year', 'Last Year', 'All Time', 'Custom']
        period_combo.pack(side='left', padx=5)
        period_combo.bind('<<ComboboxSelected>>', self.on_period_change)

        # Custom time-frame labels and date pickers (disabled unless using custom timeframe)
        ttk.Label(centered_container, text="Start:").pack(side='left', padx=5)
        self.start_date_picker = DateEntry(centered_container, width=12, firstweekday='sunday',
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
        self.start_date_picker.bind("<<DateEntrySelected>>", lambda e: self.generate_report())

        ttk.Label(centered_container, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(centered_container, width=12, firstweekday='sunday',
                                        background='#232323', foreground='whitesmoke',
                                        headersbackground='#454545', headersforeground='whitesmoke',
                                        othermonthwebackground='#565656', othermonthweforeground='whitesmoke',
                                        weekendbackground='#666666', weekendforeground='whitesmoke',
                                        othermonthbackground='#777777', othermonthforeground='#232323',
                                        normalbackground='#888888', normalforeground='black',
                                        disableddaybackground='#454545', disableddayforeground='#888888',
                                        bordercolor='#343434', borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=(5,0))
        self.end_date_picker.bind("<<DateEntrySelected>>", lambda e: self.generate_report())

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        self.report_frame = HtmlFrame(self, messages_enabled = False)
        self.report_frame.pack(fill='both', expand=True, padx=10, pady=(5,10))

    def on_tab_opened(self): # Trigger refresh when switching to tab from another
        self.generate_report()

    # Enable date pickers when using custom timeframe
    def on_period_change(self, event=None):
        if self.period_var.get() == 'Custom':
            self.start_date_picker.config(state='readonly')
            self.end_date_picker.config(state='readonly')
        else:
            self.start_date_picker.config(state='disabled')
            self.end_date_picker.config(state='disabled')
        # Regenerate report whenever the selected period changes
        self.generate_report()

    # Report timeframe picker logic
    def get_date_range(self):
        period = self.period_var.get()
        today = datetime.now()

        match period:
            case 'This Month':
                start = today.replace(day=1)
                end = today
            case 'Last Month':
                first_this_month = today.replace(day=1)
                end = first_this_month - timedelta(days=1)
                start = end.replace(day=1)
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
                start_year = this_year - 1 if start_month == 12 or 11 else this_year
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

        # Return start and end dates as ISO strings for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    # Generates a simple text-based financial report for the user
    def generate_report(self):
        # Clear previous report text, if any
        self.report_frame.load_html("")

        start_date, end_date = self.get_date_range()
        
        # Fetch transactions within the requested date range
        transactions = self.db.get_transactions(start_date, end_date)
        
        # Aggregate simple totals for the report
        total_income = sum(Decimal(t['amount'])/100 for t in transactions if t['amount'] > 0)
        total_expenses = sum(abs(Decimal(t['amount'])/100) for t in transactions if t['amount'] < 0)
        net_income = total_income - total_expenses

        html_output = f"""
        <html>
        <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 15px; color: #333; }}
            .header {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            .section-title {{ font-size: 18px; font-weight: bold; margin-top: 25px; margin-bottom: 10px; color: #34495e; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 12px 15px; text-align: right; border-bottom: 1px solid #ddd; }}
            th:first-child, td:first-child {{ text-align: left; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .income {{ color: #2ecc71; font-weight: bold; }}
            .expense {{ color: #e74c3c; font-weight: bold; }}
            .net {{ color: #2980b9; font-weight: bold; font-size: 16px; }}
            .status-over {{ color: #e74c3c; }}
            .status-under {{ color: #2ecc71; }}
        </style>
        </head>
        <body>
        <div class="header">FINANCIAL REPORT</div>
        <p><strong>Period:</strong> {start_date} to {end_date if start_date else 'All Time'}</p>

        <div class="section-title">INCOME & EXPENSES SUMMARY</div>
        <table>
            <tr><td>Total Income:</td><td class="income">${total_income:,.2f}</td></tr>
            <tr><td>Total Expenses:</td><td class="expense">${total_expenses:,.2f}</td></tr>
            <tr style="border-top: 2px solid #333;"><td><strong>Net Income:</strong></td><td class="net"><strong>${net_income:,.2f}</strong></td></tr>
        </table>
        """
        
        # --- Spending by Category (Example of extending HTML) ---
        spending_by_category = self.db.get_category_totals_by_type(start_date, end_date, type='expense')

        if spending_by_category:
            html_output += "<div class='section-title'>SPENDING BY CATEGORY</div>"
            html_output += "<table><tr><th>Category</th><th>Amount</th><th>Percent</th></tr>"
            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)
            total_exp_cents = sum(spending_by_category.values())
            
            for category, amount_cents in sorted_categories:
                amount = Decimal(amount_cents) / 100
                percentage = (Decimal(amount_cents) / total_exp_cents) if total_exp_cents > 0 else 0
                html_output += f"<tr><td>{category}</td><td>${amount:,.2f}</td><td>{percentage:.1f}%</td></tr>"
            html_output += "</table>"

        # --- Budget vs Actual (Example with color coding) ---
        budget_targets = self.db.get_budget_targets()
        if budget_targets:
            html_output += "<div class='section-title'>BUDGET VS ACTUAL</div>"
            html_output += "<table>"
            html_output += "<tr><th>Category</th><th>Budget</th><th>Actual</th><th>Difference</th><th>Status</th></tr>"
            for budget in budget_targets:
                category = budget['category']
                budget_amount = budget['monthly_target']
                actual_amount = Decimal(spending_by_category.get(category, 0))/100
                difference = budget_amount - actual_amount
                
                status_class = "status-under" if difference >= 0 else "status-over"
                status_text = "✓ Under" if difference >= 0 else "✗ Over"
                
                html_output += f"""
                <tr>
                    <td>{category}</td>
                    <td>${budget_amount:,.2f}</td>
                    <td>${actual_amount:,.2f}</td>
                    <td>${difference:,.2f}</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
                """
            html_output += "</table>"
        
        # Breakdown income by category for reporting and charts
        income_by_category = self.db.get_category_totals_by_type(start_date, end_date, type='income')

        if income_by_category:
            
            sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            
            for category, amount in sorted_income:
                percentage = (Decimal(amount) / total_income) if total_income > 0 else 0
        
        # Include net worth (asset/liability) snapshot information
        net_worth_entries = self.db.get_net_worth_entries(start_date, end_date)
        allowed_types = ['Cash', 'Checking', 'Savings', 'Investment', 'Credit Card']

        if net_worth_entries:
            
            total_balance = 0
            totals_by_type = {}

            for account in net_worth_entries:
                atype = account.get('asset_type') or 'Other'
                value = account.get('value', 0)
                totals_by_type[atype] = totals_by_type.get(atype, 0) + value

                if atype not in allowed_types:
                    continue

                total_balance += value

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

            # Final net worth calculation and display
            total_net_worth = total_assets - total_liabilities

        # Close HTML body and tags
        html_output += "</body></html>"
        
        # Load the entire string into the HtmlFrame widget
        self.report_frame.load_html(html_output)
