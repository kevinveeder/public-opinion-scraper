"""Text processing utilities for sentiment analysis."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import string

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """Advanced text analysis utilities."""
    
    def __init__(self):
        self._setup_patterns()
    
    def _setup_patterns(self) -> None:
        """Setup regex patterns for text analysis."""
        # Negation patterns
        self.negation_pattern = re.compile(
            r'\b(?:not|no|never|none|nobody|nothing|neither|nowhere|isn\'t|aren\'t|wasn\'t|weren\'t|haven\'t|hasn\'t|hadn\'t|won\'t|wouldn\'t|don\'t|doesn\'t|didn\'t|can\'t|couldn\'t|shouldn\'t|mustn\'t|needn\'t|daren\'t|mayn\'t|oughtn\'t)\b',
            re.IGNORECASE
        )
        
        # Intensifier patterns
        self.intensifier_pattern = re.compile(
            r'\b(?:very|really|extremely|incredibly|absolutely|totally|completely|utterly|quite|rather|pretty|fairly|somewhat|slightly|barely|hardly|scarcely)\b',
            re.IGNORECASE
        )
        
        # Question patterns
        self.question_pattern = re.compile(r'\?')
        
        # Exclamation patterns
        self.exclamation_pattern = re.compile(r'!')
        
        # Capital letters pattern (for emphasis detection)
        self.caps_pattern = re.compile(r'\b[A-Z]{2,}\b')
        
        # Repeated characters (e.g., "sooooo")
        self.repeated_chars_pattern = re.compile(r'(.)\1{2,}')
    
    def analyze_negation_context(self, text: str) -> Dict[str, Any]:
        """Analyze negation patterns in text."""
        negations = self.negation_pattern.findall(text.lower())
        
        # Split text into sentences for context analysis
        sentences = re.split(r'[.!?]+', text)
        negated_sentences = []
        
        for sentence in sentences:
            if self.negation_pattern.search(sentence.lower()):
                negated_sentences.append(sentence.strip())
        
        return {
            'has_negation': len(negations) > 0,
            'negation_count': len(negations),
            'negations': negations,
            'negated_sentences': negated_sentences,
            'negation_ratio': len(negations) / max(len(text.split()), 1)
        }
    
    def analyze_intensifiers(self, text: str) -> Dict[str, Any]:
        """Analyze intensifier patterns in text."""
        intensifiers = self.intensifier_pattern.findall(text.lower())
        
        return {
            'has_intensifiers': len(intensifiers) > 0,
            'intensifier_count': len(intensifiers),
            'intensifiers': intensifiers,
            'intensifier_ratio': len(intensifiers) / max(len(text.split()), 1)
        }
    
    def analyze_emphasis(self, text: str) -> Dict[str, Any]:
        """Analyze emphasis patterns (caps, repetition, punctuation)."""
        # Analyze capital letters
        caps_words = self.caps_pattern.findall(text)
        
        # Analyze repeated characters
        repeated_chars = self.repeated_chars_pattern.findall(text)
        
        # Analyze punctuation
        exclamations = len(self.exclamation_pattern.findall(text))
        questions = len(self.question_pattern.findall(text))
        
        # Calculate emphasis score
        emphasis_score = (
            len(caps_words) * 0.3 +
            len(repeated_chars) * 0.2 +
            exclamations * 0.3 +
            questions * 0.2
        ) / max(len(text.split()), 1)
        
        return {
            'caps_words': caps_words,
            'caps_count': len(caps_words),
            'repeated_chars': repeated_chars,
            'repeated_chars_count': len(repeated_chars),
            'exclamation_count': exclamations,
            'question_count': questions,
            'emphasis_score': emphasis_score
        }
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """Extract keywords from text."""
        # Simple keyword extraction using word frequency
        # Remove punctuation and convert to lowercase
        text_clean = text.lower().translate(str.maketrans('', '', string.punctuation))
        words = text_clean.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'this', 'that', 'these', 'those', 'will', 'would', 'could', 'should', 'can', 'may', 'might'
        }
        
        # Filter words
        filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        return word_counts.most_common(top_n)
    
    def analyze_text_complexity(self, text: str) -> Dict[str, Any]:
        """Analyze text complexity metrics."""
        if not text:
            return {}
        
        # Basic metrics
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Average metrics
        avg_word_length = sum(len(word) for word in text.split()) / max(word_count, 1)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Vocabulary richness (unique words / total words)
        unique_words = len(set(text.lower().split()))
        vocabulary_richness = unique_words / max(word_count, 1)
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'unique_words': unique_words,
            'vocabulary_richness': vocabulary_richness
        }
    
    def detect_language_patterns(self, text: str) -> Dict[str, Any]:
        """Detect language-specific patterns."""
        # Simple heuristics for English text patterns
        
        # Detect informal language
        informal_patterns = [
            r'\b(?:lol|omg|wtf|btw|fyi|imho|imo|afaik|ttyl|brb|thx|ur|u)\b',
            r'\b(?:gonna|wanna|gotta|kinda|sorta|dunno|yeah|yep|nope)\b'
        ]
        
        informal_matches = []
        for pattern in informal_patterns:
            matches = re.findall(pattern, text.lower())
            informal_matches.extend(matches)
        
        # Detect slang/colloquial expressions
        slang_pattern = re.compile(r'\b(?:awesome|cool|sick|dope|lit|fire|dank|savage|salty|salty|lowkey|highkey|periodt|no cap|facts|bet|vibe|mood)\b', re.IGNORECASE)
        slang_matches = slang_pattern.findall(text)
        
        return {
            'informal_language': len(informal_matches) > 0,
            'informal_count': len(informal_matches),
            'informal_words': informal_matches,
            'slang_language': len(slang_matches) > 0,
            'slang_count': len(slang_matches),
            'slang_words': slang_matches,
            'formality_score': 1.0 - (len(informal_matches) + len(slang_matches)) / max(len(text.split()), 1)
        }
    
    def comprehensive_analysis(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive text analysis."""
        if not text:
            return {}
        
        analysis = {
            'original_text': text,
            'text_length': len(text),
            'complexity': self.analyze_text_complexity(text),
            'negation': self.analyze_negation_context(text),
            'intensifiers': self.analyze_intensifiers(text),
            'emphasis': self.analyze_emphasis(text),
            'language_patterns': self.detect_language_patterns(text),
            'keywords': self.extract_keywords(text)
        }
        
        # Calculate overall text characteristics
        analysis['characteristics'] = {
            'is_negative_context': analysis['negation']['has_negation'],
            'is_emphatic': analysis['emphasis']['emphasis_score'] > 0.1,
            'is_informal': analysis['language_patterns']['informal_language'],
            'complexity_level': self._categorize_complexity(analysis['complexity']['avg_sentence_length']),
            'emotion_intensity': self._calculate_emotion_intensity(analysis)
        }
        
        return analysis
    
    def _categorize_complexity(self, avg_sentence_length: float) -> str:
        """Categorize text complexity based on sentence length."""
        if avg_sentence_length < 10:
            return 'simple'
        elif avg_sentence_length < 20:
            return 'moderate'
        else:
            return 'complex'
    
    def _calculate_emotion_intensity(self, analysis: Dict[str, Any]) -> float:
        """Calculate emotional intensity score from text analysis."""
        intensity = 0.0
        
        # Add intensity from emphasis
        intensity += analysis['emphasis']['emphasis_score'] * 0.4
        
        # Add intensity from intensifiers
        intensity += analysis['intensifiers']['intensifier_ratio'] * 0.3
        
        # Add intensity from informal language (can indicate emotional expression)
        intensity += (analysis['language_patterns']['informal_count'] / max(analysis['complexity']['word_count'], 1)) * 0.3
        
        return min(intensity, 1.0)


def adjust_sentiment_for_context(sentiment_score: float, text_analysis: Dict[str, Any]) -> float:
    """Adjust sentiment score based on text context analysis."""
    adjusted_score = sentiment_score
    
    # Adjust for negation
    if text_analysis.get('negation', {}).get('has_negation', False):
        negation_ratio = text_analysis['negation']['negation_ratio']
        if negation_ratio > 0.1:  # Significant negation
            adjusted_score *= -0.8  # Flip and reduce magnitude
    
    # Adjust for intensifiers
    if text_analysis.get('intensifiers', {}).get('has_intensifiers', False):
        intensifier_ratio = text_analysis['intensifiers']['intensifier_ratio']
        if intensifier_ratio > 0.05:  # Significant intensification
            adjusted_score *= (1 + intensifier_ratio * 2)  # Amplify sentiment
    
    # Adjust for emphasis
    emphasis_score = text_analysis.get('emphasis', {}).get('emphasis_score', 0)
    if emphasis_score > 0.1:
        adjusted_score *= (1 + emphasis_score * 0.5)  # Amplify based on emphasis
    
    # Ensure score stays within bounds
    return max(-1.0, min(1.0, adjusted_score))


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract simple entities from text (companies, products, etc.)."""
    # Simple pattern-based entity extraction
    # This could be enhanced with NER models
    
    entities = {
        'companies': [],
        'products': [],
        'cryptocurrencies': [],
        'stocks': []
    }
    
    # Company patterns (basic)
    company_patterns = [
        r'\b(?:Apple|Google|Microsoft|Amazon|Facebook|Meta|Tesla|Netflix|Uber|Airbnb|Twitter|LinkedIn|Instagram|YouTube|TikTok|Snapchat|WhatsApp|Zoom|Slack|Discord|Spotify|Adobe|Oracle|IBM|Intel|AMD|NVIDIA|Salesforce)\b'
    ]
    
    # Cryptocurrency patterns
    crypto_patterns = [
        r'\b(?:Bitcoin|BTC|Ethereum|ETH|Dogecoin|DOGE|Litecoin|LTC|Ripple|XRP|Cardano|ADA|Polkadot|DOT|Chainlink|LINK|Binance|BNB|Polygon|MATIC)\b'
    ]
    
    # Stock ticker patterns
    stock_patterns = [
        r'\$[A-Z]{1,5}\b',  # Stock tickers like $AAPL, $TSLA
        r'\b[A-Z]{1,5}\.(?:NYSE|NASDAQ)\b'  # Exchange notation
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities['companies'].extend(matches)
    
    for pattern in crypto_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities['cryptocurrencies'].extend(matches)
    
    for pattern in stock_patterns:
        matches = re.findall(pattern, text)
        entities['stocks'].extend(matches)
    
    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities