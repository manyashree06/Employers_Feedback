"""
Hybrid Sentiment Analysis System
Combines keyword-based detection with pre-trained transformer model
for robust sentiment classification
"""

from textblob import TextBlob
from typing import Dict, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import transformers, but don't fail if not available
try:
    from transformers import pipeline
    import torch

    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers available - using hybrid sentiment analysis")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available - using keyword-only sentiment analysis")


class SentimentAnalyzer:
    """
    Hybrid sentiment analyzer that combines:
    1. Pre-trained transformer model (distilbert-base-uncased-finetuned-sst-2-english)
       - Trained on 67k+ movie reviews with 2-class sentiment
    2. Keyword-based detection for domain-specific terms
    3. TextBlob as fallback
    """

    def __init__(self):
        self.model = None
        self.model_confidence_threshold = 0.65  # Trust model if confidence > 65%

        # Initialize transformer model if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use GPU if available
                device = 0 if torch.cuda.is_available() else -1

                # Load pre-trained sentiment model (DistilBERT fine-tuned on SST-2)
                # This model has ~90% accuracy on sentiment classification
                self.model = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=device,
                    truncation=True,
                    max_length=512,
                )
                logger.info(
                    f"Loaded sentiment model on {'GPU' if device == 0 else 'CPU'}"
                )
            except Exception as e:
                logger.error(f"Failed to load transformer model: {e}")
                self.model = None

        # Define keyword indicators (fallback and for edge cases)
        self._setup_keyword_indicators()

    def _setup_keyword_indicators(self):
        """Setup comprehensive keyword indicators"""

        # Strong negative indicators
        self.negative_indicators = [
            "weak",
            "weaker",
            "weakest",
            "weakness",
            "weaknesses",
            "poor",
            "poorer",
            "poorest",
            "poorly",
            "bad",
            "worse",
            "worst",
            "badly",
            "fail",
            "failing",
            "failed",
            "failure",
            "fails",
            "lack",
            "lacking",
            "lacks",
            "lacked",
            "insufficient",
            "inadequate",
            "deficient",
            "unable",
            "incapable",
            "incompetent",
            "struggle",
            "struggling",
            "struggles",
            "struggled",
            "difficult",
            "difficulty",
            "difficulties",
            "confused",
            "confusing",
            "confusion",
            "lost",
            "unclear",
            "uncertain",
            "needs improvement",
            "needs to improve",
            "must improve",
            "needs work",
            "needs attention",
            "requires improvement",
            "needs to learn",
            "must learn",
            "should learn",
            "not good",
            "not great",
            "not strong",
            "no understanding",
            "no knowledge",
            "no grasp",
            "below average",
            "below expectations",
            "subpar",
            "disappointed",
            "disappointing",
            "frustrating",
            "problem",
            "problematic",
            "issue",
            "issues",
            "error",
            "errors",
            "mistake",
            "mistakes",
            "wrong",
            "incorrect",
            "inaccurate",
        ]

        # Strong positive indicators
        self.positive_indicators = [
            "excellent",
            "outstanding",
            "exceptional",
            "exemplary",
            "great",
            "greater",
            "greatest",
            "amazing",
            "wonderful",
            "strong",
            "stronger",
            "strongest",
            "solid",
            "impressive",
            "remarkable",
            "notable",
            "noteworthy",
            "proficient",
            "skilled",
            "competent",
            "capable",
            "master",
            "mastery",
            "expert",
            "expertise",
            "excel",
            "excels",
            "excelled",
            "excelling",
            "succeed",
            "succeeds",
            "succeeded",
            "succeeding",
            "achieve",
            "achieves",
            "achieved",
            "achievement",
            "progress",
            "progressing",
            "progressed",
            "improve",
            "improves",
            "improved",
            "improving",
            "thorough",
            "comprehensive",
            "complete",
            "detailed",
            "deep",
            "deeper",
            "deepest",
            "depth",
            "understand",
            "understands",
            "understanding",
            "understood",
            "innovative",
            "creative",
            "original",
            "efficient",
            "effective",
            "productive",
            "professional",
            "polished",
            "refined",
            "above average",
            "exceeds expectations",
            "surpasses",
        ]

        # Neutral indicators
        self.neutral_indicators = [
            "okay",
            "ok",
            "fine",
            "acceptable",
            "satisfactory",
            "average",
            "typical",
            "normal",
            "standard",
            "moderate",
            "mixed",
            "varied",
            "inconsistent",
            "some",
            "sometimes",
            "occasionally",
            "generally",
            "usually",
            "mostly",
            "progressing",
            "developing",
            "learning",
            "attentive",
            "participates",
            "engaged",
            "meets expectations",
            "on track",
        ]

    def analyze(self, text: str) -> Tuple[str, float, Dict]:
        """
        Analyze sentiment with TRANSFORMER as primary method
        Keywords only used for strong override (3-4+ matches) or if transformer fails

        Priority:
        1. Detect MIXED feedback (positive + negative elements) → Neutral
        2. Transformer model (any confidence) - PRIMARY
        3. Very strong keyword override (4+ matches) - OVERRIDE
        4. Strong keyword override (3+ matches) - BACKUP
        5. Default Neutral - LAST RESORT

        Returns:
            Tuple of (label, confidence, details)
            - label: "Positive", "Negative", or "Neutral"
            - confidence: 0.0 to 1.0
            - details: dict with method used and scores
        """
        if not text or not text.strip():
            return "Neutral", 0.0, {"method": "empty_text"}

        text_lower = text.lower()

        # Count keywords first (for potential override)
        negative_count = sum(1 for ind in self.negative_indicators if ind in text_lower)
        positive_count = sum(1 for ind in self.positive_indicators if ind in text_lower)
        neutral_count = sum(1 for ind in self.neutral_indicators if ind in text_lower)

        # Detect balanced/mixed indicators (words suggesting both sides)
        # These words almost always indicate balanced feedback showing both strengths and limitations
        mixed_indicators = [
            "but",
            "however",
            "though",
            "although",
            "yet",
            "while",
            "without",
            "except",
        ]
        has_mixed_structure = any(ind in text_lower for ind in mixed_indicators)

        # FAST PATH: If "but/however" is present, likely NEUTRAL (balanced feedback)
        # Exception: Only if there's EXTREME negative language (4+ negative keywords)
        if has_mixed_structure:
            # Check for extreme negativity (multiple failures, very poor performance)
            extreme_negative_words = [
                "terrible",
                "awful",
                "horrible",
                "dreadful",
                "failed",
                "failing",
                "very poor",
                "very bad",
                "extremely weak",
                "completely lacking",
                "no understanding at all",
                "totally confused",
            ]
            extreme_negative_count = sum(
                1 for word in extreme_negative_words if word in text_lower
            )

            # If extreme negativity (2+ extreme words), let transformer decide
            if extreme_negative_count >= 2:
                pass  # Fall through to transformer
            # Otherwise, "but/however" almost always means balanced/neutral feedback
            else:
                return (
                    "Neutral",
                    0.85,
                    {
                        "method": "balanced_structure_detected",
                        "reason": "'but/however' indicates balanced feedback with both strengths and areas for growth",
                    },
                )

        # Success with limitation pattern (without "but/however")
        # Example: "Answered questions correctly", "Completed task" + limitation word
        success_words = [
            "solved",
            "completed",
            "finished",
            "achieved",
            "passed",
            "answered",
        ]
        limitation_words = [
            "didn't",
            "did not",
            "couldn't",
            "could not",
            "without",
            "not",
        ]
        has_success = any(word in text_lower for word in success_words)
        has_limitation = any(word in text_lower for word in limitation_words)

        if (
            has_success
            and has_limitation
            and not any(neg in text_lower for neg in ["fail", "poor", "bad", "weak"])
        ):
            return (
                "Neutral",
                0.80,
                {
                    "method": "success_with_limitation",
                    "reason": "Achievement mentioned with limitation (not criticism) suggests balanced performance",
                },
            )

        # Method 1: TRANSFORMER MODEL - PRIMARY METHOD (use regardless of confidence)
        if self.model:
            try:
                result = self.model(text[:512])[0]  # Truncate to max length
                model_label = result["label"]  # 'POSITIVE' or 'NEGATIVE'
                model_score = result["score"]  # Confidence 0-1

                # Check if keywords STRONGLY disagree (4+ opposite keywords = override)
                if model_label == "POSITIVE" and negative_count >= 4:
                    return (
                        "Negative",
                        0.90,
                        {
                            "method": "keyword_strong_override",
                            "transformer_said": "Positive",
                            "negative_count": negative_count,
                            "reason": "4+ negative keywords override transformer",
                        },
                    )
                elif model_label == "NEGATIVE" and positive_count >= 4:
                    return (
                        "Positive",
                        0.90,
                        {
                            "method": "keyword_strong_override",
                            "transformer_said": "Negative",
                            "positive_count": positive_count,
                            "reason": "4+ positive keywords override transformer",
                        },
                    )

                # Otherwise, TRUST THE TRANSFORMER
                if model_label == "POSITIVE":
                    return (
                        "Positive",
                        model_score,
                        {
                            "method": "transformer_primary",
                            "model_confidence": model_score,
                            "negative_count": negative_count,
                            "positive_count": positive_count,
                        },
                    )
                elif model_label == "NEGATIVE":
                    return (
                        "Negative",
                        model_score,
                        {
                            "method": "transformer_primary",
                            "model_confidence": model_score,
                            "negative_count": negative_count,
                            "positive_count": positive_count,
                        },
                    )
            except Exception as e:
                logger.error(f"Transformer model error: {e}")
                # Fall through to keyword backup if transformer fails

        # Method 2: KEYWORD BACKUP (only if transformer completely failed)
        # Very strong keyword signals (3+ matches)
        if negative_count >= 3:
            return (
                "Negative",
                0.85,
                {
                    "method": "keyword_backup_strong",
                    "negative_count": negative_count,
                    "positive_count": positive_count,
                    "reason": "Transformer failed, using keywords",
                },
            )

        if positive_count >= 3:
            return (
                "Positive",
                0.85,
                {
                    "method": "keyword_backup_strong",
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "reason": "Transformer failed, using keywords",
                },
            )

        if neutral_count >= 3:
            return (
                "Neutral",
                0.75,
                {
                    "method": "keyword_backup_neutral",
                    "neutral_count": neutral_count,
                    "reason": "Transformer failed, using keywords",
                },
            )

        # Method 3: Default to Neutral if everything failed
        # TextBlob removed - only transformer and keywords used
        # TextBlob removed - only transformer and keywords used
        return "Neutral", 0.50, {"method": "default_neutral"}


# Create global instance
_analyzer = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create global sentiment analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> Tuple[str, float, Dict]:
    """
    Convenience function to analyze sentiment

    Args:
        text: Text to analyze

    Returns:
        Tuple of (label, confidence, details)
    """
    analyzer = get_sentiment_analyzer()
    return analyzer.analyze(text)


# Legacy compatibility function
def score_to_label(score: float, text: str = "") -> str:
    """
    Legacy function for backward compatibility
    Now uses hybrid sentiment analysis
    """
    if text:
        label, confidence, details = analyze_sentiment(text)
        logger.info(
            f"Sentiment: {label} (confidence: {confidence:.2f}, method: {details.get('method')})"
        )
        return label

    # Fallback to score-based if no text provided
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"
