"""
Expense Predictor and Financial Analyzer
Provides AI-powered insights, predictions, and recommendations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class ExpensePredictor:
    """
    AI-powered expense prediction and financial analysis.
    Provides spending insights, predictions, and recommendations.
    """
    
    def __init__(self, db_manager):
        """Initialize with database manager."""
        self.db = db_manager
    
    def predict_next_month_expenses(self, user_id: int) -> Dict:
        """
        Predict next month's expenses based on historical data for a specific user.
        Uses weighted moving average with recent months having more weight.
        """
        # Get monthly trends for the past 6 months
        df = self.db.get_monthly_trends(user_id=user_id, months=6)
        
        if df.empty or len(df) < 2:
            return {
                'predicted_expense': 0,
                'predicted_income': 0,
                'confidence': 'low',
                'trend': 'insufficient_data',
                'message': 'Not enough historical data for accurate prediction. Add more transactions!'
            }
        
        # Calculate weighted average (more recent = higher weight)
        weights = np.array([1, 1.5, 2, 2.5, 3, 3.5])[:len(df)]
        weights = weights / weights.sum()
        
        # Predict expenses
        if 'expense' in df.columns:
            expenses = df['expense'].fillna(0).values
            predicted_expense = np.average(expenses, weights=weights)
        else:
            predicted_expense = 0
        
        # Predict income
        if 'income' in df.columns:
            incomes = df['income'].fillna(0).values
            predicted_income = np.average(incomes, weights=weights)
        else:
            predicted_income = 0
        
        # Determine trend
        if len(df) >= 3:
            recent_expenses = df['expense'].tail(3).mean() if 'expense' in df.columns else 0
            older_expenses = df['expense'].head(3).mean() if 'expense' in df.columns else 0
            
            if recent_expenses > older_expenses * 1.1:
                trend = 'increasing'
            elif recent_expenses < older_expenses * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # Confidence based on data points
        confidence = 'high' if len(df) >= 5 else 'medium' if len(df) >= 3 else 'low'
        
        return {
            'predicted_expense': round(predicted_expense, 2),
            'predicted_income': round(predicted_income, 2),
            'predicted_savings': round(predicted_income - predicted_expense, 2),
            'confidence': confidence,
            'trend': trend,
            'message': self._get_prediction_message(trend, predicted_expense, predicted_income)
        }
    
    def _get_prediction_message(self, trend: str, expense: float, income: float) -> str:
        """Generate human-readable prediction message."""
        if trend == 'increasing':
            return f"📈 Your spending is trending upward. Expected expense: ₹{expense:,.0f}"
        elif trend == 'decreasing':
            return f"📉 Great job! Your spending is decreasing. Expected expense: ₹{expense:,.0f}"
        elif trend == 'stable':
            return f"➡️ Your spending is stable. Expected expense: ₹{expense:,.0f}"
        else:
            return "📊 Add more transactions to get accurate predictions."
    
    def detect_overspending(self, user_id: int) -> List[Dict]:
        """
        Detect categories where user is overspending compared to their budget
        or historical average.
        """
        alerts = []
        
        # Check budget status
        budget_status = self.db.get_budget_status(user_id=user_id)
        
        for item in budget_status:
            percentage = item['percentage']
            if percentage >= 100:
                alerts.append({
                    'category': item['name'],
                    'icon': item['icon'],
                    'type': 'budget_exceeded',
                    'severity': 'high',
                    'message': f"Budget exceeded! Spent ₹{item['spent']:,.0f} of ₹{item['monthly_limit']:,.0f} limit",
                    'percentage': percentage
                })
            elif percentage >= 80:
                alerts.append({
                    'category': item['name'],
                    'icon': item['icon'],
                    'type': 'budget_warning',
                    'severity': 'medium',
                    'message': f"Approaching budget limit! {percentage:.0f}% used",
                    'percentage': percentage
                })
        
        # Detect unusual spending spikes (compared to category average)
        current_month = datetime.now().strftime('%Y-%m')
        current_breakdown = self.db.get_category_breakdown(
            user_id=user_id,
            start_date=datetime.now().replace(day=1).date()
        )
        
        # Get historical average for comparison
        historical_df = self.db.get_monthly_trends(user_id=user_id, months=3)
        
        if not historical_df.empty and 'expense' in historical_df.columns:
            avg_monthly_expense = historical_df['expense'].mean()
            
            for cat in current_breakdown:
                if cat['total'] > avg_monthly_expense * 0.5:  # Category > 50% of avg total
                    if cat['name'] not in [a['category'] for a in alerts]:
                        alerts.append({
                            'category': cat['name'],
                            'icon': cat['icon'],
                            'type': 'high_spending',
                            'severity': 'low',
                            'message': f"High spending detected: ₹{cat['total']:,.0f} this month",
                            'percentage': 0
                        })
        
        return alerts
    
    def get_recommendations(self, user_id: int) -> List[Dict]:
        """
        Generate personalized financial recommendations based on spending patterns.
        """
        recommendations = []
        
        # Get current month summary
        current_month_start = datetime.now().replace(day=1).date()
        summary = self.db.get_summary(user_id=user_id, start_date=current_month_start)
        
        # Get category breakdown
        breakdown = self.db.get_category_breakdown(user_id=user_id, start_date=current_month_start)
        
        # Get predictions
        predictions = self.predict_next_month_expenses(user_id=user_id)
        
        # Recommendation 1: Savings ratio
        if summary['income'] > 0:
            savings_ratio = (summary['income'] - summary['expense']) / summary['income'] * 100
            
            if savings_ratio < 10:
                recommendations.append({
                    'icon': '💰',
                    'title': 'Increase Your Savings',
                    'description': f'Your current savings rate is {savings_ratio:.1f}%. Aim for at least 20% of your income.',
                    'priority': 'high'
                })
            elif savings_ratio >= 20:
                recommendations.append({
                    'icon': '🌟',
                    'title': 'Great Savings Rate!',
                    'description': f'You\'re saving {savings_ratio:.1f}% of your income. Keep it up!',
                    'priority': 'low'
                })
        
        # Recommendation 2: Top spending category
        if breakdown:
            top_category = breakdown[0]
            total_expense = sum(c['total'] for c in breakdown)
            
            if total_expense > 0:
                top_percentage = (top_category['total'] / total_expense) * 100
                
                if top_percentage > 40:
                    recommendations.append({
                        'icon': '⚠️',
                        'title': f'Review {top_category["name"]} Spending',
                        'description': f'{top_category["name"]} accounts for {top_percentage:.0f}% of your expenses. Consider reducing it.',
                        'priority': 'medium'
                    })
        
        # Recommendation 3: Budget setup
        budgets = self.db.get_budgets(user_id=user_id)
        if not budgets:
            recommendations.append({
                'icon': '📋',
                'title': 'Set Up Budgets',
                'description': 'Create monthly budgets for your expense categories to better track spending.',
                'priority': 'medium'
            })
        
        # Recommendation 4: Spending trend
        if predictions['trend'] == 'increasing':
            recommendations.append({
                'icon': '📈',
                'title': 'Watch Your Spending Trend',
                'description': 'Your expenses are increasing month over month. Review recent purchases.',
                'priority': 'high'
            })
        
        # Recommendation 5: Emergency fund
        if summary['balance'] > 0:
            recommendations.append({
                'icon': '🏦',
                'title': 'Build Emergency Fund',
                'description': 'Consider saving 3-6 months of expenses in an emergency fund.',
                'priority': 'low'
            })
        
        return recommendations
    
    def get_spending_insights(self, user_id: int) -> Dict:
        """
        Generate comprehensive spending insights.
        """
        # Current month data
        current_month_start = datetime.now().replace(day=1).date()
        current_summary = self.db.get_summary(user_id=user_id, start_date=current_month_start)
        current_breakdown = self.db.get_category_breakdown(user_id=user_id, start_date=current_month_start)
        
        # Previous month data
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        prev_summary = self.db.get_summary(user_id=user_id, start_date=prev_month_start, end_date=prev_month_end)
        
        # Calculate changes
        expense_change = 0
        income_change = 0
        
        if prev_summary['expense'] > 0:
            expense_change = ((current_summary['expense'] - prev_summary['expense']) / 
                            prev_summary['expense']) * 100
        
        if prev_summary['income'] > 0:
            income_change = ((current_summary['income'] - prev_summary['income']) / 
                           prev_summary['income']) * 100
        
        # Daily average
        days_passed = datetime.now().day
        daily_avg = current_summary['expense'] / days_passed if days_passed > 0 else 0
        
        # Most frequent category
        most_frequent = None
        if current_breakdown:
            most_frequent = max(current_breakdown, key=lambda x: x['count'])
        
        # Biggest expense category
        biggest_expense = current_breakdown[0] if current_breakdown else None
        
        return {
            'current_month': {
                'income': current_summary['income'],
                'expense': current_summary['expense'],
                'balance': current_summary['balance']
            },
            'previous_month': {
                'income': prev_summary['income'],
                'expense': prev_summary['expense'],
                'balance': prev_summary['balance']
            },
            'changes': {
                'expense_change': round(expense_change, 1),
                'income_change': round(income_change, 1)
            },
            'daily_average': round(daily_avg, 2),
            'most_frequent_category': most_frequent,
            'biggest_expense_category': biggest_expense,
            'total_categories_used': len(current_breakdown)
        }
    
    def get_category_trends(self, user_id: int, category_id: int, months: int = 6) -> pd.DataFrame:
        """
        Get spending trend for a specific category over time.
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as total
            FROM transactions
            WHERE category_id = ? AND user_id = ?
            AND date >= date('now', ?)
            GROUP BY month
            ORDER BY month
        ''', (category_id, user_id, f'-{months} months'))
        
        results = cursor.fetchall()
        
        if not results:
            return pd.DataFrame(columns=['month', 'total'])
        
        return pd.DataFrame([dict(row) for row in results])
