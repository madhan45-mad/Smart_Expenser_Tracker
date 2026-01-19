"""
ML-based Expense Categorizer
Uses text classification to automatically categorize transactions
"""

import re
from typing import Optional, Tuple, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import os


class ExpenseCategorizer:
    """
    Machine Learning model for automatic expense categorization
    based on transaction descriptions.
    """
    
    # Pre-defined training data for expense categories
    TRAINING_DATA = {
        'Food & Dining': [
            'restaurant', 'pizza', 'burger', 'coffee', 'cafe', 'lunch', 'dinner',
            'breakfast', 'groceries', 'supermarket', 'food', 'meal', 'snack',
            'bakery', 'swiggy', 'zomato', 'ubereats', 'doordash', 'mcdonalds',
            'starbucks', 'dominos', 'kfc', 'subway', 'tea', 'juice', 'ice cream',
            'food delivery', 'takeout', 'dine', 'eating out', 'fast food'
        ],
        'Transport': [
            'uber', 'lyft', 'ola', 'taxi', 'cab', 'bus', 'train', 'metro',
            'fuel', 'petrol', 'gas', 'diesel', 'parking', 'toll', 'car',
            'bike', 'motorcycle', 'airline', 'flight', 'airport', 'travel',
            'commute', 'ride', 'transport', 'auto', 'rickshaw', 'fare'
        ],
        'Entertainment': [
            'movie', 'cinema', 'netflix', 'spotify', 'amazon prime', 'disney',
            'hulu', 'youtube', 'gaming', 'games', 'concert', 'show', 'party',
            'club', 'bar', 'pub', 'theatre', 'music', 'books', 'magazine',
            'subscription', 'streaming', 'fun', 'leisure', 'hobby'
        ],
        'Utilities': [
            'electricity', 'electric bill', 'water bill', 'gas bill', 'internet',
            'wifi', 'broadband', 'phone bill', 'mobile recharge', 'cable',
            'utility', 'rent', 'housing', 'maintenance', 'repair', 'plumber',
            'electrician', 'home', 'apartment', 'heating', 'cooling'
        ],
        'Shopping': [
            'amazon', 'flipkart', 'walmart', 'target', 'mall', 'clothes',
            'shoes', 'electronics', 'gadget', 'phone', 'laptop', 'furniture',
            'home decor', 'appliance', 'gift', 'present', 'shopping', 'store',
            'retail', 'online shopping', 'fashion', 'accessories', 'jewelry'
        ],
        'Healthcare': [
            'hospital', 'doctor', 'clinic', 'medicine', 'pharmacy', 'medical',
            'health', 'dental', 'dentist', 'eye', 'optician', 'glasses',
            'prescription', 'therapy', 'gym', 'fitness', 'workout', 'yoga',
            'insurance', 'health insurance', 'checkup', 'lab', 'test'
        ],
        'Education': [
            'school', 'college', 'university', 'course', 'tuition', 'books',
            'textbook', 'udemy', 'coursera', 'learning', 'training', 'workshop',
            'seminar', 'certification', 'exam', 'study', 'education', 'class',
            'tutorial', 'online course', 'degree', 'diploma'
        ],
        'Savings': [
            'savings', 'investment', 'mutual fund', 'stock', 'fixed deposit',
            'fd', 'rd', 'recurring deposit', 'retirement', 'pension', 'emi',
            'loan payment', 'sip', 'bonds', 'gold', 'crypto', 'bitcoin'
        ],
        'Salary': [
            'salary', 'paycheck', 'wages', 'income', 'pay', 'compensation',
            'bonus', 'commission', 'earnings'
        ],
        'Freelance': [
            'freelance', 'consulting', 'contract', 'project payment', 'gig',
            'side hustle', 'client payment', 'invoice', 'hourly'
        ],
        'Investment': [
            'dividend', 'interest', 'returns', 'capital gains', 'profit',
            'investment income', 'rental income', 'passive income'
        ],
        'Gift': [
            'gift', 'present', 'birthday money', 'cash gift', 'received',
            'wedding gift', 'bonus gift'
        ]
    }
    
    def __init__(self, model_path: str = None):
        """Initialize the categorizer with optional pre-trained model."""
        if model_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            model_path = os.path.join(data_dir, 'categorizer_model.pkl')
        
        self.model_path = model_path
        self.model = None
        self.categories = list(self.TRAINING_DATA.keys())
        
        # Try to load existing model or train new one
        if os.path.exists(model_path):
            self._load_model()
        else:
            self._train_model()
    
    def _prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """Prepare training data from predefined examples."""
        texts = []
        labels = []
        
        for category, keywords in self.TRAINING_DATA.items():
            for keyword in keywords:
                # Add variations
                texts.extend([
                    keyword,
                    keyword.upper(),
                    keyword.capitalize(),
                    f"paid for {keyword}",
                    f"{keyword} payment",
                    f"{keyword} expense",
                ])
                labels.extend([category] * 6)
        
        return texts, labels
    
    def _train_model(self):
        """Train the categorization model."""
        texts, labels = self._prepare_training_data()
        
        # Create pipeline with TF-IDF and Naive Bayes
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_features=5000,
                stop_words='english'
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        self.model.fit(texts, labels)
        self._save_model()
    
    def _save_model(self):
        """Save the trained model to disk."""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def _load_model(self):
        """Load a pre-trained model from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        except Exception:
            self._train_model()
    
    def predict(self, description: str) -> Tuple[str, float]:
        """
        Predict the category for a transaction description.
        
        Returns:
            Tuple of (category_name, confidence_score)
        """
        if not description or not description.strip():
            return 'Other', 0.0
        
        # Clean the description
        cleaned = self._clean_text(description)
        
        # First, try keyword matching for high confidence
        keyword_match = self._keyword_match(cleaned)
        if keyword_match:
            return keyword_match, 0.95
        
        # Use ML model for prediction
        if self.model:
            try:
                prediction = self.model.predict([cleaned])[0]
                probabilities = self.model.predict_proba([cleaned])[0]
                confidence = max(probabilities)
                
                return prediction, confidence
            except Exception:
                pass
        
        return 'Other', 0.0
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _keyword_match(self, text: str) -> Optional[str]:
        """Try to match based on keywords for high-confidence predictions."""
        text_lower = text.lower()
        
        for category, keywords in self.TRAINING_DATA.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return None
    
    def get_top_predictions(self, description: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Get top N category predictions with confidence scores.
        
        Returns:
            List of tuples (category_name, confidence_score)
        """
        if not description or not description.strip():
            return [('Other', 0.0)]
        
        cleaned = self._clean_text(description)
        
        if self.model:
            try:
                probabilities = self.model.predict_proba([cleaned])[0]
                classes = self.model.classes_
                
                # Sort by probability
                sorted_indices = np.argsort(probabilities)[::-1][:top_n]
                
                return [(classes[i], probabilities[i]) for i in sorted_indices]
            except Exception:
                pass
        
        return [('Other', 0.0)]
    
    def retrain(self, additional_data: List[Tuple[str, str]] = None):
        """
        Retrain the model, optionally with additional labeled data.
        
        Args:
            additional_data: List of (description, category) tuples
        """
        texts, labels = self._prepare_training_data()
        
        if additional_data:
            for desc, cat in additional_data:
                texts.append(desc)
                labels.append(cat)
        
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_features=5000,
                stop_words='english'
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        self.model.fit(texts, labels)
        self._save_model()
