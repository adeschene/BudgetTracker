import tkinter as tk
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.figure import Figure
from matplotlib.backends import _backend_tk
import matplotlib.dates as mdates
from tkinter import ttk
from tkinterweb import HtmlFrame
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from decimal import Decimal
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager
from utils.helpers import DP_COLORS, REPORT_CLRS

# Fix for the scroll crash in Tkinter/tkinterweb
def safe_scroll_event(self, event):
    try:
        # Check if widget is just a string name (e.g. ".!frame.!htmlframe")
        if isinstance(event.widget, str):
            # Attempt to convert name back to a Python widget object
            event.widget = self.canvas.get_tk_widget().nametowidget(event.widget)
        
        # Now call the original Matplotlib internal function
        return _backend_tk.FigureCanvasTk.scroll_event_windows(self, event)
    except (AttributeError, KeyError, Exception):
        # If it's not a Matplotlib widget or conversion fails, just ignore the event
        pass

# Apply the patch to the Matplotlib backend class
_backend_tk.FigureCanvasTk.scroll_event_windows = safe_scroll_event

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
                                        background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                        headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                        othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                        weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                        othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                        normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                        disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                        bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now(), day=1)
        self.start_date_picker.pack(side='left', padx=5)
        self.start_date_picker.bind("<<DateEntrySelected>>", lambda e: self.generate_report())

        ttk.Label(centered_container, text="End:").pack(side='left', padx=5)
        self.end_date_picker = DateEntry(centered_container, width=12, firstweekday='sunday',
                                        background=DP_COLORS['main_bg'], foreground=DP_COLORS['main_fg'],
                                        headersbackground=DP_COLORS['header_bg'], headersforeground=DP_COLORS['header_fg'],
                                        othermonthwebackground=DP_COLORS['otherwe_bg'], othermonthweforeground=DP_COLORS['otherwe_fg'],
                                        weekendbackground=DP_COLORS['weekend_bg'], weekendforeground=DP_COLORS['weekend_fg'],
                                        othermonthbackground=DP_COLORS['other_bg'], othermonthforeground=DP_COLORS['other_fg'],
                                        normalbackground=DP_COLORS['nm_bg'], normalforeground=DP_COLORS['nm_fg'],
                                        disableddaybackground=DP_COLORS['disabled_bg'], disableddayforeground=DP_COLORS['disabled_fg'],
                                        bordercolor=DP_COLORS['border'], borderwidth=2, date_pattern='mm-dd-yyyy',
                                        maxdate=datetime.now())
        self.end_date_picker.pack(side='left', padx=(5,0))
        self.end_date_picker.bind("<<DateEntrySelected>>", lambda e: self.generate_report())

        self.start_date_picker.config(state='disabled')
        self.end_date_picker.config(state='disabled')

        self.report_frame = HtmlFrame(self, messages_enabled = False)
        self.report_frame.pack(fill='both', expand=True, padx=20, pady=(15,20))

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
                return None, None, None, None

        # Return start and end dates (both functional and displayable) as ISO strings for DB queries
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), start.strftime('%m-%d-%Y'), end.strftime('%m-%d-%Y')
    
    # Generates a simple text-based financial report for the user
    def generate_report(self):
        # Clear previous report text, if any
        self.report_frame.load_html("")

        start_date, end_date, display_start, display_end = self.get_date_range()
        
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
            body {{ font-family: 'Roboto Mono', Tahoma, Geneva, Verdana, sans-serif; margin: 15px; color: {REPORT_CLRS['normal_text']}; background-color: {REPORT_CLRS['normal_bg']}; }}
            .header {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; color: {REPORT_CLRS['normal_text']}; border-bottom: 2px solid {REPORT_CLRS['normal_text']}; padding-bottom: 10px; }}
            .section-title {{ font-size: 18px; font-weight: bold; margin-top: 40px; margin-bottom: 10px; color: {REPORT_CLRS['normal_text']}; border-bottom: 2px solid {REPORT_CLRS['highlighted']}; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; color: {REPORT_CLRS['normal_text']}; margin: 0px 6px; }}
            th, td {{ padding: 12px 15px; text-align: right; border-bottom: 1px solid {REPORT_CLRS['normal_text']}; }}
            th:first-child, td:first-child {{ text-align: left; }}
            tr:nth-child(even) {{ background-color: #ddd; }}
            .income {{ color: {REPORT_CLRS['income']}; font-weight: bold; }}
            .expense {{ color: {REPORT_CLRS['expense']}; font-weight: bold; }}
            .net {{ color: {REPORT_CLRS['normal_text']}; font-weight: bold; font-size: 16px; }}
            .status-over {{ color: {REPORT_CLRS['expense']}; }}
            .status-under {{ color: {REPORT_CLRS['income']}; }}
            .nw-card {{ 
                background-color: {REPORT_CLRS['emphasis']};
                color: {REPORT_CLRS['normal_text']};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin: 30px 0px 20px 0px;
            }}
            .nw-amount {{ font-size: 32px; font-weight: bold; }}
            .asset-text {{ color: {REPORT_CLRS['income']}; font-weight: bold; }}
            .liability-text {{ color: {REPORT_CLRS['expense']}; font-weight: bold; }}
            .indent {{ padding-left: 20px; color: {REPORT_CLRS['indented']}; font-size: 0.9em; margin: 0px 8px; }}
        </style>
        </head>
        <body>
        <div class="header">FINANCIAL REPORT</div>
        <p><strong>Period:</strong> {display_start + ' to ' + display_end if display_start else 'All Time'}</p>

        <div class="section-title">INCOME & EXPENSES</div>
        <table>
            <tr><td>Total Income:</td><td class="income">${total_income:,.2f}</td></tr>
            <tr><td>Total Expenses:</td><td class="expense">${total_expenses:,.2f}</td></tr>
            <tr style="background: {REPORT_CLRS['emphasis']}"><td><strong>Net Income:</strong></td><td class="net"><strong>${net_income:,.2f}</strong></td></tr>
        </table>
        """
        
        # --- Spending by Category ---
        spending_by_category = self.db.get_category_totals_by_type(start_date, end_date, type='expense')

        if spending_by_category:
            html_output += "<div class='section-title'>SPENDING BY CATEGORY</div>"
            html_output += "<table><tr><th>Category</th><th>Amount</th><th>Percent</th></tr>"
            sorted_categories = sorted(spending_by_category.items(), key=lambda x: x[1], reverse=True)
            total_exp_cents = sum(spending_by_category.values())
            
            for category, amount_cents in sorted_categories:
                amount = Decimal(amount_cents) / 100
                percentage = (Decimal(amount_cents) / total_exp_cents) * 100 if total_exp_cents > 0 else 0
                html_output += f"<tr><td>{category}</td><td>${amount:,.2f}</td><td>{percentage:.1f}%</td></tr>"
            html_output += "</table>"

        # --- Budget vs Actual ---
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
        
        # --- NET WORTH SECTION ---
        net_worth_entries = self.db.get_net_worth_entries(start_date, end_date)

        if not net_worth_entries:
            return
        
        html_output += '<div class="section-title">NET WORTH</div>'

        if not start_date and not end_date: # 'All Time' handler
            all_dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in net_worth_entries]
            
            start_date = datetime.strftime(min(all_dates), '%Y-%m-%d')
            end_date = datetime.strftime(max(all_dates), '%Y-%m-%d')
        
        # Calculate difference in months for conditional logic
        diff = relativedelta(datetime.strptime(end_date, '%Y-%m-%d'), datetime.strptime(start_date, '%Y-%m-%d'))
        total_months = diff.years * 12 + diff.months

        chart_base64_url = None

        # Group entries into months
        monthly_data = self.group_by_month(net_worth_entries)
        sorted_months = sorted(monthly_data.keys())

        if total_months >= 6: # Create trend chart if looking at span of at least 6 months
            chart_base64_url = self.generate_net_worth_chart(monthly_data, sorted_months)
            
        # Grab the First and Latest month snapshots
        first_month_key = sorted_months[0]
        latest_month_key = sorted_months[-1]

        # Calculate totals for the First Month (Opening)
        opening_nw = sum(e['value'] for e in monthly_data[first_month_key])
        
        # Calculate totals for the Latest Month (Closing)
        latest_entries = monthly_data[latest_month_key]
        grouped_accounts = defaultdict(list)
        total_assets = 0
        total_liabilities = 0

        for account in latest_entries:
            atype = account.get('asset_type') or 'Other'
            value = account.get('value', 0)
            account_name = account.get('asset_name', 'Unknown Account')
            
            grouped_accounts[atype].append({'name': account_name, 'value': value})

            if value >= 0:
                total_assets += value
            else:
                total_liabilities += abs(value)
            
        total_net_worth = total_assets - total_liabilities

        # This represents the growth from the start of the period to the end.
        change_val = total_net_worth - opening_nw

        html_output += self.generate_net_worth_html(
            grouped_accounts, total_assets, total_liabilities, total_net_worth, change_val, chart_base64_url
        )
        
        # Close HTML body and tags
        html_output += "</body></html>"
        
        # Load the entire string into the HtmlFrame widget
        self.report_frame.load_html(html_output)

    def group_by_month(self, entries):
        months = defaultdict(list)
        for entry in entries:
            # Assuming entry['date'] is a string 'YYYY-MM-DD' or datetime object
            date_obj = datetime.strptime(entry['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m') # Format: '2026-01'
            months[month_key].append(entry)
        return months
    
    def generate_net_worth_chart(self, monthly_data, sorted_months):
        dates = [datetime.strptime(m, '%Y-%m') for m in sorted_months]
        values = []
        for month_key in sorted_months:
            # Calculate total NW for each month snapshot
            nw_sum = sum(e['value'] for e in monthly_data[month_key])
            values.append(nw_sum)
        
        fig = Figure(figsize=(8, 4), dpi=300, tight_layout=True, facecolor=REPORT_CLRS['normal_bg'])
        ax = fig.add_subplot(111, facecolor=REPORT_CLRS['chart_bg'])
        ax.plot(dates, values, color=REPORT_CLRS['line'], linestyle='-', marker='o', linewidth=2)
        # Set the locator to tell Matplotlib where to put ticks (every month start)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        # Set the formatter to define how those ticks should look (Month/Year)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.grid(True, linestyle='--', alpha=0.6) # Add a subtle grid for readability
        fig.autofmt_xdate(ha='right',rotation=45) # Auto format dates on X-axis

        # Coloring
        ax.spines['top'].set_color(REPORT_CLRS['normal_text'])
        ax.spines['left'].set_color(REPORT_CLRS['normal_text'])
        ax.tick_params(axis='x', colors=REPORT_CLRS['normal_text'], labelsize=8)
        ax.tick_params(axis='y', colors=REPORT_CLRS['normal_text'], labelsize=8)

        # Save the figure to a base64 string to embed directly in HTML
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig) # Prevents memory leaks and the scroll bug
        buf.seek(0)
        
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    def generate_net_worth_html(self, grouped_accounts, total_assets, total_liabilities, total_net_worth, change_val=None, chart_url=None):
        # Add a growth indicator if we have comparative data
        growth_html = ""
        if change_val is not None:
            color = REPORT_CLRS['income'] if change_val >= 0 else REPORT_CLRS['expense']
            prefix = "+" if change_val >= 0 else ""
            growth_html = f"<div style='color:{color}; font-size:14px;'>{prefix}${change_val:,.0f} this period</div>"
        
        html = ""

        # Inject the chart here if the URL is provided
        if chart_url:
            html += f"<div style='font-size: 20px; font-weight: bold; color: {REPORT_CLRS['normal_text']}; text-align: center; padding-top: 10px'>Net Worth Trend</div>"
            html += f"<img src='{chart_url}' style='width: 100%; height: auto; margin-bottom: 20px;' />"

        html += f"""
        <div class="nw-card">
            <div style="font-size: 20px; color: {REPORT_CLRS['normal_text']}; margin-bottom: 5px;">CLOSING NET WORTH</div>
            <div class="nw-amount">${total_net_worth:,.0f}</div>
            {growth_html}
        </div>
        """

        # --- Assets Section ---
        html += "<div class='section-title'>Assets (Closing)</div><table>"
        # Sort types A-Z
        for atype in sorted(grouped_accounts.keys()):
            # Only process asset types (positive total)
            if sum(a['value'] for a in grouped_accounts[atype]) >= 0:
                html += f"<tr class='asset-text'><td>{atype}</td><td class='asset-text'>${sum(a['value'] for a in grouped_accounts[atype]):,.0f}</td></tr>"
                
                # Display individual accounts underneath
                for account in grouped_accounts[atype]:
                    html += f"<tr class='indent'><td>▶ {account['name']}</td><td>${account['value']:,.0f}</td></tr>"

        html += f"<tr style='background-color: {REPORT_CLRS['emphasis']}; color: {REPORT_CLRS['normal_text']}'><td><strong>Total Assets:</strong></td><td class='asset-text'>${total_assets:,.0f}</td></tr></table>"

        # --- Liabilities Section ---
        if total_liabilities > 0:
            html += "<div class='section-title'>Liabilities (Closing)</div><table>"
            # Sort types A-Z
            for atype in sorted(grouped_accounts.keys()):
                # Only process liability types (negative total)
                if sum(a['value'] for a in grouped_accounts[atype]) < 0:
                    html += f"<tr class='liability-text'><td>{atype}</td><td class='liability-text'>-${abs(sum(a['value'] for a in grouped_accounts[atype])):,.0f}</td></tr>"

                    # Display individual liabilities underneath
                    for account in grouped_accounts[atype]:
                        html += f"<tr class='indent'><td>▶ {account['name']}</td><td>-${abs(account['value']):,.0f}</td></tr>"

            html += f"<tr style='background-color: {REPORT_CLRS['emphasis']}; color: {REPORT_CLRS['normal_text']}'><td><strong>Total Liabilities:</strong></td><td class='liability-text'>-${total_liabilities:,.0f}</td></tr></table>"
        
        return html
