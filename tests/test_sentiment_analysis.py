"""Test sentiment analysis functionality."""

import pytest
from unittest.mock import Mock, patch

from sentiment_monitor.analysis.sentiment_analyzer import (
    SentimentAnalyzer, VADERAnalyzer, TextPreprocessor
)
from sentiment_monitor.analysis.text_utils import (
    TextAnalyzer, adjust_sentiment_for_context, extract_entities
)


class TestTextPreprocessor:
    """Test text preprocessing functionality."""
    
    def test_preprocess_basic(self):
        """Test basic text preprocessing."""
        preprocessor = TextPreprocessor()
        
        text = "This is a TEST message with URLs https://example.com and @mentions #hashtags"
        processed = preprocessor.preprocess(text)
        
        assert processed.lower() == processed  # Should be lowercase
        assert "https://example.com" not in processed  # URLs removed
        assert len(processed) > 0
    
    def test_preprocess_empty(self):
        """Test preprocessing empty text."""
        preprocessor = TextPreprocessor()
        
        assert preprocessor.preprocess("") == ""
        assert preprocessor.preprocess(None) == ""
    
    def test_preprocess_long_text(self):
        """Test preprocessing very long text."""
        preprocessor = TextPreprocessor()
        
        long_text = "word " * 1000  # Create long text
        processed = preprocessor.preprocess(long_text)
        
        # Should be truncated
        assert len(processed) <= 1003  # max_length + "..."


class TestVADERAnalyzer:
    """Test VADER sentiment analyzer."""
    
    def test_analyze_positive(self):
        """Test analyzing positive text."""
        analyzer = VADERAnalyzer()
        
        result = analyzer.analyze("I love this! It's absolutely amazing and wonderful!")
        
        assert result['model_name'] == 'vader'
        assert result['compound_score'] > 0.5
        assert result['positive_score'] > 0.5
        assert result['confidence'] > 0.5
        assert 'processing_time' in result
    
    def test_analyze_negative(self):
        """Test analyzing negative text."""
        analyzer = VADERAnalyzer()
        
        result = analyzer.analyze("I hate this! It's terrible and awful!")
        
        assert result['compound_score'] < -0.5
        assert result['negative_score'] > 0.5
        assert result['confidence'] > 0.5
    
    def test_analyze_neutral(self):
        """Test analyzing neutral text."""
        analyzer = VADERAnalyzer()
        
        result = analyzer.analyze("This is a neutral statement about something.")
        
        assert -0.2 < result['compound_score'] < 0.2
        assert result['neutral_score'] > 0.5
    
    def test_analyze_empty(self):
        """Test analyzing empty text."""
        analyzer = VADERAnalyzer()
        
        result = analyzer.analyze("")
        
        assert result['compound_score'] == 0
        assert result['neutral_score'] == 1.0


class TestSentimentAnalyzer:
    """Test main sentiment analyzer."""
    
    def test_analyze_text(self, sentiment_analyzer):
        """Test analyzing text with multiple models."""
        results = sentiment_analyzer.analyze_text("This is a great product! I love it!")
        
        assert len(results) > 0
        assert any(r['model_name'] == 'vader' for r in results)
        
        for result in results:
            assert 'compound_score' in result
            assert 'confidence' in result
            assert 'processing_time' in result
    
    def test_analyze_empty_text(self, sentiment_analyzer):
        """Test analyzing empty text."""
        results = sentiment_analyzer.analyze_text("")
        assert len(results) == 0
        
        results = sentiment_analyzer.analyze_text(None)
        assert len(results) == 0
    
    def test_get_weighted_sentiment(self, sentiment_analyzer):
        """Test weighted sentiment calculation."""
        # Mock results from multiple models
        results = [
            {
                'model_name': 'vader',
                'compound_score': 0.8,
                'positive_score': 0.9,
                'negative_score': 0.1,
                'neutral_score': 0.0,
                'confidence': 0.9
            },
            {
                'model_name': 'roberta',
                'compound_score': 0.6,
                'positive_score': 0.8,
                'negative_score': 0.2,
                'neutral_score': 0.0,
                'confidence': 0.8
            }
        ]
        
        weighted = sentiment_analyzer.get_weighted_sentiment(results)
        
        assert weighted is not None
        assert 'compound_score' in weighted
        assert 'confidence' in weighted
        assert weighted['model_count'] == 2
        assert 'models_used' in weighted
    
    def test_get_weighted_sentiment_empty(self, sentiment_analyzer):
        """Test weighted sentiment with empty results."""
        weighted = sentiment_analyzer.get_weighted_sentiment([])
        assert weighted is None
    
    def test_get_sentiment_label(self, sentiment_analyzer):
        """Test sentiment label generation."""
        assert sentiment_analyzer.get_sentiment_label(0.6) == 'positive'
        assert sentiment_analyzer.get_sentiment_label(-0.6) == 'negative'
        assert sentiment_analyzer.get_sentiment_label(0.0) == 'neutral'
        assert sentiment_analyzer.get_sentiment_label(0.03) == 'neutral'  # Within threshold
    
    def test_is_high_confidence(self, sentiment_analyzer):
        """Test confidence threshold checking."""
        assert sentiment_analyzer.is_high_confidence(0.8) is True
        assert sentiment_analyzer.is_high_confidence(0.3) is False
    
    def test_analyze_batch(self, sentiment_analyzer):
        """Test batch analysis."""
        texts = [
            "This is great!",
            "This is terrible!",
            "This is neutral.",
            ""  # Empty text
        ]
        
        results = sentiment_analyzer.analyze_batch(texts)
        
        assert len(results) == 4
        assert results[0] is not None  # Great text
        assert results[1] is not None  # Terrible text
        assert results[2] is not None  # Neutral text
        assert results[3] is None      # Empty text
        
        # Check text indices
        for i, result in enumerate(results):
            if result:
                assert result['text_index'] == i
    
    def test_get_model_info(self, sentiment_analyzer):
        """Test getting model information."""
        info = sentiment_analyzer.get_model_info()
        
        assert 'available_models' in info
        assert 'model_details' in info
        assert 'configuration' in info
        assert 'vader' in info['available_models']


class TestTextAnalyzer:
    """Test advanced text analysis utilities."""
    
    def test_analyze_negation_context(self):
        """Test negation detection."""
        analyzer = TextAnalyzer()
        
        # Text with negation
        result = analyzer.analyze_negation_context("This is not good at all")
        assert result['has_negation'] is True
        assert result['negation_count'] > 0
        assert 'not' in result['negations']
        
        # Text without negation
        result = analyzer.analyze_negation_context("This is very good")
        assert result['has_negation'] is False
        assert result['negation_count'] == 0
    
    def test_analyze_intensifiers(self):
        """Test intensifier detection."""
        analyzer = TextAnalyzer()
        
        # Text with intensifiers
        result = analyzer.analyze_intensifiers("This is very extremely good")
        assert result['has_intensifiers'] is True
        assert result['intensifier_count'] >= 2
        assert 'very' in result['intensifiers']
        assert 'extremely' in result['intensifiers']
        
        # Text without intensifiers
        result = analyzer.analyze_intensifiers("This is good")
        assert result['has_intensifiers'] is False
    
    def test_analyze_emphasis(self):
        """Test emphasis analysis."""
        analyzer = TextAnalyzer()
        
        # Text with emphasis
        result = analyzer.analyze_emphasis("This is AMAZING!!! Really???")
        assert result['caps_count'] > 0
        assert result['exclamation_count'] >= 3
        assert result['question_count'] >= 3
        assert result['emphasis_score'] > 0
        
        # Text without emphasis
        result = analyzer.analyze_emphasis("This is good.")
        assert result['emphasis_score'] == 0
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        analyzer = TextAnalyzer()
        
        text = "Bitcoin and cryptocurrency are trending topics in technology news"
        keywords = analyzer.extract_keywords(text, top_n=5)
        
        assert len(keywords) <= 5
        assert all(isinstance(item, tuple) and len(item) == 2 for item in keywords)
        # Should filter out common stop words
        keyword_words = [word for word, count in keywords]
        assert 'and' not in keyword_words
        assert 'are' not in keyword_words
    
    def test_analyze_text_complexity(self):
        """Test text complexity analysis."""
        analyzer = TextAnalyzer()
        
        # Simple text
        simple_text = "This is simple. Short sentences."
        result = analyzer.analyze_text_complexity(simple_text)
        
        assert 'word_count' in result
        assert 'sentence_count' in result
        assert 'avg_word_length' in result
        assert 'avg_sentence_length' in result
        assert 'vocabulary_richness' in result
        
        # Complex text
        complex_text = "This is a significantly more sophisticated and intricate sentence structure with multiple clauses."
        complex_result = analyzer.analyze_text_complexity(complex_text)
        
        assert complex_result['avg_word_length'] > result['avg_word_length']
        assert complex_result['avg_sentence_length'] > result['avg_sentence_length']
    
    def test_detect_language_patterns(self):
        """Test language pattern detection."""
        analyzer = TextAnalyzer()
        
        # Formal text
        formal_text = "I would like to express my gratitude for this opportunity."
        formal_result = analyzer.detect_language_patterns(formal_text)
        assert formal_result['formality_score'] > 0.8
        
        # Informal text
        informal_text = "lol this is awesome btw gonna check it out"
        informal_result = analyzer.detect_language_patterns(informal_text)
        assert informal_result['informal_language'] is True
        assert informal_result['formality_score'] < 0.5
    
    def test_comprehensive_analysis(self):
        """Test comprehensive text analysis."""
        analyzer = TextAnalyzer()
        
        text = "This is NOT very good!!! It's actually terrible lol"
        result = analyzer.comprehensive_analysis(text)
        
        assert 'original_text' in result
        assert 'complexity' in result
        assert 'negation' in result
        assert 'intensifiers' in result
        assert 'emphasis' in result
        assert 'language_patterns' in result
        assert 'keywords' in result
        assert 'characteristics' in result
        
        # Check characteristics
        chars = result['characteristics']
        assert chars['is_negative_context'] is True  # Has "NOT"
        assert chars['is_emphatic'] is True  # Has "!!!"
        assert chars['is_informal'] is True  # Has "lol"


class TestTextUtils:
    """Test text utility functions."""
    
    def test_adjust_sentiment_for_context(self):
        """Test sentiment adjustment based on context."""
        # Test negation adjustment
        analysis_with_negation = {
            'negation': {'has_negation': True, 'negation_ratio': 0.2},
            'intensifiers': {'has_intensifiers': False, 'intensifier_ratio': 0},
            'emphasis': {'emphasis_score': 0}
        }
        
        adjusted = adjust_sentiment_for_context(0.8, analysis_with_negation)
        assert adjusted < 0  # Should flip positive to negative
        
        # Test intensifier adjustment
        analysis_with_intensifiers = {
            'negation': {'has_negation': False, 'negation_ratio': 0},
            'intensifiers': {'has_intensifiers': True, 'intensifier_ratio': 0.1},
            'emphasis': {'emphasis_score': 0}
        }
        
        adjusted = adjust_sentiment_for_context(0.5, analysis_with_intensifiers)
        assert adjusted > 0.5  # Should amplify positive sentiment
    
    def test_extract_entities(self):
        """Test entity extraction."""
        text = "Apple and Google are competing with Bitcoin and $TSLA stock prices"
        entities = extract_entities(text)
        
        assert 'companies' in entities
        assert 'cryptocurrencies' in entities
        assert 'stocks' in entities
        
        assert 'Apple' in entities['companies']
        assert 'Google' in entities['companies']
        assert 'Bitcoin' in entities['cryptocurrencies']
        assert '$TSLA' in entities['stocks']