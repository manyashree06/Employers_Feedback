import os
from datetime import datetime
from collections import defaultdict
import time
import hashlib
import logging

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import send_file
from textblob import TextBlob
import joblib

# Import hybrid sentiment analyzer
from sentiment_analyzer import analyze_sentiment, score_to_label

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
from sklearn.pipeline import Pipeline
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Import the advanced suggestion engine
try:
    from advanced_suggestions import AdvancedSuggestionEngine

    ADVANCED_SUGGESTIONS = True
    suggestion_engine = None  # Will be initialized after db is ready
except ImportError:
    ADVANCED_SUGGESTIONS = False
    suggestion_engine = None
    print("Advanced suggestions not available - using basic suggestions")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Database configuration
# Prefer PostgreSQL via DATABASE_URL env var; fallback to local SQLite for ease of development
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///app.db"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Simple in-memory cache for dashboard stats
stats_cache = {"data": None, "timestamp": 0, "file_hash": None}
CACHE_DURATION = 300  # 5 minutes


# Database model
class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    feedback_text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float, nullable=False)
    sentiment_label = db.Column(
        db.String(16), nullable=False
    )  # "Positive", "Negative", "Neutral"
    domain = db.Column(
        db.String(50), nullable=False, default="engineering"
    )  # Student domain: engineering, commerce, science, arts, etc.
    timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_text": self.feedback_text,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "domain": self.domain,
            "timestamp": self.timestamp.isoformat(),
        }


with app.app_context():
    db.create_all()

    # Initialize suggestion engine with database access
    if ADVANCED_SUGGESTIONS:
        suggestion_engine = AdvancedSuggestionEngine(db_session=db.session)
        print("Advanced suggestion engine initialized with database access")

# Load ML model if present (optional). For large datasets, train via train_model.py
MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "employer_feedback_bangalore.xlsx"),
)
model: Pipeline | None = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        model = None


# Utility: map polarity score to sentiment label with keyword enhancement
# TextBlob polarity is in [-1.0, 1.0] but often misses context, so we enhance with keywords
def score_to_label(score: float, text: str = "") -> str:
    # Expanded keyword-based override with variations and synonyms for better accuracy
    negative_indicators = [
        # Ability/Knowledge deficits
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
        "lack",
        "lacking",
        "lacks",
        "lacked",
        "insufficient",
        "insufficiently",
        "inadequate",
        "inadequately",
        "no knowledge",
        "no understanding",
        "no idea",
        "no clarity",
        "no grasp",
        "does not know",
        "doesnt know",
        "don't know",
        "do not know",
        "does not understand",
        "doesnt understand",
        "don't understand",
        "do not understand",
        "not clear",
        "not clarity",
        "unclear",
        "unclearly",
        "not good",
        "not great",
        "not well",
        "not able",
        "not capable",
        "not understanding",
        "not comprehending",
        "not grasping",
        "cannot",
        "can't",
        "unable",
        "incapable",
        "failing",
        "failed",
        "fail",
        "failure",
        "fails",
        # Improvement needs
        "needs to improve",
        "needs improvement",
        "need improvement",
        "needs to learn",
        "need to learn",
        "needs learning",
        "needs work",
        "needs attention",
        "needs focus",
        "requires improvement",
        "require improvement",
        "must improve",
        "should improve",
        "has to improve",
        "needs development",
        "needs training",
        "needs practice",
        # Struggle/Difficulty indicators
        "struggling",
        "struggle",
        "struggles",
        "struggled",
        "difficult",
        "difficulty",
        "difficulties",
        "difficultly",
        "hard time",
        "tough time",
        "challenging",
        "confused",
        "confusing",
        "confusion",
        "confuses",
        "lost",
        "losing",
        "clueless",
        # Performance issues
        "terrible",
        "terribly",
        "awful",
        "awfully",
        "horrible",
        "horribly",
        "dreadful",
        "dreadfully",
        "disappointing",
        "disappointed",
        "disappointment",
        "disappoints",
        "unsatisfactory",
        "unsatisfying",
        "dissatisfying",
        "substandard",
        "below standard",
        "below average",
        "below par",
        "very low",
        "very poor",
        "very weak",
        "extremely poor",
        "unacceptable",
        "unacceptably",
        # Negative action words
        "mistake",
        "mistakes",
        "error",
        "errors",
        "wrong",
        "problem",
        "problems",
        "issue",
        "issues",
        "deficient",
        "deficiency",
        "deficiencies",
        "incomplete",
        "incompletely",
        "unfinished",
        "missing",
        "missed",
        "misses",
        "forgotten",
        "forgot",
        "forgets",
        # Skills/Quality issues
        "unprofessional",
        "unprofessionally",
        "ineffective",
        "ineffectively",
        "inefficient",
        "inefficiently",
        "careless",
        "carelessly",
        "sloppy",
        "sloppily",
        "lazy",
        "laziness",
        "neglect",
        "neglected",
        "neglectful",
        "mediocre",
        "average at best",
    ]

    positive_indicators = [
        # Excellence/Quality
        "excellent",
        "excellently",
        "excellence",
        "outstanding",
        "outstandingly",
        "exceptional",
        "exceptionally",
        "remarkable",
        "remarkably",
        "superb",
        "superbly",
        "brilliant",
        "brilliantly",
        "brilliance",
        "perfect",
        "perfectly",
        "perfection",
        "flawless",
        "flawlessly",
        "impeccable",
        "impeccably",
        # Achievement/Success
        "great",
        "greater",
        "greatest",
        "greatly",
        "amazing",
        "amazingly",
        "wonderful",
        "wonderfully",
        "fantastic",
        "fantastically",
        "fabulous",
        "fabulously",
        "terrific",
        "terrifically",
        "impressive",
        "impressively",
        "impressed",
        "incredible",
        "incredibly",
        "phenomenal",
        "phenomenally",
        # Positive performance
        "strong",
        "stronger",
        "strongest",
        "strongly",
        "good",
        "better",
        "best",
        "well",
        "very good",
        "really good",
        "pretty good",
        "solid",
        "solidly",
        "effective",
        "effectively",
        "efficient",
        "efficiently",
        "skilled",
        "skillful",
        "skillfully",
        "talented",
        "talent",
        "capable",
        "capability",
        "competent",
        "competently",
        # Progress/Achievement
        "improved",
        "improving",
        "improvement",
        "improves",
        "progressed",
        "progressing",
        "progress",
        "progresses",
        "excelled",
        "excelling",
        "excels",
        "succeeded",
        "succeeding",
        "success",
        "successful",
        "successfully",
        "achieved",
        "achieving",
        "achievement",
        "achieves",
        "mastered",
        "mastering",
        "mastery",
        "masters",
        "accomplished",
        "accomplishing",
        "accomplishment",
        "accomplishes",
        # Positive descriptions
        "doing well",
        "doing great",
        "doing excellent",
        "good work",
        "great work",
        "excellent work",
        "well done",
        "nicely done",
        "perfectly done",
        "strong performance",
        "stellar performance",
        "top performance",
        "keeps up",
        "keep it up",
        "maintain",
        "thorough",
        "thoroughly",
        "comprehensive",
        "comprehensively",
        "dedicated",
        "dedication",
        "committed",
        "commitment",
        "professional",
        "professionally",
        "professionalism",
        "quality",
        "high quality",
        "top quality",
    ]

    # Neutral indicators (balanced, observational, mixed feedback)
    neutral_indicators = [
        "okay",
        "ok",
        "fine",
        "acceptable",
        "satisfactory",
        "average",
        "typical",
        "normal",
        "standard",
        "regular",
        "moderate",
        "moderately",
        "fair",
        "fairly",
        "reasonable",
        "reasonably",
        "adequate",
        "adequately",
        "mixed",
        "varied",
        "varies",
        "inconsistent",
        "variable",
        "some",
        "sometimes",
        "occasionally",
        "partial",
        "partially",
        "both",
        "however",
        "but",
        "although",
        "yet",
        "though",
        "certain areas",
        "some aspects",
        "in parts",
        "at times",
        "shows potential",
        "room for",
        "could be",
        "might be",
        "generally",
        "usually",
        "mostly",
        "often",
        "progressing",
        "developing",
        "learning",
        "working on",
        "building",
        "steady",
        "consistent effort",
        "making effort",
        "tries",
        "attempting",
        "attentive",
        "participates",
        "engaged",
        "present",
        "involved",
        "follows",
        "completes",
        "submits",
        "attends",
        "responds",
        "basic understanding",
        "fundamental grasp",
        "foundational knowledge",
        "meets expectations",
        "on track",
        "keeping pace",
    ]

    text_lower = text.lower() if text else ""

    # Check for strong negative indicators first (higher priority)
    if any(indicator in text_lower for indicator in negative_indicators):
        return "Negative"

    # Check for strong positive indicators
    if any(indicator in text_lower for indicator in positive_indicators):
        return "Positive"

    # Check for neutral indicators (balanced feedback)
    if any(indicator in text_lower for indicator in neutral_indicators):
        return "Neutral"

    # Fall back to TextBlob score with adjusted thresholds
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"


# Legacy score_to_label function now imported from sentiment_analyzer.py
# Uses hybrid approach: Transformer model + Keywords + TextBlob
# def score_to_label(score: float, text: str = "") -> str:
#     ... (moved to sentiment_analyzer.py)


@app.route("/api/feedback", methods=["POST"])
def create_feedback():
    """Accept JSON with feedback_text and domain, compute sentiment, store and return the record."""
    data = request.get_json(silent=True) or {}
    feedback_text = (data.get("feedback_text") or "").strip()
    domain = (data.get("domain") or "engineering").strip().lower()

    if not feedback_text:
        return jsonify({"error": "feedback_text is required"}), 400

    # Validate domain
    valid_domains = [
        "engineering",
        "commerce",
        "science",
        "arts",
        "medical",
        "law",
        "management",
        "other",
    ]
    if domain not in valid_domains:
        domain = "engineering"  # default fallback

    # Use the new hybrid sentiment analyzer (transformer + keywords + mixed detection)
    label, confidence, details = analyze_sentiment(feedback_text)

    # For backward compatibility, calculate TextBlob polarity but don't use it for classification
    polarity = float(TextBlob(feedback_text).sentiment.polarity)

    # Log sentiment analysis details
    logging.info(
        f"Sentiment analysis: {label} (confidence: {confidence:.2f}, method: {details.get('method')})"
    )

    record = Feedback(
        feedback_text=feedback_text,
        sentiment_score=polarity,  # Keep for backward compatibility
        sentiment_label=label,  # Use the hybrid analyzer result
        domain=domain,
        timestamp=datetime.utcnow(),
    )
    db.session.add(record)
    db.session.commit()

    # Update suggestion engine with new feedback for learning
    if ADVANCED_SUGGESTIONS and suggestion_engine:
        try:
            suggestion_engine.update_with_new_feedback(feedback_text, label, domain)
        except Exception as e:
            print(f"Failed to update suggestion engine: {e}")

    response = record.to_dict()
    # Optional suggestion based on ML model if available
    label_for_suggestion = label
    if model is not None:
        try:
            pred_label = model.predict([feedback_text])[0]
            response["ml_label"] = str(pred_label)
            pred_lower = str(pred_label).strip().lower()
            if pred_lower in {"positive", "neutral", "negative"}:
                label_for_suggestion = pred_lower.capitalize()
        except Exception:
            pass
    response["suggestion"] = generate_advanced_suggestion(
        feedback_text, label_for_suggestion, domain
    )
    return jsonify(response), 201


def generate_advanced_suggestion(
    text: str, label: str, domain: str = "engineering"
) -> dict:
    """Generate advanced, detailed suggestions using NLP analysis (Gemini or Ollama)"""

    # Try Gemini first if configured
    try:
        from gemini_suggestions import get_suggestion_engine

        engine = get_suggestion_engine()  # Auto-detects provider from env

        if engine:
            # Check if it's Gemini engine
            if hasattr(engine, "generate_suggestion"):
                # Gemini engine
                result = engine.generate_suggestion(text, label, domain)
                if result:
                    logging.info(f"✅ Suggestion generated via Gemini API")
                    return {
                        "suggestion": result,
                        "type": "gemini",
                        "confidence_score": 0.95,  # Gemini has high confidence
                        "sentiment_tone": label.lower(),
                        "domain": domain,
                    }
            else:
                # Ollama engine (AdvancedSuggestionEngine)
                result = engine.generate_comprehensive_suggestion(text, label, domain)
                if result:
                    logging.info(f"✅ Suggestion generated via Ollama")
                    return result
    except Exception as e:
        logging.error(f"❌ LLM engine failed: {e}")

    # Fallback: Try original Ollama engine if available
    if ADVANCED_SUGGESTIONS and suggestion_engine:
        try:
            return suggestion_engine.generate_comprehensive_suggestion(
                text, label, domain
            )
        except Exception as e:
            logging.error(f"Advanced suggestion engine failed: {e}")

    # Final fallback: basic suggestions
    logging.warning("⚠️ Falling back to basic suggestions")
    return {
        "suggestion": generate_suggestion(text, label, domain),
        "type": "basic",
        "confidence_score": 0.75,
        "sentiment_tone": label.lower(),
        "domain": domain,
    }


def generate_suggestion(text: str, label: str, domain: str = "engineering") -> str:
    # Simple heuristic suggestions; can be replaced by a trained recommender later
    text_lower = text.lower()

    # Domain-specific negative feedback suggestions
    if label == "Negative":
        if any(
            k in text_lower
            for k in ["communication", "communicate", "presentation", "speak"]
        ):
            if domain == "commerce":
                return "Focus on business communication: practice elevator pitches, join Toastmasters, and improve presentation skills for client interactions and business proposals."
            elif domain == "science":
                return "Enhance scientific communication: practice explaining complex concepts simply, join research presentation groups, and develop poster/paper presentation skills."
            elif domain == "arts":
                return "Improve creative communication: develop your portfolio presentation skills, practice articulating your creative process, and join critique groups."
            else:  # engineering or other
                return "Focus on technical communication: practice concise updates, join a speaking workshop, and seek peer feedback after presentations."

        if any(k in text_lower for k in ["deadline", "time", "late", "schedule"]):
            if domain == "commerce":
                return "Improve business time management: prioritize using ROI analysis, use project management tools like Asana, and master deadline negotiation skills."
            elif domain == "science":
                return "Enhance research time management: plan experiments with buffer time, maintain detailed lab notebooks, and balance coursework with research commitments."
            else:
                return "Improve time management: break tasks into milestones, use a planner, and review progress daily to anticipate blockers."

        if any(k in text_lower for k in ["quality", "work", "performance", "output"]):
            if domain == "commerce":
                return "Strengthen business analysis: master Excel/data analysis, improve report quality with clear insights, and develop attention to financial details."
            elif domain == "science":
                return "Enhance research quality: implement rigorous experimental controls, maintain detailed documentation, and practice peer review processes."
            else:
                return "Strengthen quality: add test cases, use code reviews, and adopt a checklist for deliverables."

        # Domain-specific general negative feedback
        if domain == "commerce":
            return "Identify improvement areas in business skills: set weekly goals for Excel proficiency, financial analysis, or client communication, and seek mentorship."
        elif domain == "science":
            return "Focus on research fundamentals: strengthen your experimental design, literature review skills, and data analysis capabilities through targeted practice."
        elif domain == "arts":
            return "Develop your creative portfolio: dedicate time daily to your craft, seek constructive critiques, and study works in your field systematically."
        else:
            return "Identify one improvement area, set a weekly goal, and review progress with a mentor."

    if label == "Neutral":
        if domain == "commerce":
            return "Build on business acumen: pursue certifications (CFA, CPA prep), take case study competitions, and develop industry-specific knowledge."
        elif domain == "science":
            return "Advance research capabilities: collaborate on publications, learn new lab techniques, and present at conferences to gain visibility."
        elif domain == "arts":
            return "Expand creative horizons: experiment with new mediums, collaborate with other artists, and build your professional network."
        else:
            return "Build on current performance: set stretch goals and ask for targeted feedback to level up."

    # Positive feedback
    if domain == "commerce":
        return "Excellent business performance: document your successful strategies, mentor junior students in finance/marketing, and contribute to case competitions."
    elif domain == "science":
        return "Outstanding research work: consider publishing your findings, mentor lab juniors, and explore advanced research opportunities or collaborations."
    elif domain == "arts":
        return "Impressive creative work: showcase your portfolio publicly, consider exhibitions or publications, and inspire fellow artists through workshops."
    else:
        return "Keep up the good work: document best practices and mentor peers to amplify impact."


@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    """Return all feedback entries as JSON array (newest first)."""
    records = Feedback.query.order_by(Feedback.timestamp.desc()).all()
    return jsonify([r.to_dict() for r in records])


@app.route("/api/dashboard_stats", methods=["GET"])
def dashboard_stats():
    """Return summary stats. If query param source=dataset (or DB empty), compute from dataset file.

    Dataset file path can be provided via env DATASET_PATH, defaulting to project-level employer_feedback_bangalore.xlsx.
    """
    source = request.args.get("source")

    def _get_file_hash(filepath):
        """Get file hash for cache invalidation"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None

    def _from_db():
        records = Feedback.query.all()
        total = len(records)
        avg_score = sum(r.sentiment_score for r in records) / total if total else 0.0
        counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for r in records:
            counts[r.sentiment_label] = counts.get(r.sentiment_label, 0) + 1
        by_day = defaultdict(list)
        for r in records:
            day = r.timestamp.date().isoformat()
            by_day[day].append(r.sentiment_score)
        timeseries = []
        for day in sorted(by_day.keys()):
            scores = by_day[day]
            timeseries.append(
                {
                    "date": day,
                    "count": len(scores),
                    "avg_score": sum(scores) / len(scores) if scores else 0.0,
                }
            )
        return {
            "total": total,
            "avg_sentiment_score": avg_score,
            "count_positive": counts.get("Positive", 0),
            "count_neutral": counts.get("Neutral", 0),
            "count_negative": counts.get("Negative", 0),
            "timeseries": timeseries,
            "source": "database",
        }

    def _from_dataset():
        dataset_path = os.getenv(
            "DATASET_PATH",
            os.path.normpath(
                os.path.join(
                    os.path.dirname(__file__), "..", "employer_feedback_bangalore.xlsx"
                )
            ),
        )

        # Check cache first
        current_time = time.time()
        file_hash = _get_file_hash(dataset_path)

        if (
            stats_cache["data"]
            and (current_time - stats_cache["timestamp"]) < CACHE_DURATION
            and stats_cache["file_hash"] == file_hash
        ):
            print(
                f"Returning cached data (age: {current_time - stats_cache['timestamp']:.1f}s)"
            )
            return stats_cache["data"]

        print("Computing fresh stats from dataset...")
        start_time = time.time()

        try:
            ext = os.path.splitext(dataset_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(dataset_path)
            else:
                df = pd.read_excel(dataset_path)
        except Exception as e:
            print(f"Error reading dataset: {e}")
            return {
                "total": 0,
                "avg_sentiment_score": 0.0,
                "count_positive": 0,
                "count_neutral": 0,
                "count_negative": 0,
                "timeseries": [],
                "source": "dataset",
                "error": "Could not read dataset file",
            }

        # Auto-detect columns
        def _find(cols, candidates):
            for c in cols:
                if c.lower() in candidates:
                    return c
            return None

        text_col = _find(df.columns, {"feedback_text", "feedback", "text"})
        label_col = _find(
            df.columns, {"sentiment_label", "label", "sentiment", "target"}
        )
        year_col = _find(df.columns, {"year_of_passout", "year", "passout_year"})

        if label_col is None:
            # If no label column, try to use a sample for quick analysis
            print("No sentiment labels found, using sample analysis...")
            if text_col is None:
                result = {
                    "total": 0,
                    "avg_sentiment_score": 0.0,
                    "count_positive": 0,
                    "count_neutral": 0,
                    "count_negative": 0,
                    "timeseries": [],
                    "source": "dataset",
                }
            else:
                # Use only a sample for performance
                sample_size = min(100, len(df))
                sample_df = df.sample(n=sample_size) if len(df) > sample_size else df

                labels = []
                for t in sample_df[text_col].astype(str).tolist():
                    try:
                        polarity = float(
                            TextBlob(str(t)[:200]).sentiment.polarity
                        )  # Limit text length
                        labels.append(score_to_label(polarity))
                    except:
                        labels.append("neutral")

                sample_df["__label"] = labels
                label_col = "__label"
                df = sample_df  # Use sample for rest of calculation
                sample_df["__label"] = labels
                label_col = "__label"
                df = sample_df  # Use sample for rest of calculation

        # Map labels to numeric for average
        label_to_score = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        series = df[label_col].astype(str).str.lower()
        total = int(series.shape[0])
        counts = {
            "Positive": int((series == "positive").sum()),
            "Neutral": int((series == "neutral").sum()),
            "Negative": int((series == "negative").sum()),
        }
        avg_score = (
            float(series.map(lambda s: label_to_score.get(s, 0.0)).mean())
            if total
            else 0.0
        )

        # Timeseries by year if available
        timeseries = []
        if year_col is not None:
            df_year = df[[year_col, label_col]].copy()
            df_year[label_col] = df_year[label_col].astype(str).str.lower()
            df_year["__score"] = df_year[label_col].map(
                lambda s: label_to_score.get(s, 0.0)
            )
            for year, group in df_year.groupby(year_col):
                scores = group["__score"].tolist()
                timeseries.append(
                    {
                        "date": str(year),
                        "count": int(len(scores)),
                        "avg_score": float(
                            sum(scores) / len(scores) if scores else 0.0
                        ),
                    }
                )
            # sort by year value if possible
            try:
                timeseries = sorted(
                    timeseries, key=lambda x: int(str(x["date"]).strip())
                )
            except Exception:
                timeseries = sorted(timeseries, key=lambda x: str(x["date"]))

        result = {
            "total": total,
            "avg_sentiment_score": avg_score,
            "count_positive": counts.get("Positive", 0),
            "count_neutral": counts.get("Neutral", 0),
            "count_negative": counts.get("Negative", 0),
            "timeseries": timeseries,
            "source": "dataset",
        }

        # Cache the result
        stats_cache["data"] = result
        stats_cache["timestamp"] = time.time()
        stats_cache["file_hash"] = file_hash

        processing_time = time.time() - start_time
        print(f"Stats computed in {processing_time:.2f}s")

        return result

    # Route logic
    if source == "dataset":
        return jsonify(_from_dataset())
    # Default: try DB; if empty, fallback to dataset
    db_stats = _from_db()
    if db_stats["total"] == 0:
        return jsonify(_from_dataset())
    return jsonify(db_stats)


@app.route("/api/suggest", methods=["POST"])
def suggest():
    data = request.get_json(silent=True) or {}
    text = (data.get("feedback_text") or "").strip()
    if not text:
        return jsonify({"error": "feedback_text is required"}), 400
    polarity = float(TextBlob(text).sentiment.polarity)
    label = score_to_label(polarity)
    ml_label = None
    result = {
        "sentiment_score": polarity,
        "sentiment_label": label,
    }
    if model is not None:
        try:
            ml_label = str(model.predict([text])[0])
            result["ml_label"] = ml_label
            # Optional: decision function / probabilities if classifier supports it
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba([text])[0]
                classes = list(getattr(model, "classes_", []))
                result["ml_probabilities"] = dict(
                    zip(map(str, classes), map(float, proba))
                )
        except Exception:
            pass
    label_for_suggestion = label
    if isinstance(ml_label, str) and ml_label.strip().lower() in {
        "positive",
        "neutral",
        "negative",
    }:
        label_for_suggestion = ml_label.strip().capitalize()
    result["suggestion"] = generate_suggestion(text, label_for_suggestion)
    return jsonify(result)


def format_suggestion_for_pdf(suggestion):
    """Format suggestion data into structured sections for PDF"""
    try:
        # Try to parse as JSON if it's a string
        if isinstance(suggestion, str):
            import json

            suggestion_data = json.loads(suggestion)
        else:
            suggestion_data = suggestion

        # Handle basic suggestions
        if isinstance(suggestion_data, str) or suggestion_data.get("type") == "basic":
            return (
                suggestion_data
                if isinstance(suggestion_data, str)
                else suggestion_data.get("suggestion", "")
            )

        # Return the parsed data for custom formatting
        return suggestion_data

    except Exception as e:
        print(f"Error formatting suggestion: {e}")
        # Fallback to original suggestion
        return str(suggestion)


@app.route("/generate-report", methods=["POST"])
def generate_report():
    """Generate a personalized PDF report in-memory from JSON {feedback, sentiment, suggestion}

    Streams the PDF back as an attachment named Feedback_Report.pdf
    """
    data = request.get_json(silent=True) or {}
    feedback = data.get("feedback") or data.get("feedback_text") or ""
    sentiment = data.get("sentiment") or data.get("sentiment_label") or ""
    suggestion = data.get("suggestion") or ""

    # Format suggestion into structured data
    formatted_suggestion = format_suggestion_for_pdf(suggestion)

    # Build PDF in-memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=12,
        alignment=1,  # Center
        fontName="Helvetica-Bold",
    )

    section_header = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=8,
        spaceBefore=12,
        fontName="Helvetica-Bold",
        borderPadding=6,
        leftIndent=0,
    )

    subsection_header = ParagraphStyle(
        "SubsectionHeader",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=6,
        spaceBefore=8,
        fontName="Helvetica-Bold",
    )

    body_text = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
        textColor=colors.HexColor("#1f2937"),
    )

    bullet_text = ParagraphStyle(
        "BulletText",
        parent=body_text,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=4,
    )

    meta_text = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=8,
    )

    elems = []

    # Title
    elems.append(Paragraph("Personalized Feedback Report", title_style))
    elems.append(Spacer(1, 3))

    # Date
    elems.append(
        Paragraph(
            f'Generated on {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}',
            meta_text,
        )
    )
    elems.append(Spacer(1, 10))

    # Divider line
    elems.append(
        Table(
            [[""]],
            colWidths=[160 * mm],
            style=TableStyle(
                [("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.HexColor("#e5e7eb"))]
            ),
        )
    )
    elems.append(Spacer(1, 12))

    # Feedback Summary Section
    elems.append(Paragraph("📋 Feedback Summary", section_header))
    feedback_table = Table(
        [[Paragraph(feedback.replace("\n", "<br/>"), body_text)]],
        colWidths=[160 * mm],
    )
    feedback_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elems.append(feedback_table)
    elems.append(Spacer(1, 12))

    # Sentiment Analysis
    elems.append(Paragraph("💭 Detected Sentiment", section_header))
    sentiment_color = {
        "Positive": colors.HexColor("#10b981"),
        "Negative": colors.HexColor("#ef4444"),
        "Neutral": colors.HexColor("#6b7280"),
    }.get(sentiment, colors.HexColor("#6b7280"))

    sentiment_table = Table(
        [[Paragraph(f"<b>{sentiment}</b>", body_text)]],
        colWidths=[160 * mm],
    )
    sentiment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), sentiment_color.clone(alpha=0.1)),
                ("BOX", (0, 0), (-1, -1), 2, sentiment_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elems.append(sentiment_table)
    elems.append(Spacer(1, 15))

    # Personalized Suggestion Section
    elems.append(Paragraph("🎯 Personalized Development Plan", section_header))
    elems.append(Spacer(1, 8))

    # Handle structured suggestion data
    if isinstance(formatted_suggestion, dict):
        suggestion_data = formatted_suggestion

        # Title and metadata
        if suggestion_data.get("title"):
            elems.append(
                Paragraph(f'<b>{suggestion_data["title"]}</b>', subsection_header)
            )

        # Focus area and priority in a small table
        meta_items = []
        if suggestion_data.get("primary_focus"):
            meta_items.append(
                [
                    "Focus Area:",
                    suggestion_data["primary_focus"].replace("_", " ").title(),
                ]
            )
        if suggestion_data.get("urgency"):
            meta_items.append(["Priority Level:", suggestion_data["urgency"].title()])

        if meta_items:
            meta_table = Table(meta_items, colWidths=[40 * mm, 120 * mm])
            meta_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e40af")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbeafe")),
                    ]
                )
            )
            elems.append(meta_table)
            elems.append(Spacer(1, 12))

        # Immediate Actions
        if suggestion_data.get("immediate_actions"):
            elems.append(Paragraph("🚀 Immediate Actions", subsection_header))
            for i, action in enumerate(suggestion_data["immediate_actions"][:5], 1):
                elems.append(Paragraph(f"<b>{i}.</b> {action}", bullet_text))
            elems.append(Spacer(1, 10))

        # 6-Week Development Plan
        if suggestion_data.get("weekly_goals"):
            elems.append(Paragraph("📅 6-Week Development Plan", subsection_header))
            for i, goal in enumerate(suggestion_data["weekly_goals"][:6], 1):
                elems.append(Paragraph(f"<b>Week {i}:</b> {goal}", bullet_text))
            elems.append(Spacer(1, 10))

        # Learning Resources
        if suggestion_data.get("resources"):
            elems.append(Paragraph("📚 Recommended Resources", subsection_header))
            for resource in suggestion_data["resources"][:5]:
                elems.append(Paragraph(f"• {resource}", bullet_text))
            elems.append(Spacer(1, 10))

        # Success Metrics
        if suggestion_data.get("success_metrics"):
            elems.append(Paragraph("✅ Success Metrics", subsection_header))
            for metric in suggestion_data["success_metrics"]:
                elems.append(Paragraph(f"• {metric}", bullet_text))
            elems.append(Spacer(1, 10))

        # Timeline
        if suggestion_data.get("timeline"):
            elems.append(Paragraph("⏱️ Expected Timeline", subsection_header))
            elems.append(Paragraph(suggestion_data["timeline"], body_text))
            elems.append(Spacer(1, 10))

    else:
        # Fallback for simple text suggestions
        elems.append(
            Paragraph(str(formatted_suggestion).replace("\n", "<br/>"), body_text)
        )
        elems.append(Spacer(1, 12))

    # Footer
    elems.append(Spacer(1, 15))
    elems.append(
        Table(
            [[""]],
            colWidths=[160 * mm],
            style=TableStyle(
                [("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb"))]
            ),
        )
    )
    elems.append(Spacer(1, 8))
    footer_style = ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#9ca3af"),
        alignment=1,
    )
    elems.append(
        Paragraph(
            "Generated by Feedback Analytics System | Empowering Growth Through Insights",
            footer_style,
        )
    )

    doc.build(elems)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Feedback_Report.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    # Use port 5000 by default so CRA can run on 3000; disable debug reloader for stability
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
