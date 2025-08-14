"""Sentiment analysis engine with multiple models."""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime

# VADER sentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Hugging Face transformers
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers")

# Text processing
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Handles text preprocessing for sentiment analysis."""
    
    def __init__(self):
        self.config = get_config()
        self._download_nltk_data()
        self._setup_patterns()
    
    def _download_nltk_data(self) -> None:
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                logger.warning(f"Could not download NLTK data: {e}")
    
    def _setup_patterns(self) -> None:
        """Setup regex patterns for text cleaning."""
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@\\w+')
        self.hashtag_pattern = re.compile(r'#\\w+')
        self.emoji_pattern = re.compile("["
                                      u"\\U0001F600-\\U0001F64F"  # emoticons
                                      u"\\U0001F300-\\U0001F5FF"  # symbols & pictographs
                                      u"\\U0001F680-\\U0001F6FF"  # transport & map symbols
                                      u"\\U0001F1E0-\\U0001F1FF"  # flags (iOS)
                                      u"\\U00002500-\\U00002BEF"  # chinese char
                                      u"\\U00002702-\\U000027B0"
                                      u"\\U00002702-\\U000027B0"
                                      u"\\U000024C2-\\U0001F251"
                                      u"\\U0001f926-\\U0001f937"
                                      u"\\U00010000-\\U0010ffff"
                                      u"\\u2640-\\u2642"
                                      u"\\u2600-\\u2B55"
                                      u"\\u200d"
                                      u"\\u23cf"
                                      u"\\u23e9"
                                      u"\\u231a"
                                      u"\\ufe0f"  # dingbats
                                      u"\\u3030"
                                      "]+", flags=re.UNICODE)
    
    def preprocess(self, text: str) -> str:
        """Preprocess text for sentiment analysis."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs if configured
        if self.config.text_processing.remove_urls:
            text = self.url_pattern.sub('', text)
        
        # Remove mentions if configured
        if self.config.text_processing.remove_mentions:
            text = self.mention_pattern.sub('', text)
        
        # Remove hashtags if configured
        if self.config.text_processing.remove_hashtags:
            text = self.hashtag_pattern.sub('', text)
        
        # Handle emojis
        if self.config.text_processing.handle_emojis:
            text = self.emoji_pattern.sub(' [EMOJI] ', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        max_length = self.config.text_processing.max_text_length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text


class VADERAnalyzer:
    """VADER sentiment analyzer wrapper."""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.model_name = "vader"
        self.model_version = "3.3.2"
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER."""
        try:
            start_time = time.time()
            scores = self.analyzer.polarity_scores(text)
            processing_time = time.time() - start_time
            
            # VADER provides compound, pos, neu, neg scores
            # Compound score is the main sentiment indicator (-1 to 1)
            compound = scores['compound']
            
            # Calculate confidence based on the magnitude of compound score
            confidence = abs(compound)
            
            return {
                'model_name': self.model_name,
                'model_version': self.model_version,
                'compound_score': compound,
                'positive_score': scores['pos'],
                'negative_score': scores['neg'],
                'neutral_score': scores['neu'],
                'confidence': confidence,
                'processing_time': processing_time,
                'raw_output': scores
            }
            
        except Exception as e:
            logger.error(f"VADER analysis error: {e}")
            return self._get_error_result(e)
    
    def _get_error_result(self, error: Exception) -> Dict[str, Any]:
        """Return error result structure."""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'compound_score': 0.0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'neutral_score': 1.0,
            'confidence': 0.0,
            'processing_time': 0.0,
            'raw_output': {'error': str(error)}
        }


class RoBERTaAnalyzer:
    """RoBERTa sentiment analyzer using Hugging Face."""
    
    def __init__(self):
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.model_version = "latest"
        self.pipeline = None
        self.tokenizer = None
        
        if HF_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the RoBERTa model."""
        try:
            logger.info(f"Loading {self.model_name} model...")
            
            # Initialize the pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                top_k=None  # Return all scores (replaces deprecated return_all_scores=True)
            )
            
            # Also load tokenizer for length checking
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            logger.info("RoBERTa model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading RoBERTa model: {e}")
            self.pipeline = None
            self.tokenizer = None
    
    def is_available(self) -> bool:
        """Check if RoBERTa analyzer is available."""
        return HF_AVAILABLE and self.pipeline is not None
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using RoBERTa."""
        if not self.is_available():
            return self._get_unavailable_result()
        
        try:
            start_time = time.time()
            
            # Check text length and truncate if necessary
            if self.tokenizer:
                tokens = self.tokenizer.encode(text, truncation=True, max_length=512)
                if len(tokens) >= 512:
                    text = self.tokenizer.decode(tokens[:-1], skip_special_tokens=True)
            
            # Get predictions
            results = self.pipeline(text)
            processing_time = time.time() - start_time
            
            # Handle nested list format (RoBERTa returns [[{results}]])
            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
                results = results[0]
            
            # Convert to our format
            scores = {result['label'].lower(): result['score'] for result in results}
            
            # Map labels to our format
            positive_score = scores.get('positive', 0.0)
            negative_score = scores.get('negative', 0.0)
            neutral_score = scores.get('neutral', 0.0)
            
            # Calculate compound score (-1 to 1)
            compound_score = positive_score - negative_score
            
            # Confidence is the maximum score
            confidence = max(positive_score, negative_score, neutral_score)
            
            return {
                'model_name': self.model_name,
                'model_version': self.model_version,
                'compound_score': compound_score,
                'positive_score': positive_score,
                'negative_score': negative_score,
                'neutral_score': neutral_score,
                'confidence': confidence,
                'processing_time': processing_time,
                'raw_output': {
                    'results': results,
                    'scores': scores
                }
            }
            
        except Exception as e:
            logger.error(f"RoBERTa analysis error: {e}")
            return self._get_error_result(e)
    
    def _get_unavailable_result(self) -> Dict[str, Any]:
        """Return result when model is unavailable."""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'compound_score': 0.0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'neutral_score': 1.0,
            'confidence': 0.0,
            'processing_time': 0.0,
            'raw_output': {'error': 'Model not available'}
        }
    
    def _get_error_result(self, error: Exception) -> Dict[str, Any]:
        """Return error result structure."""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'compound_score': 0.0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'neutral_score': 1.0,
            'confidence': 0.0,
            'processing_time': 0.0,
            'raw_output': {'error': str(error)}
        }


class SentimentAnalyzer:
    """Main sentiment analyzer that combines multiple models."""
    
    def __init__(self):
        self.config = get_config()
        self.preprocessor = TextPreprocessor()
        
        # Initialize analyzers
        self.analyzers = {}
        
        # Always initialize VADER
        try:
            self.analyzers['vader'] = VADERAnalyzer()
            logger.info("VADER analyzer initialized")
        except Exception as e:
            logger.error(f"Error initializing VADER: {e}")
        
        # Initialize RoBERTa if available and enabled
        if self.config.sentiment.models.get('roberta', {}).get('enabled', True):
            try:
                roberta = RoBERTaAnalyzer()
                if roberta.is_available():
                    self.analyzers['roberta'] = roberta
                    logger.info("RoBERTa analyzer initialized")
                else:
                    logger.warning("RoBERTa analyzer not available")
            except Exception as e:
                logger.error(f"Error initializing RoBERTa: {e}")
    
    def analyze_text(self, text: str) -> List[Dict[str, Any]]:
        """Analyze text sentiment using all available models."""
        if not text or not text.strip():
            return []
        
        # Preprocess text
        processed_text = self.preprocessor.preprocess(text)
        if not processed_text:
            return []
        
        results = []
        
        for name, analyzer in self.analyzers.items():
            try:
                # Check if model is enabled in config
                model_config = self.config.sentiment.models.get(name, {})
                if not model_config.get('enabled', True):
                    continue
                
                result = analyzer.analyze(processed_text)
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error analyzing with {name}: {e}")
                continue
        
        return results
    
    def get_weighted_sentiment(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate weighted sentiment from multiple model results."""
        if not results:
            return None
        
        # Get weights from config
        vader_weight = self.config.sentiment.models.get('vader', {}).get('weight', 0.4)
        roberta_weight = self.config.sentiment.models.get('roberta', {}).get('weight', 0.6)
        
        weights = {
            'vader': vader_weight,
            'roberta': roberta_weight
        }
        
        # Calculate weighted averages
        total_weight = 0
        weighted_compound = 0
        weighted_positive = 0
        weighted_negative = 0
        weighted_neutral = 0
        weighted_confidence = 0
        
        model_results = {}
        
        for result in results:
            model_name = result['model_name'].split('/')[-1].split('-')[0]  # Extract model type
            weight = weights.get(model_name, 1.0)
            
            weighted_compound += result['compound_score'] * weight
            weighted_positive += result['positive_score'] * weight
            weighted_negative += result['negative_score'] * weight
            weighted_neutral += result['neutral_score'] * weight
            weighted_confidence += result['confidence'] * weight
            
            total_weight += weight
            model_results[model_name] = result
        
        if total_weight == 0:
            return None
        
        # Normalize by total weight
        final_result = {
            'compound_score': weighted_compound / total_weight,
            'positive_score': weighted_positive / total_weight,
            'negative_score': weighted_negative / total_weight,
            'neutral_score': weighted_neutral / total_weight,
            'confidence': weighted_confidence / total_weight,
            'model_count': len(results),
            'models_used': list(model_results.keys()),
            'individual_results': model_results
        }
        
        return final_result
    
    def get_sentiment_label(self, compound_score: float) -> str:
        """Get sentiment label from compound score."""
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def is_high_confidence(self, confidence: float) -> bool:
        """Check if confidence meets threshold."""
        threshold = self.config.sentiment.confidence_threshold
        return confidence >= threshold
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze multiple texts efficiently."""
        results = []
        
        for i, text in enumerate(texts):
            try:
                analysis_results = self.analyze_text(text)
                weighted_result = self.get_weighted_sentiment(analysis_results)
                
                if weighted_result:
                    weighted_result['text_index'] = i
                    weighted_result['sentiment_label'] = self.get_sentiment_label(weighted_result['compound_score'])
                    weighted_result['high_confidence'] = self.is_high_confidence(weighted_result['confidence'])
                
                results.append(weighted_result)
                
            except Exception as e:
                logger.error(f"Error analyzing text {i}: {e}")
                results.append(None)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        info = {
            'available_models': list(self.analyzers.keys()),
            'model_details': {},
            'configuration': self.config.sentiment.model_dump()
        }
        
        for name, analyzer in self.analyzers.items():
            info['model_details'][name] = {
                'model_name': analyzer.model_name,
                'model_version': getattr(analyzer, 'model_version', 'unknown'),
                'available': getattr(analyzer, 'is_available', lambda: True)()
            }
        
        return info