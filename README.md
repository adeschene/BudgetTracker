# Personal Budget Tracker

A Windows desktop application for tracking personal finances, managing transactions, and monitoring net worth.

## Features

- **CSV Import**: Import transactions from bank statements (CSV files) with automatic column detection
- **Auto-Categorization**: Automatically categorize transactions based on keywords
- **Transaction Management**: Add, edit, delete, and filter transactions
- **Net Worth Tracking**: Manually enter and track assets and liabilities
- **Financial Reports**: Generate comprehensive reports with income/expense summaries
- **Account Management**: Track multiple accounts (checking, savings, credit, investment)
- **Category Management**: Customize income and expense categories

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies (optional):
   ```
   pip install -r requirements.txt
   ```
   Note: The app uses tkinter which comes with Python, so no additional packages are strictly required.

## Usage

Run the application:
```
python main.py
```

### Importing CSV Files

1. Go to **File > Import CSV**
2. Select your bank statement CSV file
3. Optionally specify column names (the app will try to auto-detect them)
4. Choose an account name
5. Enable auto-categorization to automatically assign categories based on transaction descriptions

### Managing Transactions

- View all transactions in the **Transactions** tab
- Filter by date range, category, or account
- Add manual transactions using the "Add Transaction" button
- Edit or delete existing transactions

### Tracking Net Worth

- Go to the **Net Worth** tab
- Add entries for your assets (cash, investments, real estate, etc.)
- Add entries for liabilities (loans, credit cards, etc.) as negative values
- View your total net worth and breakdown by asset type

### Generating Reports

- Go to the **Reports** tab
- Select a time period (This Month, Last Month, This Year, etc.)
- View income/expense summaries, spending by category, and net worth

## Data Storage

All data is stored in a local SQLite database file (`budget_tracker.db`) in the application directory.

## CSV Format

The app can handle various CSV formats. It looks for columns containing:
- **Date**: "date", "transaction date", "posted date"
- **Description**: "description", "memo", "details", "payee"
- **Amount**: "amount", "debit", "credit", "transaction amount"

Supported date formats: YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY, and more.

## Default Categories

The app comes with default categories:
- **Income**: Salary, Investment, Other Income
- **Expenses**: Groceries, Dining, Transportation, Utilities, Entertainment, Shopping, Healthcare, Housing, Other Expense

You can add custom categories via **Data > Manage Categories**.
