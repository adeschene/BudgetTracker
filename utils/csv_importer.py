import csv
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from database.db_manager import DatabaseManager
from utils.helpers import center_window

class CSVImporter:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def parse_csv(self, file_path: str, date_col: str = None, desc_col: str = None,
                  amount_col: str = None, debit_col: str = None, credit_col: str = None,
                  desc2_col: str = None, delimiter: str = '',
                  has_header: bool = True, skip_rows: int = 0) -> List[Dict]:
        transactions = []

        with open(file_path, 'r', encoding='utf-8-sig') as file:
            for _ in range(skip_rows):
                next(file, None)

            if has_header:
                # Use DictReader when file contains headers; try to auto-detect
                # common column names when caller did not supply them.
                reader = csv.DictReader(file)
                headers = reader.fieldnames

                if not date_col:
                    date_col = self._detect_column(headers, ['date', 'transaction date', 'posted date'])
                if not desc_col:
                    desc_col = self._detect_column(headers, ['description', 'memo', 'details', 'payee'])
                if not amount_col and not (debit_col and credit_col):
                    amount_col = self._detect_column(headers, ['amount', 'debit', 'credit', 'transaction amount'])

                for row in reader:
                    try:
                        transaction = self._parse_row(row, date_col, desc_col, amount_col, debit_col, credit_col, desc2_col, delimiter)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        # Non-fatal: skip rows that fail to parse and continue
                        print(f"Error parsing row: {e}")
                        continue
            else:
                reader = csv.reader(file)
                for row in reader:
                    try:
                        if len(row) >= 3:
                            transaction = {
                                'date': self._parse_date(row[0]),
                                'description': row[1],
                                'amount': self._parse_amount(row[2])
                            }
                            transactions.append(transaction)
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                        continue

        return transactions

    def _detect_column(self, headers: List[str], possible_names: List[str]) -> str:
        headers_lower = [h.lower() for h in headers]
        for name in possible_names:
            for i, header in enumerate(headers_lower):
                if name in header:
                    return headers[i]
        return headers[0] if headers else None

    def _parse_row(self, row: Dict, date_col: str, desc_col: str, amount_col: str = None,
                   debit_col: str = None, credit_col: str = None,
                   desc2_col: str = None, delimiter: str = ' - ') -> Dict:
        date_str = row.get(date_col, '')
        description = row.get(desc_col, '')

        if desc2_col:
            description2 = row.get(desc2_col, '')
            if description2:
                description = f"{description}{delimiter}{description2}"

        if not date_str:
            return None

        amount = 0.0
        if debit_col and credit_col:
            debit_str = row.get(debit_col, '')
            credit_str = row.get(credit_col, '')

            debit_amount = self._parse_amount(debit_str) if debit_str else Decimal(0.0)
            credit_amount = self._parse_amount(credit_str) if credit_str else Decimal(0.0)

            debit_amount = abs(debit_amount)
            credit_amount = abs(credit_amount)

            amount = credit_amount - debit_amount
        elif amount_col:
            amount_str = row.get(amount_col, '')
            if not amount_str:
                return None
            amount = self._parse_amount(amount_str)
        else:
            return None

        # Normalize and return a simplified transaction dict used by importer
        return {
            'date': self._parse_date(date_str),
            'description': description,
            'amount': amount
        }

    def _parse_date(self, date_str: str) -> str:
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%b %d, %Y',
            '%B %d, %Y'
        ]

        # Attempt several common date formats, returning ISO date on success
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If parsing fails, return the original string (TODO caller should handle error)
        return date_str

    def _parse_amount(self, amount_str: str) -> Decimal:
        amount_str = amount_str.strip()
        amount_str = re.sub(r'[^\d\.\-\+]', '', amount_str)

        try:
            return Decimal(amount_str)
        except ValueError:
            return 0.0

    def import_transactions(self, file_path: str, template: Dict, has_header: bool = True,
                          auto_categorize: bool = True) -> int:
        date_col = template['date_column']
        desc_col = template['description_column']
        desc2_col = template.get('description2_column')
        delimiter = template.get('description_delimiter', ' - ')
        amount_col = template.get('amount_column')
        debit_col = template.get('debit_column')
        credit_col = template.get('credit_column')
        account_name = template['account_name']
        skip_rows = template.get('skip_rows', 0)

        # Only fetch rules if template has an ID (auto-detect templates have id=None)
        rules = self.db.get_description_rules(template['id']) if template['id'] else []

        # Parse CSV into normalized transaction dicts using template mapping
        transactions = self.parse_csv(file_path, date_col, desc_col, amount_col, debit_col, credit_col, desc2_col, delimiter, has_header, skip_rows)

        count = 0
        # Apply description rules and categorization, then persist each transaction
        for trans in transactions:
            description = trans['description']
            category = None

            # Rules can rewrite the description, assign a category, or indicate ignore
            description, rule_category = self._apply_description_rules(description, rules)

            # If a rule marked the transaction to be ignored, skip it
            if description is None:
                continue

            trans['description'] = description

            # Rule category takes precedence; otherwise try automatic matching
            if rule_category:
                category = rule_category
            elif auto_categorize:
                category = self._auto_categorize(description, trans['amount'])

            transaction_type = 'income' if trans['amount'] > 0 else 'expense'

            self.db.add_transaction(
                date=trans['date'],
                description=description,
                amount=int(Decimal(trans['amount'])*100),
                category_id=self.db.get_category_id_by_name(category),
                account_id=self.db.get_account_id_by_name(account_name),
                transaction_type=transaction_type
            )
            count += 1

        return count

    def _apply_description_rules(self, description: str, rules: List[Dict]) -> Tuple[str, Optional[str]]:
        category = None

        for rule in rules:
            try:
                pattern = rule['pattern']

                if re.search(pattern, description):
                    if rule.get('ignore', 0):
                        return None, None

                    replacement = rule['replacement']
                    description = replacement

                    if rule['category_id']:
                        category = self.db.get_category_name_by_id(rule['category_id'])

                    break
            except re.error as e:
                print(f"Invalid regex pattern '{pattern}': {e}")
                continue

        return description, category

    def _auto_categorize(self, description: str, amount: float) -> str:
        categories = self.db.get_categories()
        description_lower = description.lower()

        best_match = None
        max_matches = 0

        for category in categories:
            keywords = category.get('keywords', '')
            if not keywords:
                continue

            keyword_list = [k.strip() for k in keywords.split(',')]
            matches = sum(1 for keyword in keyword_list if keyword and keyword in description_lower)

            if matches > max_matches:
                max_matches = matches
                best_match = category['name']

        if best_match:
            return best_match

        if amount > 0:
            return 'Other Income'
        else:
            return 'Other Expense'

class ImportDialog:
    def __init__(self, parent, db, csv_importer, file_path):
        self.db = db
        self.csv_importer = csv_importer
        self.file_path = file_path
        self.success = False
        self.count = 0

        # Lightweight dialog to choose import template and options
        self.dialog = tk.Toplevel(parent)
        self.dialog.withdraw()
        self.dialog.title("Import CSV")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        
        ttk.Label(self.dialog, text="Import Template (optional):").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(self.dialog, textvariable=self.template_var, state='readonly')
        templates = self.db.get_import_templates()
        # Prepend auto-detect option; templates are optional
        template_combo['values'] = ['(Auto-detect columns)'] + [t['template_name'] for t in templates]
        template_combo.set('(Auto-detect columns)')
        template_combo.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

        self.has_header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.dialog, text="File has header row", variable=self.has_header_var).grid(row=1, column=0, columnspan=2, pady=5)

        self.auto_categorize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.dialog, text="Auto-categorize transactions", variable=self.auto_categorize_var).grid(row=2, column=0, columnspan=2, pady=5)

        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Import", command=self.do_import, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side='left', padx=5)

        self.dialog.columnconfigure(1, weight=1)
        
        self.dialog.update_idletasks()
        center_window(self.dialog)
        self.dialog.deiconify()
        self.dialog.grab_set()

    def do_import(self):
        template_name = self.template_var.get()
        
        # If auto-detect is selected, use a default template that lets parse_csv auto-detect columns
        if template_name == '(Auto-detect columns)' or not template_name:
            template = {
                'id': None,
                'template_name': 'Auto-detect',
                'account_name': 'Imported Transactions',
                'date_column': None,  # Will be auto-detected by parse_csv
                'description_column': None,  # Will be auto-detected by parse_csv
                'amount_column': None,  # Will be auto-detected by parse_csv
                'debit_column': None,
                'credit_column': None,
                'description2_column': None,
                'description_delimiter': ' - ',
                'skip_rows': 0,
                'notes': 'Auto-generated template'
            }
        else:
            templates = self.db.get_import_templates()
            template = next((t for t in templates if t['template_name'] == template_name), None)
            
            if not template:
                messagebox.showerror("Error", "Template not found")
                return

        try:
            # Delegate parsing and insertion to CSVImporter
            self.count = self.csv_importer.import_transactions(
                self.file_path,
                template=template,
                has_header=self.has_header_var.get(),
                auto_categorize=self.auto_categorize_var.get()
            )
            self.success = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")
