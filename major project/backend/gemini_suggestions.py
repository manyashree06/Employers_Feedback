"""
Gemini API Integration for Personalized Feedback Suggestions
Uses Google's Gemini 1.5 Flash/Pro models for intelligent suggestion generation
"""

import os
import json
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True

    # Configure Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini API configured successfully")
    else:
        GEMINI_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")

except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning(
        "⚠️ google-generativeai not installed. Run: pip install google-generativeai"
    )


class GeminiSuggestionEngine:
    """
    Generates personalized feedback suggestions using Google Gemini API
    """

    def __init__(self, model_name: str = None):
        """
        Initialize Gemini suggestion engine

        Args:
            model_name: Gemini model to use. Options:
                - gemini-1.5-flash (fastest, recommended for production)
                - gemini-1.5-pro (most capable, slower)
                - gemini-1.0-pro (legacy)
        """
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Gemini API not available. Check configuration.")

        # Get model from env or use default
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # Map short names to actual available model names (updated for 2025)
        model_mapping = {
            "gemini-1.5-flash": "gemini-2.0-flash",  # Updated to 2.0
            "gemini-1.5-pro": "gemini-2.0-pro-exp",  # Updated to 2.0
            "gemini-1.0-pro": "gemini-pro-latest",
            "gemini-flash": "gemini-2.0-flash",
            "gemini-pro": "gemini-2.0-pro-exp",
            "gemini-2.0-flash": "gemini-2.0-flash",
            "gemini-2.0-pro": "gemini-2.0-pro-exp",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-pro": "gemini-2.5-pro",
        }

        # Use mapped name if available, otherwise use as-is
        full_model_name = model_mapping.get(self.model_name, self.model_name)

        # Initialize model
        self.model = genai.GenerativeModel(full_model_name)

        # Generation config for consistent outputs
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        logger.info(f"🚀 Gemini engine initialized with model: {self.model_name}")

    def generate_suggestion(
        self, feedback_text: str, sentiment_label: str, domain: str = "engineering"
    ) -> Optional[Dict]:
        """
        Generate personalized development suggestions using Gemini

        Args:
            feedback_text: The feedback text to analyze
            sentiment_label: Sentiment (Positive/Negative/Neutral)
            domain: Domain (engineering/medical/law/management/etc.)

        Returns:
            Dict with structured suggestion or None if generation fails
        """
        try:
            # Build domain-specific context
            domain_notes = self._get_domain_notes(domain)

            # Build prompt
            prompt = self._build_prompt(
                feedback_text, sentiment_label, domain, domain_notes
            )

            # Generate response
            logger.info(f"🤖 Calling Gemini API for: {feedback_text[:50]}...")
            response = self.model.generate_content(
                prompt, generation_config=self.generation_config
            )

            # Extract and parse JSON
            response_text = response.text
            logger.info(f"📥 Gemini response length: {len(response_text)} characters")

            # Parse JSON from response
            suggestion = self._parse_response(response_text)

            if suggestion:
                logger.info("✅ Successfully parsed Gemini suggestion")
                return suggestion
            else:
                logger.error("❌ Failed to parse Gemini response")
                return None

        except Exception as e:
            logger.error(f"❌ Gemini API error: {str(e)}")
            return None

    def _get_domain_notes(self, domain: str) -> str:
        """Get domain-specific context notes"""
        domain_notes = {
            "law": "IPC = Indian Penal Code. Focus on legal research, case briefs, court procedures.",
            "medical": "Focus on clinical skills, patient care, SOAP notes, medical terminology.",
            "engineering": "Focus on coding, system design, debugging, technical documentation.",
            "management": "Focus on leadership, team management, strategic planning, delegation.",
            "commerce": "Focus on financial analysis, accounting, business strategy, Excel skills.",
            "science": "Focus on research methodology, lab techniques, data analysis, publications.",
            "arts": "Focus on creative portfolio, exhibitions, artistic expression, networking.",
        }
        return domain_notes.get(
            domain, "Focus on professional development and skill building."
        )

    def _build_prompt(
        self, feedback_text: str, sentiment_label: str, domain: str, domain_notes: str
    ) -> str:
        """Build structured prompt for Gemini"""

        prompt = f"""You are an expert career development advisor specializing in {domain}.

FEEDBACK TEXT: "{feedback_text}"
SENTIMENT: {sentiment_label}
DOMAIN: {domain}
DOMAIN NOTE: {domain_notes}

Generate a personalized development plan in JSON format with EXACTLY this structure:

{{
    "title": "Brief title for the development plan (50-80 chars)",
    "primary_focus": "skill1|skill2|skill3",
    "urgency": "high" or "medium" or "low",
    "immediate_actions": [
        "Action 1: Specific, actionable step with concrete details (1-2 sentences)",
        "Action 2: Another specific action with measurable outcomes (1-2 sentences)",
        "Action 3: Third actionable step with timeline or resources (1-2 sentences)"
    ],
    "weekly_goals": [
        "Week 1-2: Specific goal with clear deliverable (1 sentence)",
        "Week 3-4: Next milestone with measurable target (1 sentence)",
        "Week 5-6: Final goal with completion criteria (1 sentence)"
    ],
    "resources": [
        "Resource 1: Specific platform/course/tool with URL or details (1 sentence)",
        "Resource 2: Another concrete resource with access info (1 sentence)",
        "Resource 3: Third practical resource with usage guidance (1 sentence)"
    ],
    "success_metrics": [
        "Metric 1: Measurable indicator of progress (1 sentence)",
        "Metric 2: Another quantifiable success measure (1 sentence)",
        "Metric 3: Final outcome indicator (1 sentence)"
    ],
    "timeline": "6 weeks" or "8 weeks" or "12 weeks"
}}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON (no markdown, no code blocks, no extra text)
2. Use domain-specific terminology and examples
3. Make actions specific and immediately implementable
4. Include concrete resources (courses, tools, platforms)
5. Each array must have EXACTLY 3 items
6. Keep each item concise (1-2 sentences max)
7. Focus on practical, actionable advice
8. Tailor suggestions to the sentiment (positive = advance, negative = improve basics)

Generate the JSON response now:"""

        return prompt

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response from Gemini"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parse JSON
            suggestion = json.loads(text)

            # Validate required fields
            required_fields = [
                "title",
                "primary_focus",
                "urgency",
                "immediate_actions",
                "weekly_goals",
                "resources",
                "success_metrics",
            ]

            for field in required_fields:
                if field not in suggestion:
                    logger.error(f"❌ Missing required field: {field}")
                    return None

            # Ensure exactly 3 items in each array
            for field in [
                "immediate_actions",
                "weekly_goals",
                "resources",
                "success_metrics",
            ]:
                if len(suggestion[field]) != 3:
                    logger.warning(
                        f"⚠️ {field} has {len(suggestion[field])} items, trimming to 3"
                    )
                    suggestion[field] = suggestion[field][:3]

            # Normalize urgency
            suggestion["urgency"] = suggestion.get("urgency", "medium").lower()

            return suggestion

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {str(e)}")
            logger.error(f"Raw response: {response_text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Parse error: {str(e)}")
            return None


# Factory function to get the appropriate suggestion engine
def get_suggestion_engine(provider: str = None):
    """
    Get suggestion engine based on provider preference

    Args:
        provider: 'gemini' or 'ollama' or None (auto-detect)

    Returns:
        Suggestion engine instance or None
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        if GEMINI_AVAILABLE:
            try:
                return GeminiSuggestionEngine()
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                return None
        else:
            logger.warning("Gemini not available, falling back to Ollama")
            provider = "ollama"

    if provider == "ollama":
        try:
            # Import Ollama engine
            from advanced_suggestions import AdvancedSuggestionEngine

            return AdvancedSuggestionEngine()
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            return None

    return None


# Convenience function for backward compatibility
def generate_suggestion_with_gemini(
    feedback_text: str, sentiment_label: str, domain: str = "engineering"
) -> Optional[Dict]:
    """
    Generate suggestion using Gemini API

    Convenience function for quick integration
    """
    try:
        engine = GeminiSuggestionEngine()
        return engine.generate_suggestion(feedback_text, sentiment_label, domain)
    except Exception as e:
        logger.error(f"Error generating suggestion: {e}")
        return None
