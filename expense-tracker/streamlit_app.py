"""
AI-Based Smart Expense Tracker
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from ml.categorizer import ExpenseCategorizer
from ml.predictor import ExpensePredictor
from ml.assistant import AIAssistant
from utils.helpers import (
    format_currency, format_currency_compact, get_greeting,
    get_date_range, format_date_friendly, days_remaining_in_month,
    generate_color_palette
)

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --background-dark: #1a1a2e;
        --card-background: #16213e;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Gradient header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    .metric-card h3 {
        color: #94a3b8;
        font-size: 0.9rem;
        margin: 0;
        font-weight: 500;
    }
    
    .metric-card .value {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-card .change {
        font-size: 0.85rem;
    }
    
    .change.positive { color: #10B981; }
    .change.negative { color: #EF4444; }
    
    /* Transaction list */
    .transaction-item {
        background: rgba(255,255,255,0.05);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid rgba(255,255,255,0.08);
        transition: all 0.2s ease;
    }
    
    .transaction-item:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.15);
    }
    
    .transaction-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
    }
    
    .transaction-details {
        flex: 1;
    }
    
    .transaction-description {
        color: white;
        font-weight: 500;
    }
    
    .transaction-category {
        color: #94a3b8;
        font-size: 0.85rem;
    }
    
    .transaction-amount {
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .amount-expense { color: #EF4444; }
    .amount-income { color: #10B981; }
    
    /* Alert cards */
    .alert-card {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .alert-high {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .alert-medium {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .alert-low {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Recommendation cards */
    .recommendation-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .recommendation-title {
        color: white;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .recommendation-text {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Progress bars */
    .budget-progress {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .budget-progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Input styling */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select,
    .stDateInput>div>div>input {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94a3b8;
        font-weight: 500;
        padding: 1rem 0;
    }
    
    .stTabs [aria-selected="true"] {
        color: white;
        border-bottom: 2px solid #667eea;
    }
    
    /* Chart container */
    .chart-container {
        background: rgba(255,255,255,0.03);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #94a3b8;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ==================== Initialize Session State ====================
@st.cache_resource
def get_database():
    """Get or create database connection."""
    return DatabaseManager()

@st.cache_resource
def get_categorizer():
    """Get or create ML categorizer."""
    return ExpenseCategorizer()

def init_session_state():
    """Initialize session state variables."""
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = 'Dashboard'
    if 'edit_transaction_id' not in st.session_state:
        st.session_state.edit_transaction_id = None
    if 'show_add_form' not in st.session_state:
        st.session_state.show_add_form = False
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

init_session_state()
db = get_database()
categorizer = get_categorizer()
predictor = ExpensePredictor(db)
assistant = AIAssistant(db, categorizer)

# ==================== Authentication UI ====================
def render_auth():
    """Render Login and Sign-up forms."""
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; padding: 2rem 0;">
        <div style="text-align: center; max-width: 500px;">
            <h1 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; margin-bottom: 0.5rem;">
            M
            </h1>
            <h2 style="font-size: 1.8rem; font-weight: 700;">Smart Expense Tracker</h2>
            <p style="color: #94a3b8; font-size: 1.1rem;">Manage your finances with AI intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    user = db.authenticate_user(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user['id']
                        st.session_state.user_data = user
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    if not full_name or not username or not password:
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = db.register_user(username, password, full_name)
                        if success:
                            st.success("Account created! Please login.")
                        else:
                            st.error(message)


# ==================== Sidebar Navigation ====================
with st.sidebar:
    # Logo and Branding
    try:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=250)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.5rem;">
                💰 ExpenseAI
                </h2>
                <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">Smart Finance Tracker</p>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("## 💰 ExpenseAI")

    if st.session_state.logged_in:
        st.markdown(f"### 👋 Hello, {st.session_state.user_data['full_name'].split()[0]}!")
        st.markdown("---")
        
        # Navigation
        pages = {
            '📊 Dashboard': 'Dashboard',
            '💬 AI Assistant': 'Chat',
            '➕ Add Transaction': 'Add Transaction',
            '📝 Transaction History': 'History',
            '🤖 AI Insights': 'Insights',
            '💳 Budgets': 'Budgets',
            '⚙️ Settings': 'Settings'
        }
        
        for label, page in pages.items():
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.selected_page = page
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        summary = db.get_summary(user_id=st.session_state.user_id, start_date=date.today().replace(day=1))
        st.markdown(f"""
        <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 12px;">
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">This Month</p>
            <p style="color: #10B981; font-size: 1.2rem; font-weight: 600; margin: 0.25rem 0;">
                ↑ {format_currency(summary['income'])}
            </p>
            <p style="color: #EF4444; font-size: 1.2rem; font-weight: 600; margin: 0.25rem 0;">
                ↓ {format_currency(summary['expense'])}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Connect with me
        st.markdown("### 🔗 Connect with me")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/madhankumar10102004/)")
        with col2:
            st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/madhan45-mad)")
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_data = None
            st.rerun()
    else:
        st.markdown("Please login to access your finance tracker.")
        st.markdown("---")
        # Connect with me even when not logged in
        st.markdown("### 🔗 Connect with me")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/madhankumar10102004/)")
        with col2:
            st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/madhan45-mad)")


# ==================== Dashboard Page ====================
def render_dashboard():
    """Render the main dashboard."""
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>💰 {get_greeting()}!</h1>
        <p>Here's your financial overview for {datetime.now().strftime('%B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get data
    current_month_start = date.today().replace(day=1)
    summary = db.get_summary(user_id=st.session_state.user_id, start_date=current_month_start)
    insights = predictor.get_spending_insights(user_id=st.session_state.user_id)
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        expense_change = insights['changes']['expense_change']
        change_class = 'negative' if expense_change > 0 else 'positive'
        change_icon = '↑' if expense_change > 0 else '↓'
        st.markdown(f"""
        <div class="metric-card">
            <h3>💸 Total Expenses</h3>
            <div class="value">{format_currency(summary['expense'])}</div>
            <div class="change {change_class}">{change_icon} {abs(expense_change):.1f}% from last month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        income_change = insights['changes']['income_change']
        change_class = 'positive' if income_change > 0 else 'negative'
        change_icon = '↑' if income_change > 0 else '↓'
        st.markdown(f"""
        <div class="metric-card">
            <h3>💵 Total Income</h3>
            <div class="value">{format_currency(summary['income'])}</div>
            <div class="change {change_class}">{change_icon} {abs(income_change):.1f}% from last month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        balance = summary['balance']
        balance_class = 'positive' if balance >= 0 else 'negative'
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Balance</h3>
            <div class="value" style="color: {'#10B981' if balance >= 0 else '#EF4444'}">
                {format_currency(balance)}
            </div>
            <div class="change">{days_remaining_in_month()} days left this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        daily_avg = insights['daily_average']
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅 Daily Average</h3>
            <div class="value">{format_currency(daily_avg)}</div>
            <div class="change">Based on this month's spending</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Expense Breakdown")
        breakdown = db.get_category_breakdown(user_id=st.session_state.user_id, start_date=current_month_start)
        
        if breakdown:
            fig = px.pie(
                values=[c['total'] for c in breakdown],
                names=[f"{c['icon']} {c['name']}" for c in breakdown],
                color_discrete_sequence=generate_color_palette(len(breakdown)),
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                ),
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <p>No expenses recorded this month.<br>Add transactions to see your breakdown!</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📈 Monthly Trends")
        trends = db.get_monthly_trends(user_id=st.session_state.user_id, months=6)
        
        if not trends.empty:
            fig = go.Figure()
            
            if 'expense' in trends.columns:
                fig.add_trace(go.Scatter(
                    x=trends['month'],
                    y=trends['expense'],
                    name='Expenses',
                    line=dict(color='#EF4444', width=3),
                    mode='lines+markers',
                    marker=dict(size=8)
                ))
            
            if 'income' in trends.columns:
                fig.add_trace(go.Scatter(
                    x=trends['month'],
                    y=trends['income'],
                    name='Income',
                    line=dict(color='#10B981', width=3),
                    mode='lines+markers',
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(
                    showgrid=False,
                    title='',
                    tickfont=dict(color='#94a3b8')
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    title='',
                    tickfont=dict(color='#94a3b8')
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📈</div>
                <p>Not enough data to show trends.<br>Keep tracking to see your patterns!</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Recent transactions and alerts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Recent Transactions")
        recent = db.get_transactions(user_id=st.session_state.user_id, limit=5)
        
        if recent:
            for t in recent:
                amount_class = 'amount-expense' if t['transaction_type'] == 'expense' else 'amount-income'
                amount_prefix = '-' if t['transaction_type'] == 'expense' else '+'
                st.markdown(f"""
                <div class="transaction-item">
                    <span class="transaction-icon">{t.get('category_icon', '📦')}</span>
                    <div class="transaction-details">
                        <div class="transaction-description">{t.get('description', 'No description')}</div>
                        <div class="transaction-category">{t.get('category_name', 'Uncategorized')} • {format_date_friendly(t['date'])}</div>
                    </div>
                    <div class="transaction-amount {amount_class}">
                        {amount_prefix}{format_currency(t['amount'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No transactions yet. Start by adding your first expense!</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⚠️ Alerts")
        alerts = predictor.detect_overspending(user_id=st.session_state.user_id)
        
        if alerts:
            for alert in alerts[:3]:
                severity_class = f"alert-{alert['severity']}"
                st.markdown(f"""
                <div class="alert-card {severity_class}">
                    <span style="font-size: 1.5rem;">{alert['icon']}</span>
                    <div>
                        <strong>{alert['category']}</strong><br>
                        <span style="font-size: 0.85rem; color: #94a3b8;">{alert['message']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #10B981;">
                <span style="font-size: 2rem;">✅</span><br>
                <p style="margin-top: 0.5rem;">All good! No spending alerts.</p>
            </div>
            """, unsafe_allow_html=True)


# ==================== Add Transaction Page ====================
def render_add_transaction():
    """Render the add transaction form."""
    st.markdown("""
    <div class="main-header">
        <h1>➕ Add Transaction</h1>
        <p>Record a new income or expense</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("add_transaction_form", clear_on_submit=True):
            # Transaction type
            transaction_type = st.radio(
                "Transaction Type",
                options=['expense', 'income'],
                format_func=lambda x: '💸 Expense' if x == 'expense' else '💵 Income',
                horizontal=True
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    step=100.0,
                    format="%.2f"
                )
            
            with col_b:
                transaction_date = st.date_input(
                    "Date",
                    value=date.today(),
                    max_value=date.today()
                )
            
            description = st.text_input(
                "Description",
                placeholder="e.g., Lunch at restaurant, Monthly salary, etc."
            )
            
            # AI-powered category suggestion
            suggested_category = None
            if description:
                predicted, confidence = categorizer.predict(description)
                if confidence > 0.3:
                    suggested_category = predicted
                    st.info(f"🤖 AI suggests: **{predicted}** (Confidence: {confidence:.0%})")
            
            # Category selection
            categories = db.get_categories(user_id=st.session_state.user_id, category_type=transaction_type)
            category_options = {f"{c['icon']} {c['name']}": c['id'] for c in categories}
            
            # Pre-select suggested category if available
            default_index = 0
            if suggested_category:
                for i, (label, _) in enumerate(category_options.items()):
                    if suggested_category in label:
                        default_index = i
                        break
            
            selected_category = st.selectbox(
                "Category",
                options=list(category_options.keys()),
                index=default_index
            )
            
            submitted = st.form_submit_button("💾 Add Transaction", use_container_width=True)
            
            if submitted:
                if amount > 0 and description:
                    category_id = category_options[selected_category]
                    
                    db.add_transaction(
                        amount=amount,
                        description=description,
                        category_id=category_id,
                        transaction_type=transaction_type,
                        transaction_date=transaction_date,
                        user_id=st.session_state.user_id
                    )
                    
                    st.success("✅ Transaction added successfully!")
                    st.balloons()
                else:
                    st.error("Please fill in all required fields!")
    
    with col2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        <div class="recommendation-card">
            <div class="recommendation-title">🤖 AI Auto-Categorization</div>
            <div class="recommendation-text">
                Type a description and our AI will suggest the best category for your transaction.
            </div>
        </div>
        
        <div class="recommendation-card">
            <div class="recommendation-title">📝 Good Descriptions</div>
            <div class="recommendation-text">
                Be specific! "Coffee at Starbucks" is better than just "Coffee" for tracking.
            </div>
        </div>
        
        <div class="recommendation-card">
            <div class="recommendation-title">📅 Backdate Transactions</div>
            <div class="recommendation-text">
                Forgot to log something? You can select past dates when adding transactions.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==================== Transaction History Page ====================
def render_history():
    """Render transaction history."""
    st.markdown("""
    <div class="main-header">
        <h1>📝 Transaction History</h1>
        <p>View and manage all your transactions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        period = st.selectbox(
            "Period",
            options=['This Month', 'Last Month', 'Last 30 Days', 'Last 90 Days', 'This Year', 'All Time'],
            index=0
        )
    
    with col2:
        type_filter = st.selectbox(
            "Type",
            options=['All', 'Expenses', 'Income'],
            index=0
        )
    
    with col3:
        categories = db.get_categories(user_id=st.session_state.user_id)
        category_options = {'All Categories': None}
        category_options.update({f"{c['icon']} {c['name']}": c['id'] for c in categories})
        category_filter = st.selectbox(
            "Category",
            options=list(category_options.keys()),
            index=0
        )
    
    with col4:
        search = st.text_input("Search", placeholder="Search description...")
    
    # Get date range
    period_map = {
        'This Month': 'this_month',
        'Last Month': 'last_month',
        'Last 30 Days': 'last_30_days',
        'Last 90 Days': 'last_90_days',
        'This Year': 'this_year',
        'All Time': 'all_time'
    }
    start_date, end_date = get_date_range(period_map.get(period, 'this_month'))
    
    # Type filter
    trans_type = None
    if type_filter == 'Expenses':
        trans_type = 'expense'
    elif type_filter == 'Income':
        trans_type = 'income'
    
    # Category filter
    cat_id = category_options[category_filter]
    
    # Get transactions
    transactions = db.get_transactions(
        user_id=st.session_state.user_id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=trans_type,
        category_id=cat_id
    )
    
    # Filter by search
    if search:
        transactions = [t for t in transactions if search.lower() in t.get('description', '').lower()]
    
    # Display summary
    total_expense = sum(t['amount'] for t in transactions if t['transaction_type'] == 'expense')
    total_income = sum(t['amount'] for t in transactions if t['transaction_type'] == 'income')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", len(transactions))
    col2.metric("Total Expenses", format_currency(total_expense))
    col3.metric("Total Income", format_currency(total_income))
    
    st.markdown("---")
    
    if transactions:
        # Export option
        if st.button("📥 Export to CSV"):
            df = pd.DataFrame(transactions)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Display transactions
        for t in transactions:
            col1, col2, col3, col4 = st.columns([0.5, 3, 1.5, 1])
            
            with col1:
                st.markdown(f"<span style='font-size: 1.5rem;'>{t.get('category_icon', '📦')}</span>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{t.get('description', 'No description')}**")
                st.caption(f"{t.get('category_name', 'Uncategorized')} • {format_date_friendly(t['date'])}")
            
            with col3:
                color = '#EF4444' if t['transaction_type'] == 'expense' else '#10B981'
                prefix = '-' if t['transaction_type'] == 'expense' else '+'
                st.markdown(f"<span style='color: {color}; font-weight: 600; font-size: 1.1rem;'>{prefix}{format_currency(t['amount'])}</span>", unsafe_allow_html=True)
            
            with col4:
                if st.button("🗑️", key=f"del_{t['id']}", help="Delete transaction"):
                    db.delete_transaction(t['id'], user_id=st.session_state.user_id)
                    st.rerun()
            
            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <p>No transactions found matching your filters.</p>
        </div>
        """, unsafe_allow_html=True)


# ==================== AI Insights Page ====================
def render_insights():
    """Render AI-powered insights."""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Insights</h1>
        <p>Smart analysis and recommendations for your finances</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Predictions
    st.markdown("### 🔮 Next Month Prediction")
    predictions = predictor.predict_next_month_expenses(user_id=st.session_state.user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Predicted Expenses</h3>
            <div class="value" style="color: #EF4444;">{format_currency(predictions['predicted_expense'])}</div>
            <div class="change">Confidence: {predictions['confidence'].upper()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Predicted Income</h3>
            <div class="value" style="color: #10B981;">{format_currency(predictions['predicted_income'])}</div>
            <div class="change">Based on {6} months history</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        savings = predictions.get('predicted_savings', predictions.get('predicted_income', 0) - predictions.get('predicted_expense', 0))
        st.markdown(f"""
        <div class="metric-card">
            <h3>Predicted Savings</h3>
            <div class="value" style="color: {'#10B981' if savings >= 0 else '#EF4444'};">
                {format_currency(savings)}
            </div>
            <div class="change">{'On track!' if savings >= 0 else 'Consider reducing expenses'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.info(predictions['message'])
    
    st.markdown("---")
    
    # Recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💡 Smart Recommendations")
        recommendations = predictor.get_recommendations(user_id=st.session_state.user_id)
        
        if recommendations:
            for rec in recommendations:
                priority_color = {
                    'high': '#EF4444',
                    'medium': '#F59E0B',
                    'low': '#10B981'
                }.get(rec['priority'], '#94a3b8')
                
                st.markdown(f"""
                <div class="recommendation-card">
                    <div class="recommendation-title">
                        <span style="color: {priority_color};">●</span> {rec['icon']} {rec['title']}
                    </div>
                    <div class="recommendation-text">{rec['description']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Add more transactions to get personalized recommendations!")
    
    with col2:
        st.markdown("### ⚠️ Spending Alerts")
        alerts = predictor.detect_overspending(user_id=st.session_state.user_id)
        
        if alerts:
            for alert in alerts:
                severity_class = f"alert-{alert['severity']}"
                st.markdown(f"""
                <div class="alert-card {severity_class}">
                    <span style="font-size: 1.5rem;">{alert['icon']}</span>
                    <div>
                        <strong>{alert['category']}</strong><br>
                        <span style="font-size: 0.85rem; color: #94a3b8;">{alert['message']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("🎉 Great job! No spending issues detected.")
    
    st.markdown("---")
    
    # Spending patterns
    st.markdown("### 📊 Spending Pattern Analysis")
    
    insights = predictor.get_spending_insights(user_id=st.session_state.user_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if insights['biggest_expense_category']:
            cat = insights['biggest_expense_category']
            st.markdown(f"""
            <div class="metric-card">
                <h3>{cat['icon']} Top Spending Category</h3>
                <div class="value">{cat['name']}</div>
                <div class="change">{format_currency(cat['total'])} this month ({cat['count']} transactions)</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if insights['most_frequent_category']:
            cat = insights['most_frequent_category']
            st.markdown(f"""
            <div class="metric-card">
                <h3>{cat['icon']} Most Frequent Category</h3>
                <div class="value">{cat['name']}</div>
                <div class="change">{cat['count']} transactions this month</div>
            </div>
            """, unsafe_allow_html=True)


# ==================== Budgets Page ====================
def render_budgets():
    """Render budget management page."""
    st.markdown("""
    <div class="main-header">
        <h1>💳 Budget Management</h1>
        <p>Set and track spending limits for each category</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add new budget
    st.markdown("### ➕ Set Budget Limit")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    expense_categories = db.get_categories(user_id=st.session_state.user_id, category_type='expense')
    category_options = {f"{c['icon']} {c['name']}": c['id'] for c in expense_categories}
    
    with col1:
        selected_category = st.selectbox(
            "Category",
            options=list(category_options.keys())
        )
    
    with col2:
        budget_amount = st.number_input(
            "Monthly Limit (₹)",
            min_value=100.0,
            step=500.0,
            value=5000.0
        )
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Set Budget", use_container_width=True):
            category_id = category_options[selected_category]
            db.set_budget(category_id, st.session_state.user_id, budget_amount)
            st.success("Budget set successfully!")
            st.rerun()
    
    st.markdown("---")
    
    # Budget status
    st.markdown("### 📊 Current Budget Status")
    
    budget_status = db.get_budget_status(user_id=st.session_state.user_id)
    
    if budget_status:
        for item in budget_status:
            percentage = min(item['percentage'], 100)
            remaining = item['remaining']
            
            # Determine color based on percentage
            if percentage >= 100:
                bar_color = '#EF4444'
                status_text = '⚠️ Over budget!'
            elif percentage >= 80:
                bar_color = '#F59E0B'
                status_text = '⚡ Approaching limit'
            else:
                bar_color = '#10B981'
                status_text = '✅ On track'
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.1rem;">
                        <strong>{item['icon']} {item['name']}</strong>
                    </span>
                    <span style="color: #94a3b8;">{status_text}</span>
                </div>
                <div class="budget-progress">
                    <div class="budget-progress-fill" style="width: {percentage}%; background: {bar_color};"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; color: #94a3b8; font-size: 0.85rem;">
                    <span>Spent: {format_currency(item['spent'])}</span>
                    <span>Limit: {format_currency(item['monthly_limit'])}</span>
                    <span style="color: {'#10B981' if remaining >= 0 else '#EF4444'};">
                        {'Remaining: ' + format_currency(remaining) if remaining >= 0 else 'Over by: ' + format_currency(abs(remaining))}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💳</div>
            <p>No budgets set yet. Set budget limits above to start tracking!</p>
        </div>
        """, unsafe_allow_html=True)


# ==================== Settings Page ====================
def render_settings():
    """Render settings page."""
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings</h1>
        <p>Manage your expense tracker preferences</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Categories management
    st.markdown("### 📁 Manage Categories")
    
    tab1, tab2 = st.tabs(["Expense Categories", "Income Categories"])
    
    with tab1:
        expense_cats = db.get_categories(user_id=st.session_state.user_id, category_type='expense')
        
        for cat in expense_cats:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{cat['icon']} **{cat['name']}**")
            with col2:
                st.markdown(f"<span style='color: {cat['color']};'>●</span>", unsafe_allow_html=True)
        
        # Add new category
        st.markdown("---")
        st.markdown("**Add New Expense Category**")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_cat_name = st.text_input("Category Name", key="new_expense_cat")
        with col2:
            new_cat_icon = st.text_input("Icon", value="📦", key="new_expense_icon")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add Category", key="add_expense_cat"):
                if new_cat_name:
                    db.add_category(new_cat_name, 'expense', st.session_state.user_id, new_cat_icon)
                    st.success("Category added!")
                    st.rerun()
    
    with tab2:
        income_cats = db.get_categories(user_id=st.session_state.user_id, category_type='income')
        
        for cat in income_cats:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{cat['icon']} **{cat['name']}**")
            with col2:
                st.markdown(f"<span style='color: {cat['color']};'>●</span>", unsafe_allow_html=True)
        
        # Add new category
        st.markdown("---")
        st.markdown("**Add New Income Category**")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_cat_name = st.text_input("Category Name", key="new_income_cat")
        with col2:
            new_cat_icon = st.text_input("Icon", value="💰", key="new_income_icon")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add Category", key="add_income_cat"):
                if new_cat_name:
                    db.add_category(new_cat_name, 'income', st.session_state.user_id, new_cat_icon)
                    st.success("Category added!")
                    st.rerun()
    
    st.markdown("---")
    
    # Data management
    st.markdown("### 🗃️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="recommendation-card">
            <div class="recommendation-title">📥 Export Data</div>
            <div class="recommendation-text">Download all your transactions as a CSV file for backup or analysis.</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Export All Data", use_container_width=True):
            df = db.get_transactions_dataframe(user_id=st.session_state.user_id)
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"expense_tracker_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export!")
    
    with col2:
        st.markdown("""
        <div class="recommendation-card" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2);">
            <div class="recommendation-title" style="color: #EF4444;">⚠️ Clear All Data</div>
            <div class="recommendation-text">Permanently delete all transactions and budgets. This cannot be undone!</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
            st.warning("⚠️ Are you sure? This will delete all your transaction data!")
            if st.button("Yes, Delete Everything", type="primary"):
                db.clear_all_data(user_id=st.session_state.user_id)
                st.success("All data cleared!")
                st.rerun()
    
    st.markdown("---")
    
    # Gemini AI Configuration
    st.markdown("### 🤖 Gemini AI Configuration")
    api_key = db.get_setting('gemini_api_key', user_id=st.session_state.user_id, default='')
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_api_key = st.text_input(
            "Gemini API Key",
            value=api_key,
            type="password",
            help="Enter your Google Gemini API key to enable advanced AI assistant features."
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save API Key", use_container_width=True):
            db.set_setting('gemini_api_key', new_api_key, user_id=st.session_state.user_id)
            st.success("API Key saved!")
            st.rerun()
            
    if not api_key:
        st.warning("⚠️ No API key found. Assistant will use basic regex-based matching.")
    else:
        st.success("✅ Gemini AI is active.")

    st.markdown("---")
    
    # About
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div class="recommendation-card">
        <div class="recommendation-title">💰 AI-Based Smart Expense Tracker</div>
        <div class="recommendation-text">
            An intelligent expense tracking application powered by Machine Learning for automatic 
            expense categorization, spending predictions, and personalized financial recommendations.
            <br><br>
            <strong>Features:</strong>
            <ul>
                <li>🤖 AI-powered expense categorization</li>
                <li>📊 Interactive dashboards and charts</li>
                <li>🔮 Spending predictions and trend analysis</li>
                <li>💡 Personalized financial recommendations</li>
                <li>💳 Budget tracking and alerts</li>
            </ul>
            <br>
            Built with Python, Streamlit, Scikit-learn, and Plotly.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== AI Chat Assistant Page ====================
def render_chat():
    """Render the AI chat assistant page."""
    st.markdown("""
    <div class="main-header">
        <h1>💬 AI Assistant</h1>
        <p>Chat with me to manage your expenses naturally!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick insights bar
    insights = assistant.get_quick_insights(user_id=st.session_state.user_id)
    st.info(f"📊 **Quick Insight:** {insights}")
    
    # Initialize chat with welcome message if empty
    if not st.session_state.chat_messages:
        welcome = assistant.process_message("hi", user_id=st.session_state.user_id)
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': welcome['response']
        })
    
    # Display chat messages using Streamlit's native chat components
    for msg in st.session_state.chat_messages:
        if msg['role'] == 'user':
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg['content'])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg['content'])
    
    # Chat input using Streamlit's chat_input
    user_input = st.chat_input("Type a message... (e.g., 'Spent ₹500 on groceries')")
    
    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input
        })
        
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        
        # Get AI response
        response = assistant.process_message(user_input, user_id=st.session_state.user_id)
        
        # Add assistant response
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': response['response']
        })
        
        # Display assistant response
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response['response'])
        
        st.rerun()
    
    st.markdown("---")
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💰 Check Balance", use_container_width=True):
            st.session_state.chat_messages.append({'role': 'user', 'content': 'What is my balance?'})
            response = assistant.process_message('what is my balance', user_id=st.session_state.user_id)
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response['response']})
            st.rerun()
    
    with col2:
        if st.button("📊 View Spending", use_container_width=True):
            st.session_state.chat_messages.append({'role': 'user', 'content': 'Show my spending'})
            response = assistant.process_message('show my spending', user_id=st.session_state.user_id)
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response['response']})
            st.rerun()
    
    with col3:
        if st.button("📋 Recent Transactions", use_container_width=True):
            st.session_state.chat_messages.append({'role': 'user', 'content': 'Show recent transactions'})
            response = assistant.process_message('show recent transactions', user_id=st.session_state.user_id)
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response['response']})
            st.rerun()
    
    with col4:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    
    # Example prompts
    st.markdown("### 💡 Try saying...")
    col1, col2, col3, col4 = st.columns(4)
    
    examples = [
        ("Spent ₹500 on groceries", col1),
        ("Paid 200 for coffee", col2),
        ("Received salary of ₹50000", col3),
        ("Set budget of ₹10000 for food", col4)
    ]
    
    for i, (example, col) in enumerate(examples):
        with col:
            if st.button(f"'{example}'", key=f"example_{i}", use_container_width=True):
                st.session_state.chat_messages.append({'role': 'user', 'content': example})
                response = assistant.process_message(example, user_id=st.session_state.user_id)
                st.session_state.chat_messages.append({'role': 'assistant', 'content': response['response']})
                st.rerun()


# ==================== Main Router ====================
def main():
    """Main application router."""
    # Check login status
    if not st.session_state.logged_in:
        render_auth()
        return

    page = st.session_state.selected_page
    
    if page == 'Dashboard':
        render_dashboard()
    elif page == 'Chat':
        render_chat()
    elif page == 'Add Transaction':
        render_add_transaction()
    elif page == 'History':
        render_history()
    elif page == 'Insights':
        render_insights()
    elif page == 'Budgets':
        render_budgets()
    elif page == 'Settings':
        render_settings()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
