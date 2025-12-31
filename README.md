# Personal Budget Tracker

A Windows desktop application for tracking and visualizing personal finances. Designed for maximum ease of use after initial setup/customization.

## Features

- **CSV Import**: Import transactions from bank statements (CSV files) with automatic column detection
- **Custom Import Rules**: Set up custom import options for bank/card statements that always import correctly
- **Auto-Categorization**: Automatically categorize transactions based on keywords
- **Custom Categorization**: Add or modify categories for your needs
- **Account Management**: Track all of your transactions by account (checking, savings, credit, investment)
- **Transaction Management**: Add, edit, delete, and filter transactions
- **Custom Transaction Rules**: Set up regex rules to always import transactions details perfectly every time
- **Budget Tools**: Set up budget limits for any categories you want to limit
- **Net Worth Tracking**: Track assets and liabilities month by month
- **Custom Account Templates**: Add all your accounts to a template and you'll only have to enter the new values every month
- **Financial Reports**: Generate comprehensive reports with income/expense summaries, net worth summaries, and budget adherence info
- **Visualizations for Clarity**: Robust visualizations to help you understand your financial trends and habits over time

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
   Uses matplotlib for visualization charts

## Usage

From inside the repo folder, run:
```
python main.py
```

### Importing CSV Files

1. (Optional) Use the **Manage Templates** button to add/customize an import template for each of your bank/card statements
2. Use the **Import CSV** button in the **Transactions** tab
3. Select your bank/card statement CSV file
4. (Optional) Select an Import Template (the app will try to auto-detect CSV columns if no template is selected)
5. Choose an account name
6. Enable auto-categorization to automatically assign categories based on transaction descriptions (accuracy will be low)

### Managing Transactions

- View all transactions in the **Transactions** tab
- Filter by date range, category, or keyword (exact or fuzzy matching)
- Sort transactions by date, description, amount, account, or category by clicking on the corresponding header
- Add manual transactions using the "Add Transaction" button
- Edit or delete existing transactions (supports batch deletion)

### Tracking Net Worth

- Go to the **Net Worth** tab
- Add entries for your assets (cash, investments, real estate, etc.)
- Add entries for liabilities (loans, credit cards, etc.) as negative values
- View your total net worth and breakdown by month

### Generating Reports

- Go to the **Reports** tab
- Select a time period (This Month, Last Month, This Year, etc.)
- View income/expense summaries, spending by category, budget performance, and net worth summary

## Data Storage

All data is stored in a local SQLite database file (`budget_tracker.db`) in the application directory.

## CSV Format

The app can handle various CSV formats. It looks for columns containing:
- **Date**: "date", "transaction date", "posted date"
- **Description**: "description", "memo", "details", "payee"
- **Amount**: "amount", "debit", "credit", "transaction amount"
For the best experience, create/use custom import templates for each statement format

Supported date formats: YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY, and more.

## Default Categories

The app comes with default categories:
- **Income**: Salary, Investment, Other Income
- **Expenses**: Groceries, Dining, Transportation, Utilities, Entertainment, Shopping, Healthcare, Housing, Other Expense

You can add custom categories via the **Settings Menu**.
