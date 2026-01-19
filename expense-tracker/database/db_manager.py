"""
Database Manager for Expense Tracker
Handles all SQLite database operations
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import pandas as pd


class DatabaseManager:
    """Manages SQLite database operations for the expense tracker."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection and create tables if needed."""
        if db_path is None:
            # Get the directory where this file is located
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'expenses.db')
        
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
        self._seed_categories()
    
    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                icon TEXT,
                color TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(name, user_id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                description TEXT,
                category_id INTEGER,
                transaction_type TEXT NOT NULL,
                date DATE NOT NULL,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Budget limits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                user_id INTEGER,
                monthly_limit REAL NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(category_id, user_id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT,
                value TEXT,
                user_id INTEGER,
                PRIMARY KEY (key, user_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        self.conn.commit()
    
    def _seed_categories(self, user_id: int = None):
        """Seed default categories for a user if their category table is empty."""
        # This will be called both during init (for any existing global categories) 
        # and when a new user signs up.
        cursor = self.conn.cursor()
        
        check_query = 'SELECT COUNT(*) FROM categories WHERE user_id IS NULL' if user_id is None else 'SELECT COUNT(*) FROM categories WHERE user_id = ?'
        params = () if user_id is None else (user_id,)
        
        cursor.execute(check_query, params)
        
        if cursor.fetchone()[0] == 0:
            default_categories = [
                ('Food & Dining', 'expense', '🍔', '#FF6B6B', user_id),
                ('Transport', 'expense', '🚗', '#4ECDC4', user_id),
                ('Entertainment', 'expense', '🎬', '#45B7D1', user_id),
                ('Utilities', 'expense', '💡', '#96CEB4', user_id),
                ('Shopping', 'expense', '🛍️', '#FFEAA7', user_id),
                ('Healthcare', 'expense', '🏥', '#DDA0DD', user_id),
                ('Education', 'expense', '📚', '#98D8C8', user_id),
                ('Savings', 'expense', '💰', '#F7DC6F', user_id),
                ('Other', 'expense', '📦', '#BDC3C7', user_id),
                ('Salary', 'income', '💵', '#2ECC71', user_id),
                ('Freelance', 'income', '💻', '#3498DB', user_id),
                ('Investment', 'income', '📈', '#9B59B6', user_id),
                ('Gift', 'income', '🎁', '#E74C3C', user_id),
                ('Other Income', 'income', '💸', '#1ABC9C', user_id),
            ]
            
            cursor.executemany(
                'INSERT INTO categories (name, type, icon, color, user_id) VALUES (?, ?, ?, ?, ?)',
                default_categories
            )
            self.conn.commit()
    
    # ==================== User Operations ====================
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash a password with a salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        phash = hashlib.sha256((password + salt).encode()).hexdigest()
        return phash, salt

    def register_user(self, username: str, password: str, full_name: str = None) -> Tuple[bool, str]:
        """Register a new user."""
        try:
            phash, salt = self._hash_password(password)
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, full_name)
                VALUES (?, ?, ?, ?)
            ''', (username.lower(), phash, salt, full_name))
            user_id = cursor.lastrowid
            self.conn.commit()
            
            # Seed categories for the new user
            self._seed_categories(user_id)
            
            return True, "Registration successful"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data if successful."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username.lower(),))
        user = cursor.fetchone()
        
        if user:
            user_dict = dict(user)
            phash, _ = self._hash_password(password, user_dict['salt'])
            if phash == user_dict['password_hash']:
                # Don't return privacy sensitive data
                user_data = {
                    'id': user_dict['id'],
                    'username': user_dict['username'],
                    'full_name': user_dict['full_name']
                }
                return user_data
        
        return None
    
    # ==================== Category Operations ====================
    
    def get_categories(self, category_type: str = None, user_id: int = None) -> List[Dict]:
        """Get all categories, optionally filtered by type and user."""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM categories WHERE (user_id = ? OR user_id IS NULL)'
        params = [user_id]
        
        if category_type:
            query += ' AND type = ?'
            params.append(category_type)
        
        query += ' ORDER BY type, name'
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_category_by_id(self, category_id: int, user_id: int = None) -> Optional[Dict]:
        """Get a category by its ID."""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM categories WHERE id = ?'
        params = [category_id]
        
        if user_id is not None:
            query += ' AND (user_id = ? OR user_id IS NULL)'
            params.append(user_id)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_category_by_name(self, name: str, user_id: int = None) -> Optional[Dict]:
        """Get a category by its name."""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM categories WHERE name = ?'
        params = [name]
        
        if user_id is not None:
            query += ' AND (user_id = ? OR user_id IS NULL)'
            params.append(user_id)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_category(self, name: str, category_type: str, user_id: int, icon: str = '📦', color: str = '#BDC3C7') -> int:
        """Add a new category."""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO categories (name, type, icon, color, user_id) VALUES (?, ?, ?, ?, ?)',
            (name, category_type, icon, color, user_id)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    # ==================== Transaction Operations ====================
    
    def add_transaction(self, amount: float, description: str, category_id: int,
                       transaction_type: str, transaction_date: date, user_id: int) -> int:
        """Add a new transaction."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (amount, description, category_id, transaction_type, date, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (amount, description, category_id, transaction_type, transaction_date, user_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_transactions(self, user_id: int, start_date: date = None, end_date: date = None,
                        transaction_type: str = None, category_id: int = None,
                        limit: int = None) -> List[Dict]:
        """Get transactions with optional filters."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT t.*, c.name as category_name, c.icon as category_icon, c.color as category_color
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
        '''
        params = [user_id]
        
        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)
        
        if transaction_type:
            query += ' AND t.transaction_type = ?'
            params.append(transaction_type)
        
        if category_id:
            query += ' AND t.category_id = ?'
            params.append(category_id)
        
        query += ' ORDER BY t.date DESC, t.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_transaction_by_id(self, transaction_id: int, user_id: int = None) -> Optional[Dict]:
        """Get a transaction by its ID."""
        cursor = self.conn.cursor()
        query = '''
            SELECT t.*, c.name as category_name, c.icon as category_icon
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?
        '''
        params = [transaction_id]
        
        if user_id is not None:
            query += ' AND t.user_id = ?'
            params.append(user_id)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_transaction(self, transaction_id: int, user_id: int, amount: float = None,
                          description: str = None, category_id: int = None,
                          transaction_date: date = None) -> bool:
        """Update an existing transaction."""
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if amount is not None:
            updates.append('amount = ?')
            params.append(amount)
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if category_id is not None:
            updates.append('category_id = ?')
            params.append(category_id)
        
        if transaction_date is not None:
            updates.append('date = ?')
            params.append(transaction_date)
        
        if not updates:
            return False
        
        params.extend([transaction_id, user_id])
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Delete a transaction."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== Analytics Operations ====================
    
    def get_summary(self, user_id: int, start_date: date = None, end_date: date = None) -> Dict:
        """Get financial summary for a period."""
        cursor = self.conn.cursor()
        
        query_base = '''
            SELECT 
                transaction_type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ?
        '''
        params = [user_id]
        
        if start_date:
            query_base += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query_base += ' AND date <= ?'
            params.append(end_date)
        
        query_base += ' GROUP BY transaction_type'
        
        cursor.execute(query_base, params)
        results = cursor.fetchall()
        
        summary = {'income': 0, 'expense': 0, 'balance': 0}
        for row in results:
            summary[row['transaction_type']] = row['total'] or 0
        
        summary['balance'] = summary['income'] - summary['expense']
        return summary
    
    def get_category_breakdown(self, user_id: int, start_date: date = None, end_date: date = None,
                               transaction_type: str = 'expense') -> List[Dict]:
        """Get spending/income breakdown by category."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                c.id, c.name, c.icon, c.color,
                SUM(t.amount) as total,
                COUNT(t.id) as count
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.transaction_type = ? AND t.user_id = ?
        '''
        params = [transaction_type, user_id]
        
        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)
        
        query += ' GROUP BY c.id ORDER BY total DESC'
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_trends(self, user_id: int, months: int = 12) -> pd.DataFrame:
        """Get monthly income/expense trends."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date) as month,
                transaction_type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND date >= date('now', ?)
            GROUP BY month, transaction_type
            ORDER BY month
        ''', (user_id, f'-{months} months',))
        
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame(columns=['month', 'income', 'expense'])
        
        # Pivot the data
        data = {}
        for row in results:
            month = row['month']
            if month not in data:
                data[month] = {'month': month, 'income': 0, 'expense': 0}
            data[month][row['transaction_type']] = row['total']
        
        return pd.DataFrame(list(data.values()))
    
    def get_daily_expenses(self, user_id: int, days: int = 30) -> pd.DataFrame:
        """Get daily expense data for the specified number of days."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                date,
                SUM(amount) as total
            FROM transactions
            WHERE transaction_type = 'expense' AND user_id = ?
            AND date >= date('now', ?)
            GROUP BY date
            ORDER BY date
        ''', (user_id, f'-{days} days',))
        
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame(columns=['date', 'total'])
        
        return pd.DataFrame([dict(row) for row in results])
    
    def get_transactions_dataframe(self, user_id: int) -> pd.DataFrame:
        """Get all transactions as a pandas DataFrame."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, c.name as category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
            ORDER BY t.date DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        if not results:
            return pd.DataFrame()
        
        return pd.DataFrame([dict(row) for row in results])
    
    # ==================== Budget Operations ====================
    
    def set_budget(self, category_id: int, user_id: int, monthly_limit: float) -> bool:
        """Set or update budget for a category."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO budgets (category_id, user_id, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT(category_id, user_id) DO UPDATE SET monthly_limit = ?
        ''', (category_id, user_id, monthly_limit, monthly_limit))
        self.conn.commit()
        return True
    
    def get_budgets(self, user_id: int) -> List[Dict]:
        """Get all budget limits."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.*, c.name as category_name, c.icon as category_icon
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ?
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_budget_status(self, user_id: int, month: str = None) -> List[Dict]:
        """Get budget vs actual spending for each category."""
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                c.id, c.name, c.icon, c.color,
                b.monthly_limit,
                COALESCE(SUM(t.amount), 0) as spent
            FROM categories c
            LEFT JOIN budgets b ON c.id = b.category_id AND b.user_id = ?
            LEFT JOIN transactions t ON c.id = t.category_id 
                AND t.transaction_type = 'expense'
                AND t.user_id = ?
                AND strftime('%Y-%m', t.date) = ?
            WHERE (c.user_id = ? OR c.user_id IS NULL) AND c.type = 'expense'
            GROUP BY c.id
            HAVING b.monthly_limit IS NOT NULL
        ''', (user_id, user_id, month, user_id))
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            row_dict['remaining'] = row_dict['monthly_limit'] - row_dict['spent']
            row_dict['percentage'] = (row_dict['spent'] / row_dict['monthly_limit'] * 100) if row_dict['monthly_limit'] > 0 else 0
            results.append(row_dict)
        
        return results
    
    # ==================== Settings Operations ====================
    
    def get_setting(self, key: str, user_id: Optional[int] = None, default: str = None) -> Optional[str]:
        """Get a setting value by key."""
        cursor = self.conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT value FROM settings WHERE key = ? AND user_id = ?', (key, user_id))
        else:
            cursor.execute('SELECT value FROM settings WHERE key = ? AND user_id IS NULL', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str, user_id: Optional[int] = None) -> bool:
        """Set or update a setting value."""
        cursor = self.conn.cursor()
        if user_id is not None:
            cursor.execute('''
                INSERT INTO settings (key, value, user_id)
                VALUES (?, ?, ?)
                ON CONFLICT(key, user_id) DO UPDATE SET value = ?
            ''', (key, value, user_id, value))
        else:
            cursor.execute('''
                INSERT INTO settings (key, value, user_id)
                VALUES (?, ?, NULL)
                ON CONFLICT(key, user_id) WHERE user_id IS NULL DO UPDATE SET value = ?
            ''', (key, value, value))
        self.conn.commit()
        return True
    
    def clear_all_data(self, user_id: int):
        """Clear all transaction data for a user."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM budgets WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
