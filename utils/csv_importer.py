import csv
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from database.db_manager import DatabaseManager

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

            debit_amount = self._parse_amount(debit_str) if debit_str else 0.0
            credit_amount = self._parse_amount(credit_str) if credit_str else 0.0

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

        # If parsing fails, return the original string (caller may handle it)
        return date_str

    def _parse_amount(self, amount_str: str) -> float:
        amount_str = amount_str.strip()
        amount_str = re.sub(r'[^\d\.\-\+]', '', amount_str)

        try:
            return float(amount_str)
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

        rules = self.db.get_description_rules(template['id'])

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
                amount=trans['amount'],
                category=category,
                account=account_name,
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

                    if rule['category']:
                        category = rule['category']

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
