"""
AI Chat Assistant for Expense Tracker
Natural language processing for conversational expense management
"""

import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import random
import google.generativeai as genai
import json


class AIAssistant:
    """
    AI-powered chat assistant for natural language expense management.
    Understands user intent and automates transaction entry.
    """
    
    def __init__(self, db_manager, categorizer):
        """Initialize with database and categorizer."""
        self.db = db_manager
        self.categorizer = categorizer
        
        # Greeting responses
        self.greetings = [
            "Hello! 👋 I'm your AI expense assistant. How can I help you today?",
            "Hi there! 💰 I'm here to help manage your finances. What would you like to do?",
            "Hey! 🤖 Ready to help with your expenses. Just tell me what you need!",
        ]
        
        # Intent patterns for natural language understanding
        self.intent_patterns = {
            'add_expense': [
                r'(?:i\s+)?(?:spent|paid|bought|purchased|expense[d]?)\s+(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?\s*(?:on|for|at)?\s*(.+)?',
                r'(?:add|record|log)\s+(?:an?\s+)?expense\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?\s*(?:for|on)?\s*(.+)?',
                r'(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?\s+(?:spent\s+)?(?:on|for|at)\s+(.+)',
            ],
            'add_income': [
                r'(?:i\s+)?(?:received|got|earned|income)\s+(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?\s*(?:from|as|for)?\s*(.+)?',
                r'(?:add|record|log)\s+(?:an?\s+)?income\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?\s*(?:from|as)?\s*(.+)?',
                r'salary\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)',
            ],
            'check_balance': [
                r'(?:what\'?s?\s+)?(?:my\s+)?(?:current\s+)?balance',
                r'how\s+much\s+(?:do\s+i\s+have|money|left)',
                r'(?:show\s+)?(?:my\s+)?(?:account\s+)?summary',
            ],
            'check_spending': [
                r'how\s+much\s+(?:did\s+i\s+)?(?:spent?|spend)',
                r'(?:my\s+)?(?:total\s+)?(?:spending|expenses)',
                r'(?:show\s+)?spending\s+(?:on|for|in)\s+(.+)',
            ],
            'recent_transactions': [
                r'(?:show\s+)?(?:my\s+)?(?:recent|last|latest)\s+(?:transactions?|expenses?)',
                r'what\s+did\s+i\s+(?:spend|buy)\s+(?:recently|today|yesterday)',
            ],
            'set_budget': [
                r'set\s+(?:a\s+)?budget\s+(?:of\s+)?(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:for\s+)?(.+)?',
                r'budget\s+(.+)\s+(?:to|at)\s+(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)',
            ],
            'greeting': [
                r'^(?:hi|hello|hey|hola|greetings)[\s!]*$',
                r'^good\s+(?:morning|afternoon|evening)[\s!]*$',
            ],
            'help': [
                r'(?:what\s+can\s+you\s+do|help|commands?|how\s+to\s+use)',
            ],
            'thanks': [
                r'(?:thanks?|thank\s+you|thx|ty)',
            ],
        }
        
        # Quick action keywords for simple parsing
        self.expense_keywords = ['spent', 'paid', 'bought', 'purchased', 'expense', 'cost']
        self.income_keywords = ['received', 'earned', 'got', 'income', 'salary', 'paid']
        
        # Gemini setup
        self.api_key = None
        self.model = None
    
    def process_message(self, message: str, user_id: int) -> Dict:
        """
        Process user message and return appropriate response with action.
        
        Returns:
            Dict with keys: response, action, data
        """
        message = message.strip().lower()
        
        # Re-check API key in case it was updated in settings
        self.api_key = self.db.get_setting('gemini_api_key', user_id=user_id)
        if self.api_key and not self.model:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                pass

        if self.model:
            return self._process_with_gemini(message, user_id)
        
        # Fallback to local regex-based logic
        return self._process_with_regex(message, user_id)

    def _process_with_gemini(self, message: str, user_id: int) -> Dict:
        """Process message using Google Gemini AI."""
        current_month = datetime.now().strftime('%B %Y')
        summary = self.db.get_summary(user_id=user_id, start_date=date.today().replace(day=1))
        categories = self.db.get_categories(user_id=user_id)
        cat_list = ", ".join([f"{c['name']} ({c['type']})" for c in categories])
        
        prompt = f"""
        You are an AI Expense Assistant for a personal finance app.
        Current Month: {current_month}
        User Current Balance: ₹{summary['balance']:.2f}
        Income this month: ₹{summary['income']:.2f}
        Expenses this month: ₹{summary['expense']:.2f}
        Available Categories: {cat_list}

        Tasks:
        1. If the user wants to add an expense/income, extract "amount", "description", and "category".
        2. If the user asks a question about their spending, answer based on the summary provided.
        3. Keep responses helpful, concise, and friendly. Use emojis.
        4. If adding a transaction, return a JSON block at the end with keys: "action" (add_expense/add_income), "amount", "description", "category".

        User Message: "{message}"
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Extract JSON if present
            action = 'chat'
            data = None
            
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if not json_match:
                json_match = re.search(r'(\{.*?\})', text, re.DOTALL)
                
            if json_match:
                try:
                    js_data = json.loads(json_match.group(1))
                    if js_data.get('action') == 'add_expense':
                        return self._handle_add_expense({'amount': js_data['amount'], 'description': js_data['description']}, user_id)
                    elif js_data.get('action') == 'add_income':
                        return self._handle_add_income({'amount': js_data['amount'], 'description': js_data['description']}, user_id)
                except:
                    pass
            
            return {
                'response': text,
                'action': action,
                'data': data
            }
        except Exception as e:
            # Fallback to regex if Gemini fails
            print(f"Gemini error: {e}")
            return self._process_with_regex(message, user_id)

    def _process_with_regex(self, message: str, user_id: int) -> Dict:
        """Existing regex-based processing logic."""
        
        # Check for greeting
        if self._match_intent(message, 'greeting'):
            return {
                'response': random.choice(self.greetings),
                'action': 'greeting',
                'data': None
            }
        
        # Check for help
        if self._match_intent(message, 'help'):
            return self._get_help_response()
        
        # Check for thanks
        if self._match_intent(message, 'thanks'):
            return {
                'response': "You're welcome! 😊 Let me know if you need anything else!",
                'action': 'thanks',
                'data': None
            }
        
        # Check for expense addition
        expense_data = self._extract_expense(message)
        if expense_data:
            return self._handle_add_expense(expense_data, user_id)
        
        # Check for income addition
        income_data = self._extract_income(message)
        if income_data:
            return self._handle_add_income(income_data, user_id)
        
        # Check for balance query
        if self._match_intent(message, 'check_balance'):
            return self._handle_check_balance(user_id)
        
        # Check for spending query
        if self._match_intent(message, 'check_spending'):
            return self._handle_check_spending(message, user_id)
        
        # Check for recent transactions
        if self._match_intent(message, 'recent_transactions'):
            return self._handle_recent_transactions(user_id)
        
        # Check for budget setting
        budget_data = self._extract_budget(message)
        if budget_data:
            return self._handle_set_budget(budget_data, user_id)
        
        # Default: try to understand as expense with smart parsing
        smart_parse = self._smart_parse(message, user_id)
        if smart_parse:
            return smart_parse
        
        # Fallback
        return self._get_fallback_response(message)
    
    def _match_intent(self, message: str, intent: str) -> bool:
        """Check if message matches an intent pattern."""
        patterns = self.intent_patterns.get(intent, [])
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _extract_expense(self, message: str) -> Optional[Dict]:
        """Extract expense details from message."""
        for pattern in self.intent_patterns['add_expense']:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                amount = float(groups[0]) if groups[0] else None
                description = groups[1].strip() if len(groups) > 1 and groups[1] else None
                
                if amount:
                    return {'amount': amount, 'description': description}
        return None
    
    def _extract_income(self, message: str) -> Optional[Dict]:
        """Extract income details from message."""
        for pattern in self.intent_patterns['add_income']:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                amount = float(groups[0]) if groups[0] else None
                description = groups[1].strip() if len(groups) > 1 and groups[1] else None
                
                if amount:
                    return {'amount': amount, 'description': description or 'Income'}
        return None
    
    def _extract_budget(self, message: str) -> Optional[Dict]:
        """Extract budget details from message."""
        for pattern in self.intent_patterns['set_budget']:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                # Pattern might have amount first or category first
                try:
                    amount = float(groups[0])
                    category = groups[1] if len(groups) > 1 else None
                except ValueError:
                    category = groups[0]
                    amount = float(groups[1]) if len(groups) > 1 else None
                
                if amount:
                    return {'amount': amount, 'category': category}
        return None
    
    def _smart_parse(self, message: str, user_id: int) -> Optional[Dict]:
        """Smart parsing for messages that don't match patterns."""
        # Look for any number in the message
        amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(?:₹|rs\.?|inr)?', message)
        
        if amount_match:
            amount = float(amount_match.group(1))
            
            # Remove the amount from message to get description
            description = re.sub(r'(?:₹|rs\.?|inr)?\s*\d+(?:\.\d{1,2})?\s*(?:₹|rs\.?|inr)?', '', message).strip()
            description = re.sub(r'(?:spent|paid|for|on|at|expense|income)\s*', '', description).strip()
            
            if amount > 0:
                # Determine if it's income or expense based on keywords
                is_income = any(kw in message for kw in self.income_keywords)
                
                if is_income:
                    return self._handle_add_income({'amount': amount, 'description': description or 'Income'}, user_id)
                else:
                    return self._handle_add_expense({'amount': amount, 'description': description or 'Expense'}, user_id)
        
        return None
    
    def _handle_add_expense(self, data: Dict, user_id: int) -> Dict:
        """Handle adding an expense."""
        amount = data['amount']
        description = data.get('description', 'Expense')
        
        # Use AI to categorize
        category_name, confidence = self.categorizer.predict(description)
        
        # Get category from database
        category = self.db.get_category_by_name(category_name, user_id=user_id)
        if not category:
            # Fallback to 'Other' category
            categories = self.db.get_categories('expense', user_id=user_id)
            category = next((c for c in categories if 'Other' in c['name']), categories[0])
        
        # Add transaction
        transaction_id = self.db.add_transaction(
            amount=amount,
            description=description.title() if description else 'Expense',
            category_id=category['id'],
            transaction_type='expense',
            transaction_date=date.today(),
            user_id=user_id
        )
        
        response = f"""✅ **Expense Added Successfully!**

💸 **Amount:** ₹{amount:,.2f}
📝 **Description:** {description.title() if description else 'Expense'}
🏷️ **Category:** {category.get('icon', '📦')} {category['name']}
📅 **Date:** {date.today().strftime('%d %b %Y')}

*I categorized this as {category['name']} based on your description.*

Would you like to add another expense or check your balance?"""
        
        return {
            'response': response,
            'action': 'expense_added',
            'data': {
                'id': transaction_id,
                'amount': amount,
                'category': category['name'],
                'description': description
            }
        }
    
    def _handle_add_income(self, data: Dict, user_id: int) -> Dict:
        """Handle adding income."""
        amount = data['amount']
        description = data.get('description', 'Income')
        
        # Categorize income
        category_name, _ = self.categorizer.predict(description)
        
        # Get income category
        category = self.db.get_category_by_name(category_name, user_id=user_id)
        if not category or category.get('type') != 'income':
            # Fallback to salary or other income
            categories = self.db.get_categories('income', user_id=user_id)
            if 'salary' in description.lower():
                category = next((c for c in categories if 'Salary' in c['name']), categories[0])
            else:
                category = categories[0] if categories else None
        
        if not category:
            return {
                'response': "❌ Sorry, I couldn't find an income category. Please try again.",
                'action': 'error',
                'data': None
            }
        
        # Add transaction
        transaction_id = self.db.add_transaction(
            amount=amount,
            description=description.title() if description else 'Income',
            category_id=category['id'],
            transaction_type='income',
            transaction_date=date.today(),
            user_id=user_id
        )
        
        response = f"""✅ **Income Added Successfully!**

💵 **Amount:** ₹{amount:,.2f}
📝 **Description:** {description.title() if description else 'Income'}
🏷️ **Category:** {category.get('icon', '💰')} {category['name']}
📅 **Date:** {date.today().strftime('%d %b %Y')}

Great! Your income has been recorded. 🎉"""
        
        return {
            'response': response,
            'action': 'income_added',
            'data': {
                'id': transaction_id,
                'amount': amount,
                'category': category['name'],
                'description': description
            }
        }
    
    def _handle_check_balance(self, user_id: int) -> Dict:
        """Handle balance check request."""
        current_month = date.today().replace(day=1)
        summary = self.db.get_summary(user_id=user_id, start_date=current_month)
        
        # Get overall summary too
        overall = self.db.get_summary(user_id=user_id)
        
        balance = summary['balance']
        status_emoji = "🟢" if balance >= 0 else "🔴"
        
        response = f"""📊 **Your Financial Summary**

**This Month ({datetime.now().strftime('%B %Y')}):**
{status_emoji} Balance: ₹{balance:,.2f}
💵 Income: ₹{summary['income']:,.2f}
💸 Expenses: ₹{summary['expense']:,.2f}

**All Time:**
💰 Total Balance: ₹{overall['balance']:,.2f}

{'Great job keeping your balance positive! 🎉' if balance >= 0 else 'Your expenses exceed your income this month. Consider reviewing your spending. 💡'}"""
        
        return {
            'response': response,
            'action': 'balance_checked',
            'data': summary
        }
    
    def _handle_check_spending(self, message: str, user_id: int) -> Dict:
        """Handle spending check request."""
        current_month = date.today().replace(day=1)
        breakdown = self.db.get_category_breakdown(user_id=user_id, start_date=current_month)
        
        if not breakdown:
            return {
                'response': "📊 You haven't recorded any expenses this month yet. Start by telling me what you spent!",
                'action': 'spending_checked',
                'data': None
            }
        
        total = sum(c['total'] for c in breakdown)
        
        # Build spending breakdown
        spending_lines = []
        for c in breakdown[:5]:  # Top 5 categories
            percentage = (c['total'] / total * 100) if total > 0 else 0
            spending_lines.append(f"  {c['icon']} {c['name']}: ₹{c['total']:,.2f} ({percentage:.1f}%)")
        
        response = f"""📊 **Your Spending This Month**

💸 **Total Spent:** ₹{total:,.2f}

**Top Categories:**
{chr(10).join(spending_lines)}

{'💡 Tip: Your biggest expense is ' + breakdown[0]['name'] + '. Consider if you can reduce spending there!' if breakdown else ''}"""
        
        return {
            'response': response,
            'action': 'spending_checked',
            'data': {'total': total, 'breakdown': breakdown}
        }
    
    def _handle_recent_transactions(self, user_id: int) -> Dict:
        """Handle recent transactions request."""
        transactions = self.db.get_transactions(user_id=user_id, limit=5)
        
        if not transactions:
            return {
                'response': "📝 No transactions recorded yet. Start by telling me about your expenses!",
                'action': 'transactions_listed',
                'data': None
            }
        
        tx_lines = []
        for t in transactions:
            prefix = "💸" if t['transaction_type'] == 'expense' else "💵"
            sign = "-" if t['transaction_type'] == 'expense' else "+"
            tx_lines.append(f"  {prefix} {t.get('description', 'No description')}: {sign}₹{t['amount']:,.2f}")
        
        response = f"""📋 **Your Recent Transactions**

{chr(10).join(tx_lines)}

Would you like to add a new transaction or see your balance?"""
        
        return {
            'response': response,
            'action': 'transactions_listed',
            'data': transactions
        }
    
    def _handle_set_budget(self, data: Dict, user_id: int) -> Dict:
        """Handle budget setting."""
        amount = data['amount']
        category_name = data.get('category', '')
        
        if not category_name:
            return {
                'response': "💳 Which category would you like to set a budget for? (e.g., 'Set budget of ₹5000 for Food')",
                'action': 'need_category',
                'data': None
            }
        
        # Find the category
        categories = self.db.get_categories('expense', user_id=user_id)
        category = None
        
        for c in categories:
            if category_name.lower() in c['name'].lower():
                category = c
                break
        
        if not category:
            return {
                'response': f"❓ I couldn't find a category matching '{category_name}'. Try: Food, Transport, Entertainment, Shopping, etc.",
                'action': 'category_not_found',
                'data': None
            }
        
        # Set the budget
        self.db.set_budget(category['id'], user_id, amount)
        
        response = f"""✅ **Budget Set Successfully!**

{category['icon']} **{category['name']}**
💳 Monthly Limit: ₹{amount:,.2f}

I'll alert you when you're approaching or exceeding this budget! 📢"""
        
        return {
            'response': response,
            'action': 'budget_set',
            'data': {'category': category['name'], 'amount': amount}
        }
    
    def _get_help_response(self) -> Dict:
        """Return help information."""
        response = """🤖 **I'm Your AI Expense Assistant!**

Here's what I can do for you:

**💸 Add Expenses:**
• "Spent ₹500 on groceries"
• "Paid 200 for coffee"
• "Bought lunch for ₹150"

**💵 Add Income:**
• "Received salary of ₹50000"
• "Got ₹5000 from freelance"

**📊 Check Finances:**
• "What's my balance?"
• "Show my spending"
• "Recent transactions"

**💳 Set Budgets:**
• "Set budget of ₹10000 for food"

Just type naturally, and I'll understand! 🎯"""
        
        return {
            'response': response,
            'action': 'help',
            'data': None
        }
    
    def _get_fallback_response(self, message: str) -> Dict:
        """Return fallback response when intent is not understood."""
        suggestions = [
            "Try saying 'Spent ₹500 on groceries'",
            "Try 'What's my balance?'",
            "Try 'Show my recent expenses'",
        ]
        
        response = f"""🤔 I'm not sure I understood that correctly.

{random.choice(suggestions)}

Type **'help'** to see all the things I can do! 💡"""
        
        return {
            'response': response,
            'action': 'fallback',
            'data': None
        }
    
    def get_quick_insights(self, user_id: int) -> str:
        """Get quick insights for proactive assistance."""
        current_month = date.today().replace(day=1)
        summary = self.db.get_summary(user_id=user_id, start_date=current_month)
        breakdown = self.db.get_category_breakdown(user_id=user_id, start_date=current_month)
        
        insights = []
        
        # Balance insight
        if summary['balance'] < 0:
            insights.append("⚠️ Your expenses exceed income this month!")
        elif summary['income'] > 0 and summary['expense'] / summary['income'] > 0.8:
            insights.append("📊 You've spent 80%+ of your income this month.")
        
        # Top category insight
        if breakdown:
            top = breakdown[0]
            insights.append(f"🏆 Top spending: {top['icon']} {top['name']} (₹{top['total']:,.0f})")
        
        return " | ".join(insights) if insights else "💰 All looks good! Keep tracking your expenses."
