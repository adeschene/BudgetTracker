import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "budget_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                category TEXT,
                account TEXT,
                transaction_type TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                keywords TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                balance REAL DEFAULT 0,
                last_updated TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS net_worth_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                asset_type TEXT,
                value REAL NOT NULL,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT UNIQUE NOT NULL,
                asset_type TEXT,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                monthly_target REAL NOT NULL,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                date_column TEXT NOT NULL,
                description_column TEXT NOT NULL,
                description2_column TEXT,
                description_delimiter TEXT DEFAULT ' - ',
                amount_column TEXT,
                debit_column TEXT,
                credit_column TEXT,
                skip_rows INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS description_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                rule_order INTEGER NOT NULL,
                pattern TEXT NOT NULL,
                replacement TEXT NOT NULL,
                category TEXT,
                ignore INTEGER DEFAULT 0,
                FOREIGN KEY (template_id) REFERENCES import_templates(id) ON DELETE CASCADE
            )
        ''')

        self._insert_default_categories(cursor)

        self._migrate_import_templates_table(cursor)

        conn.commit()
        conn.close()

    def _migrate_net_worth_table(self, cursor):
        cursor.execute("PRAGMA table_info(net_worth_entries)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_recurring' not in columns:
            cursor.execute('ALTER TABLE net_worth_entries ADD COLUMN is_recurring INTEGER DEFAULT 0')
        if 'recurring_start_date' not in columns:
            cursor.execute('ALTER TABLE net_worth_entries ADD COLUMN recurring_start_date TEXT')
        if 'recurring_end_date' not in columns:
            cursor.execute('ALTER TABLE net_worth_entries ADD COLUMN recurring_end_date TEXT')
        if 'is_auto_generated' not in columns:
            cursor.execute('ALTER TABLE net_worth_entries ADD COLUMN is_auto_generated INTEGER DEFAULT 0')

    def _migrate_import_templates_table(self, cursor):
        cursor.execute("PRAGMA table_info(import_templates)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'skip_rows' not in columns:
            cursor.execute('ALTER TABLE import_templates ADD COLUMN skip_rows INTEGER DEFAULT 0')
        if 'debit_column' not in columns:
            cursor.execute('ALTER TABLE import_templates ADD COLUMN debit_column TEXT')
        if 'credit_column' not in columns:
            cursor.execute('ALTER TABLE import_templates ADD COLUMN credit_column TEXT')
        if 'description2_column' not in columns:
            cursor.execute('ALTER TABLE import_templates ADD COLUMN description2_column TEXT')
        if 'description_delimiter' not in columns:
            cursor.execute('ALTER TABLE import_templates ADD COLUMN description_delimiter TEXT DEFAULT \' - \'')

        cursor.execute("PRAGMA table_info(description_rules)")
        rule_columns = [column[1] for column in cursor.fetchall()]

        if 'ignore' not in rule_columns:
            cursor.execute('ALTER TABLE description_rules ADD COLUMN ignore INTEGER DEFAULT 0')
    
    def _insert_default_categories(self, cursor):
        default_categories = [
            ('Groceries', 'expense', 'grocery,supermarket,food'),
            ('Dining', 'expense', 'restaurant,cafe,food,dining'),
            ('Transportation', 'expense', 'gas,fuel,uber,lyft,transit'),
            ('Utilities', 'expense', 'electric,water,gas,internet,phone'),
            ('Entertainment', 'expense', 'movie,game,streaming,netflix'),
            ('Shopping', 'expense', 'amazon,store,retail'),
            ('Healthcare', 'expense', 'doctor,pharmacy,medical,health'),
            ('Housing', 'expense', 'rent,mortgage,insurance'),
            ('Salary', 'income', 'salary,paycheck,wage'),
            ('Investment', 'income', 'dividend,interest,capital'),
            ('Other Income', 'income', ''),
            ('Other Expense', 'expense', '')
        ]
        
        for name, cat_type, keywords in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type, keywords)
                VALUES (?, ?, ?)
            ''', (name, cat_type, keywords))
    
    def add_transaction(self, date: str, description: str, amount: float, 
                       category: str = None, account: str = None, 
                       transaction_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (date, description, amount, category, account, transaction_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, description, amount, category, account, transaction_type, notes))
        
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        return transaction_id
    
    def get_transactions(self, start_date: str = None, end_date: str = None, 
                        category: str = None, account: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM transactions WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        if category:
            query += ' AND category = ?'
            params.append(category)
        if account:
            query += ' AND account = ?'
            params.append(account)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return transactions
    
    def update_transaction(self, transaction_id: int, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        values = list(kwargs.values()) + [transaction_id]
        
        cursor.execute(f'UPDATE transactions SET {set_clause} WHERE id = ?', values)
        
        conn.commit()
        conn.close()
    
    def delete_transaction(self, transaction_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        conn.close()
    
    def add_category(self, name: str, cat_type: str, keywords: str = ''):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO categories (name, type, keywords) VALUES (?, ?, ?)',
                      (name, cat_type, keywords))
        conn.commit()
        conn.close()
    
    def get_categories(self, cat_type: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cat_type:
            cursor.execute('SELECT * FROM categories WHERE type = ?', (cat_type,))
        else:
            cursor.execute('SELECT * FROM categories')
        
        columns = [description[0] for description in cursor.description]
        categories = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def add_account(self, name: str, account_type: str, balance: float = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO accounts (name, type, balance, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (name, account_type, balance, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_accounts(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts')
        columns = [description[0] for description in cursor.description]
        accounts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return accounts
    
    def update_account_balance(self, account_name: str, balance: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts SET balance = ?, last_updated = ?
            WHERE name = ?
        ''', (balance, datetime.now().isoformat(), account_name))
        conn.commit()
        conn.close()
    
    def add_net_worth_entry(self, date: str, asset_name: str, value: float,
                           asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO net_worth_entries (date, asset_name, asset_type, value, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, asset_name, asset_type, value, notes))

        conn.commit()
        conn.close()

    def update_net_worth_entry(self, entry_id: int, date: str, asset_name: str, value: float,
                              asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE net_worth_entries
            SET date = ?, asset_name = ?, asset_type = ?, value = ?, notes = ?
            WHERE id = ?
        ''', (date, asset_name, asset_type, value, notes, entry_id))
        conn.commit()
        conn.close()

    def get_net_worth_entries(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM net_worth_entries WHERE 1=1'
        params = []

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' ORDER BY date DESC'

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        entries = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return entries

    def add_asset_template(self, asset_name: str, asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO asset_templates (asset_name, asset_type, notes)
            VALUES (?, ?, ?)
        ''', (asset_name, asset_type, notes))
        conn.commit()
        conn.close()

    def get_asset_templates(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM asset_templates ORDER BY asset_name')
        columns = [description[0] for description in cursor.description]
        templates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return templates

    def update_asset_template(self, template_id: int, asset_name: str, asset_type: str = None, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE asset_templates
            SET asset_name = ?, asset_type = ?, notes = ?
            WHERE id = ?
        ''', (asset_name, asset_type, notes, template_id))
        conn.commit()
        conn.close()

    def delete_asset_template(self, template_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM asset_templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    def apply_templates_to_month(self, year: int, month: int, template_values: Dict[int, float]):
        from calendar import monthrange
        start_date = f"{year}-{month:02d}-01"
        last_day = monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day:02d}"

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT asset_name FROM net_worth_entries
            WHERE date >= ? AND date <= ?
        ''', (start_date, end_date))
        existing_assets = {row[0] for row in cursor.fetchall()}

        templates = self.get_asset_templates()

        for template in templates:
            if template['asset_name'] not in existing_assets and template['id'] in template_values:
                cursor.execute('''
                    INSERT INTO net_worth_entries (date, asset_name, asset_type, value, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (start_date, template['asset_name'], template['asset_type'],
                      template_values[template['id']], template['notes']))

        conn.commit()
        conn.close()

    def delete_net_worth_entry(self, entry_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM net_worth_entries WHERE id = ?', (entry_id,))
        conn.commit()
        conn.close()

    def get_net_worth_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        conn = self.get_connection()
        cursor = conn.cursor()

        if not start_date:
            start_date = '1900-01-01'
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        query = '''
            SELECT asset_type, SUM(value) as total
            FROM (
                SELECT asset_name, asset_type, value
                FROM net_worth_entries e1
                WHERE date = (
                    SELECT MAX(date)
                    FROM net_worth_entries e2
                    WHERE e2.asset_name = e1.asset_name
                    AND e2.date >= ?
                    AND e2.date <= ?
                )
                GROUP BY asset_name
            )
            GROUP BY asset_type
        '''

        cursor.execute(query, (start_date, end_date))

        summary = {row[0] or 'Other': row[1] for row in cursor.fetchall()}
        conn.close()
        return summary
    
    def get_spending_by_category(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE amount < 0
        '''
        params = []

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' GROUP BY category'

        cursor.execute(query, params)
        spending = {row[0] or 'Uncategorized': abs(row[1]) for row in cursor.fetchall()}

        conn.close()
        return spending

    def add_budget_target(self, category: str, monthly_target: float, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budget_targets (category, monthly_target, notes)
            VALUES (?, ?, ?)
        ''', (category, monthly_target, notes))
        conn.commit()
        conn.close()

    def get_budget_targets(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, category, monthly_target, notes FROM budget_targets ORDER BY category')

        budgets = []
        for row in cursor.fetchall():
            budgets.append({
                'id': row[0],
                'category': row[1],
                'monthly_target': row[2],
                'notes': row[3]
            })

        conn.close()
        return budgets

    def update_budget_target(self, budget_id: int, category: str, monthly_target: float, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE budget_targets
            SET category = ?, monthly_target = ?, notes = ?
            WHERE id = ?
        ''', (category, monthly_target, notes, budget_id))
        conn.commit()
        conn.close()

    def delete_budget_target(self, budget_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budget_targets WHERE id = ?', (budget_id,))
        conn.commit()
        conn.close()

    def get_net_worth_history(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT strftime('%Y-%m', date) as month
            FROM net_worth_entries
            ORDER BY month
        ''')

        months = [row[0] for row in cursor.fetchall()]
        history = []

        for month in months:
            year, month_num = month.split('-')
            start_date = f"{year}-{month_num}-01"

            if month_num == '12':
                end_date = f"{year}-12-31"
            else:
                last_day = 31
                if month_num in ['04', '06', '09', '11']:
                    last_day = 30
                elif month_num == '02':
                    last_day = 29 if int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0) else 28
                end_date = f"{year}-{month_num}-{last_day}"

            summary = self.get_net_worth_summary(start_date, end_date)
            total = sum(summary.values())

            history.append({
                'month': month,
                'total': total,
                'breakdown': summary
            })

        conn.close()
        return history

    def add_import_template(self, template_name: str, account_name: str, date_column: str,
                           description_column: str, amount_column: str = None, skip_rows: int = 0, notes: str = None,
                           debit_column: str = None, credit_column: str = None,
                           description2_column: str = None, description_delimiter: str = ' - '):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO import_templates (template_name, account_name, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (template_name, account_name, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes))
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return template_id

    def get_import_templates(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, template_name, account_name, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes
            FROM import_templates
            ORDER BY template_name
        ''')

        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row[0],
                'template_name': row[1],
                'account_name': row[2],
                'date_column': row[3],
                'description_column': row[4],
                'description2_column': row[5],
                'description_delimiter': row[6],
                'amount_column': row[7],
                'debit_column': row[8],
                'credit_column': row[9],
                'skip_rows': row[10],
                'notes': row[11]
            })

        conn.close()
        return templates

    def get_import_template(self, template_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, template_name, account_name, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes
            FROM import_templates
            WHERE id = ?
        ''', (template_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'template_name': row[1],
                'account_name': row[2],
                'date_column': row[3],
                'description_column': row[4],
                'description2_column': row[5],
                'description_delimiter': row[6],
                'amount_column': row[7],
                'debit_column': row[8],
                'credit_column': row[9],
                'skip_rows': row[10],
                'notes': row[11]
            }
        return None

    def update_import_template(self, template_id: int, template_name: str, account_name: str,
                              date_column: str, description_column: str, amount_column: str = None, skip_rows: int = 0, notes: str = None,
                              debit_column: str = None, credit_column: str = None,
                              description2_column: str = None, description_delimiter: str = ' - '):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE import_templates
            SET template_name = ?, account_name = ?, date_column = ?, description_column = ?, description2_column = ?, description_delimiter = ?, amount_column = ?, debit_column = ?, credit_column = ?, skip_rows = ?, notes = ?
            WHERE id = ?
        ''', (template_name, account_name, date_column, description_column, description2_column, description_delimiter, amount_column, debit_column, credit_column, skip_rows, notes, template_id))
        conn.commit()
        conn.close()

    def delete_import_template(self, template_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM import_templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    def add_description_rule(self, template_id: int, rule_order: int, pattern: str,
                            replacement: str, category: str = None, ignore: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO description_rules (template_id, rule_order, pattern, replacement, category, ignore)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_id, rule_order, pattern, replacement, category, ignore))
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rule_id

    def get_description_rules(self, template_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, template_id, rule_order, pattern, replacement, category, ignore
            FROM description_rules
            WHERE template_id = ?
            ORDER BY rule_order
        ''', (template_id,))

        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0],
                'template_id': row[1],
                'rule_order': row[2],
                'pattern': row[3],
                'replacement': row[4],
                'category': row[5],
                'ignore': row[6]
            })

        conn.close()
        return rules

    def update_description_rule(self, rule_id: int, rule_order: int, pattern: str,
                               replacement: str, category: str = None, ignore: int = 0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE description_rules
            SET rule_order = ?, pattern = ?, replacement = ?, category = ?, ignore = ?
            WHERE id = ?
        ''', (rule_order, pattern, replacement, category, ignore, rule_id))
        conn.commit()
        conn.close()

    def delete_description_rule(self, rule_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM description_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()

    def reorder_description_rules(self, template_id: int, rule_ids_in_order: List[int]):
        conn = self.get_connection()
        cursor = conn.cursor()
        for order, rule_id in enumerate(rule_ids_in_order):
            cursor.execute('UPDATE description_rules SET rule_order = ? WHERE id = ?', (order, rule_id))
        conn.commit()
        conn.close()
