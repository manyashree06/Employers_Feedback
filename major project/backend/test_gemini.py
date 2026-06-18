"""
Quick test script for Gemini API integration
Run this to verify your Gemini setup is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 GEMINI API TEST SCRIPT")
print("=" * 60)

# Check environment variables
print("\n1️⃣  Checking environment variables...")
api_key = os.getenv("GEMINI_API_KEY")
provider = os.getenv("LLM_PROVIDER", "gemini")
model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if api_key:
    print(f"   ✅ GEMINI_API_KEY: {api_key[:10]}...{api_key[-5:]}")
else:
    print("   ❌ GEMINI_API_KEY not found!")
    print("   💡 Create a .env file with: GEMINI_API_KEY=your_key_here")
    sys.exit(1)

print(f"   ✅ LLM_PROVIDER: {provider}")
print(f"   ✅ GEMINI_MODEL: {model}")

# Check package installation
print("\n2️⃣  Checking package installation...")
try:
    import google.generativeai as genai

    print("   ✅ google-generativeai installed")
except ImportError:
    print("   ❌ google-generativeai not installed!")
    print("   💡 Run: pip install google-generativeai")
    sys.exit(1)

# Initialize Gemini engine
print("\n3️⃣  Initializing Gemini engine...")
try:
    from gemini_suggestions import GeminiSuggestionEngine

    engine = GeminiSuggestionEngine(model_name=model)
    print(f"   ✅ Engine initialized with model: {engine.model_name}")
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    sys.exit(1)

# Test cases
test_cases = [
    {
        "feedback": "Shows excellent problem-solving skills and works well independently",
        "sentiment": "Positive",
        "domain": "engineering",
    },
    {
        "feedback": "Good communication but struggles with meeting deadlines",
        "sentiment": "Neutral",
        "domain": "management",
    },
    {
        "feedback": "Poor understanding of core concepts, needs significant improvement",
        "sentiment": "Negative",
        "domain": "science",
    },
]

print("\n4️⃣  Testing suggestion generation...")
print("-" * 60)

success_count = 0
for i, test in enumerate(test_cases, 1):
    print(f"\n📝 Test Case {i}: {test['sentiment']} feedback")
    print(f"   Feedback: {test['feedback'][:60]}...")
    print(f"   Domain: {test['domain']}")

    try:
        result = engine.generate_suggestion(
            feedback_text=test["feedback"],
            sentiment_label=test["sentiment"],
            domain=test["domain"],
        )

        if result:
            print(f"   ✅ Success!")
            print(f"      Title: {result['title'][:50]}...")
            print(f"      Urgency: {result['urgency']}")
            print(f"      Timeline: {result.get('timeline', 'N/A')}")
            print(f"      Actions: {len(result['immediate_actions'])} items")
            print(f"      Goals: {len(result['weekly_goals'])} items")
            print(f"      Resources: {len(result['resources'])} items")
            print(f"      Metrics: {len(result['success_metrics'])} items")
            success_count += 1
        else:
            print("   ❌ Failed: No result returned")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}...")

print("\n" + "=" * 60)
print(f"📊 TEST RESULTS: {success_count}/{len(test_cases)} passed")

if success_count == len(test_cases):
    print("✅ All tests passed! Gemini API is working correctly.")
    print("\n🚀 Next steps:")
    print("   1. Start backend: python backend/app.py")
    print("   2. Submit feedback via frontend")
    print("   3. Check logs for 'Suggestion generated via Gemini API'")
elif success_count > 0:
    print("⚠️  Some tests passed. Check errors above.")
else:
    print("❌ All tests failed. Check your API key and configuration.")

print("=" * 60)
