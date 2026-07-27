# Personal Budget Tracker

A Windows desktop application for tracking and visualizing personal finances. Built with Python and Tkinter, designed for maximum ease of use after initial setup/customization.

## Features

### Transaction Management
- **CSV Import**: Import transactions from bank statements (CSV files) with automatic column detection
- **Custom Import Templates**: Set up custom import options for different bank/card statement formats for perfect imports every time
- **Auto-Categorization**: Automatically categorize transactions based on keywords
- **Manual Transaction Entry**: Add transactions manually through the UI
- **Transaction Editing**: Edit or delete existing transactions
- **Batch Operations**: Support for batch deletion of multiple transactions
- **Advanced Filtering**: Filter transactions by date range, category, keyword (exact or fuzzy matching), and account
- **Sorting**: Sort by date, description, amount, account, or category

### Categories & Accounts
- **Custom Categorization**: Add, edit, or delete categories for your needs
- **Category Keywords**: Set regex rules for automatic categorization
- **Account Management**: Track transactions across multiple accounts (checking, savings, credit, investment, etc.)
- **Asset & Liability Types**: Track 10+ different asset and liability types

### Financial Planning & Analysis
- **Budget Tools**: Set monthly budget limits for any expense categories and track spending against limits
- **Net Worth Tracking**: Track assets and liabilities month by month with historical trending
- **Net Worth Templates**: Save account templates to streamline monthly net worth updates
- **Financial Reports**: Generate comprehensive reports with:
  - Income/expense summaries by time period
  - Spending breakdown by category
  - Budget adherence and performance metrics
  - Net worth summaries and trends
- **Visualizations**: Robust charts and graphs to visualize financial trends and spending habits

### Data Management
- **SQLite Database**: All data stored locally in a secure database file (`budget_tracker.db`)
- **CSV Export**: Export transactions and reports to CSV format
- **Dark Theme**: Built-in dark theme for comfortable viewing

## Installation

1. Make sure you have Python 3.7+ installed
2. Clone or download this repository
3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python main.py
   ```

## Usage

### Starting the Application

Run:
```
python main.py
```

Paths are resolved relative to the project root, so the app can be launched from any working directory.

The application will open with a tabbed interface containing:
- **Transactions**: Import, manage, and filter transactions
- **Net Worth**: Track assets and liabilities
- **Budget**: Set and monitor budget goals
- **Visualizations**: View charts and graphs of financial data
- **Reports**: Generate comprehensive financial reports

### Importing CSV Files

1. Navigate to the **Transactions** tab
2. Click the **Import CSV** button
3. Select your bank/card statement CSV file
4. (Optional) Select an Import Template for your financial institution:
   - Click **Manage Templates** to create/customize templates for your banks
   - Templates auto-detect CSV columns and parse formats consistently
5. Choose or create an account name for imported transactions
6. Enable **Auto-Categorization** to automatically assign categories based on transaction descriptions (optional)
7. Review and confirm the import

The app automatically detects common CSV column names, but custom templates ensure perfect imports every time.

### Managing Transactions

- View all transactions in the **Transactions** tab
- **Filter** by:
  - Date range (This Month, Last Month, Last Year, Custom period, etc.)
  - Account
  - Category
  - Keyword (supports exact or fuzzy matching)
- **Sort** by clicking column headers: Date, Description, Amount, Account, or Category
- **Add** manual transactions using the "Add Transaction" button
- **Edit** transactions by double-clicking cells in the table
- **Delete** individual transactions or use Shift+Click to select and batch delete
- **Categorize** using auto-categorization or manual assignment

### Managing Accounts and Categories

- **Accounts**: Automatically created when importing transactions; manage in Settings
- **Categories**:
  - Click **Settings** → **Manage Categories**
  - Add custom categories by type (Income/Expense)
  - Set keywords for automatic transaction categorization
  - Keywords support regex patterns for powerful matching
### Setting Up Budgets

- Go to the **Budget** tab
- Click **Add Budget** to create a new budget entry
- Enter a category name, monthly target amount, and optional notes
- Track actual spending against budget targets in the same tab
- Budgets support all expense categories

### Tracking Net Worth

- Go to the **Net Worth** tab
- Use **◀** and **▶** buttons to navigate between months
- Click **⭮** to return to the current month
- **Assets** section: Add entries for cash, investments, real estate, vehicles, etc.
- **Liabilities** section: Add entries for loans, credit cards, etc. as negative values
- View your total net worth and breakdown by month
- Save **Net Worth Templates** to quickly update the same accounts each month:
  - Set up all your accounts once
  - Template feature lets you apply the same structure to new months
  - Only enter the updated values each month

### Generating Reports

- Go to the **Reports** tab
- Select a time period (This Month, Last Month, This Year, All Time, Custom)
- Reports display:
  - **Summary**: Total income and expenses for the period
  - **By Category**: Breakdown of spending by expense category
  - **Budget Performance**: Comparison of actual spending vs. budget limits
  - **Net Worth Summary**: Assets, liabilities, and net worth trends
  - **Monthly Trends**: Historical visualization of income and expenses

### Viewing Visualizations

- Go to the **Visualizations** tab
- Select a time period (This Month, Last Month, This Year, All Time, Custom)
- Available charts:
  - **Spending by Category**: Pie chart showing expense distribution
  - **Income vs. Expenses**: Bar chart comparing income and expenses by month
  - **Category Trends**: Line chart showing spending trends over time
  - **Account Breakdown**: Distribution of assets/liabilities across accounts

### Settings and Preferences

- Click the **Settings** button to access:
  - **Manage Categories**: Add/edit/delete transaction categories and keywords
  - **Manage Accounts**: View and manage all accounts
  - **Import Templates**: Create/edit custom CSV import templates for your banks
  - Theme and display settings

## Data Storage

All data is stored locally in a SQLite database file (`budget_tracker.db`) in the application directory. Your financial data never leaves your computer.

## CSV Import Format

The app can handle various CSV formats with intelligent column detection. It searches for columns containing:

### Column Names
- **Date**: "date", "transaction date", "posted date"
- **Description**: "description", "memo", "details", "payee"
- **Amount**: "amount", "debit", "credit", "transaction amount"

### Supported Date Formats
- YYYY-MM-DD
- MM/DD/YYYY
- MM/DD/YY
- And many other common date formats

### Custom Import Templates

For best results, create custom import templates for each financial institution:
1. Note the exact column names and positions in your bank's CSV format
2. Set appropriate field mappings and parsing rules
3. Save as a template for that institution
4. Reuse the template for future imports from the same source

## Default Categories

The app comes with default categories organized by type:

### Income Categories
- Salary
- Investment
- Other Income

### Expense Categories
- Groceries
- Dining
- Transportation
- Utilities
- Entertainment
- Shopping
- Healthcare
- Housing
- Other Expense

You can add custom categories via **Settings** → **Manage Categories** to suit your needs.

## Project Structure

```
BudgetTracker/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── budget_tracker.db       # SQLite database (created on first run)
├── database/
│   ├── db_manager.py      # Database operations and schema
│   └── __init__.py
├── gui/
│   ├── main_window.py     # Main application window and tabs
│   ├── transactions_tab.py # Transaction management interface
│   ├── net_worth_tab.py   # Net worth tracking interface
│   ├── budget_tab.py      # Budget setting and tracking
│   ├── visualizations_tab.py # Charts and graphs
│   ├── reports_tab.py     # Financial reports
│   └── __init__.py
├── utils/
│   ├── csv_importer.py    # CSV parsing and import logic
│   ├── csv_exporter.py    # Export data to CSV
│   ├── category_manager.py # Category management dialog
│   ├── account_manager.py # Account management dialog
│   ├── import_template_manager.py # Custom CSV templates
│   ├── settings_menu.py   # Settings and preferences
│   ├── help_menu.py       # Help and documentation
│   ├── editable_tree.py   # Custom editable Treeview widget
│   ├── helpers.py         # Utility functions and helpers
│   ├── paths.py           # Project-root path resolution
│   └── __init__.py
└── assets/
    └── forest-dark.tcl    # Dark theme configuration
```

## Dependencies

- **pandas**: Data manipulation and analysis
- **matplotlib**: Chart and visualization generation
- **tkcalendar**: Date picker widget
- **pillow**: Image handling for themes
- **tkinterweb**: HTML rendering for reports

See `requirements.txt` for the complete list.

## Key Features Explained

### Auto-Categorization with Keywords

The application supports powerful keyword-based auto-categorization:
- Define keywords (including regex patterns) for each category
- When importing or adding transactions, descriptions matching these keywords are automatically categorized
- Build up your keywords over time to improve accuracy
- Override categories manually if needed

### Editable Table Trees

Throughout the application, you'll see interactive tables where you can:
- **Edit cells**: Double-click to edit values inline
- **Add rows**: Use the "Add" button to create new entries
- **Delete rows**: Select rows and press Delete key or use the Delete button
- **Sort**: Click column headers to sort ascending/descending
- **Commit changes**: Changes are automatically saved to the database

### Date Filtering

Most tabs include flexible date filtering:
- **Preset periods**: This Month, Last Month, Last Year, etc.
- **Custom ranges**: Select specific start and end dates
- Date pickers show calendar widgets for easy selection
- Date changes immediately update the displayed data

### Theme and Styling

The application uses the "Forest Dark" theme for a modern, comfortable dark interface:
- Theme is defined in `assets/forest-dark.tcl`
- Main entry point customizes various UI elements (fonts, colors, button sizes)
- Designed for long-term use without eye strain

## Troubleshooting

### CSV Import Issues
- Ensure your CSV file uses standard formatting (headers in first row)
- Check that date formats are recognized (YYYY-MM-DD or MM/DD/YYYY work best)
- Use Import Templates to handle non-standard CSV formats
- Review the import preview before confirming

### Missing Transactions
- Verify the transaction date falls within your selected date range
- Check if the account filter is set to the correct account
- Try clearing all filters to see if the transaction appears

### Database Issues
- The database file (`budget_tracker.db`) is automatically created on first run
- If corrupted, close the app, back up the file, and delete it to recreate
- The backup file `budget_tracker.db.bak` can be used to restore data

## Future Enhancement Ideas

- Multi-user support
- Cloud backup integration
- Mobile app companion
- Advanced forecasting
- Receipt image attachment
- Multi-currency support
- Bank connection API integration
