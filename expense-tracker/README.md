# 💰 AI Expense Tracker

A smart personal finance manager built with Python and Streamlit, featuring AI-powered categorization and a conversational assistant.

## ✨ Features

- **📊 Interactive Dashboard**: Real-time overview of your finances with Plotly charts.
- **🤖 AI Categorization**: Automatically categorizes transactions based on your descriptions using ML.
- **💬 Conversational Assistant**: Add expenses or check your balance by chatting in natural language.
- **📈 Spending Insights**: Detects overspending and provides personalized financial tips.
- **💳 Budget Management**: Set monthly limits for different categories.
- **📝 Transaction History**: Full history with filters and CSV export.

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure

- `app.py`: Main Streamlit application entry point.
- `ml/`: Machine Learning components (Assistant, Categorizer, Predictor).
- `database/`: SQLite database management logic.
- `utils/`: Helper functions for formatting and calculations.
- `data/`: Local storage for the database and trained ML models.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Data Visualization**: Plotly
- **Machine Learning**: Scikit-learn
- **Database**: SQLite
