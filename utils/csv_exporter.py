import csv
from decimal import Decimal
from database.db_manager import DatabaseManager

class CSVExporter:
    def __init__(self, db: DatabaseManager):
        self.db = db

    # Fetches transactions and writes them to a CSV file
    def export_transactions(self, file_path: str, start_date: str = None,
                            end_date: str = None, category_id: int = None,
                            keyword: str = None, exact: bool = True,
                            threshold: float = None):
        # Grab all transactions from the DB, no filtering functionality (class vars added for possible future update)
        transactions = self.db.get_transactions()

        headers = ['Date', 'Description', 'Amount', 'Category', 'Account', 'Notes'] # Define headers

        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers) # Write headers to file
            # Write transaction rows to file
            for t in transactions:
                # Format amount: convert cents (int) to decimal string
                amount = Decimal(t['amount']) / 100
                
                writer.writerow([
                    t['date'],
                    t['description'],
                    f"{amount:.2f}",
                    t['category_name'],
                    t['account_name'],
                    t['notes']
                ])