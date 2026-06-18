# Google Gemini API Setup Guide

This guide explains how to switch from local Ollama to cloud-based Google Gemini API for generating personalized feedback suggestions.

## Why Choose Gemini API?

### Advantages ✅
1. **No Local Setup Required** - No need to download 3.3GB Gemma model
2. **Better Performance** - Cloud infrastructure, faster response times
3. **Scalability** - Handle multiple users simultaneously without GPU limitations
4. **Always Updated** - Latest models without manual updates
5. **Lower Maintenance** - No local server management
6. **Better Quality** - Access to Gemini 1.5 Pro/Flash models

### Disadvantages ⚠️
1. **Internet Required** - Won't work offline
2. **API Costs** - Free tier: 15 requests/minute, 1500/day (generous for development)
3. **API Key Management** - Need to secure API keys
4. **Data Privacy** - Feedback sent to Google servers

---

## Step 1: Get Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** button
4. Click **"Create API Key in new project"**
5. Copy the generated API key (starts with `AIza...`)

⚠️ **Security Note**: Never commit your API key to Git! Keep it in `.env` file (already in `.gitignore`).

---

## Step 2: Install Dependencies

```bash
cd backend
pip install google-generativeai python-dotenv
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

Create a `.env` file in `backend/` directory:

```bash
# Copy the example file
copy .env.example .env
```

Edit `.env` and add your API key:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Replace with your key

# LLM Provider Selection
LLM_PROVIDER=gemini  # Options: 'gemini' or 'ollama'

# Gemini Model Selection
GEMINI_MODEL=gemini-1.5-flash  # Options: 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Step 4: Model Selection Guide

### 🚀 gemini-1.5-flash (Recommended)
- **Speed**: Fastest (~1-2 seconds per request)
- **Cost**: Free tier - 15 RPM / 1500 RPD
- **Quality**: Excellent for structured outputs
- **Use Case**: Production, real-time suggestions
- **Best for**: This project (fast, accurate, free tier sufficient)

### 💎 gemini-1.5-pro
- **Speed**: Slower (~3-5 seconds per request)
- **Cost**: Free tier - 2 RPM / 50 RPD (more limited)
- **Quality**: Best quality, deeper analysis
- **Use Case**: Critical applications needing highest accuracy
- **Best for**: Complex feedback requiring nuanced understanding

### 📦 gemini-1.0-pro (Legacy)
- **Speed**: Medium
- **Cost**: Free tier available
- **Quality**: Good but older model
- **Use Case**: Backward compatibility
- **Best for**: Not recommended unless specific requirements

**Recommendation**: Start with `gemini-1.5-flash` - it's fast, free, and perfect for this application.

---

## Step 5: Verify Installation

Create `test_gemini.py`:

```python
import os
from dotenv import load_dotenv
from gemini_suggestions import GeminiSuggestionEngine

# Load environment variables
load_dotenv()

# Test Gemini configuration
print("🧪 Testing Gemini API...")

try:
    engine = GeminiSuggestionEngine()
    print(f"✅ Gemini engine initialized with model: {engine.model_name}")
    
    # Test generation
    result = engine.generate_suggestion(
        feedback_text="Student shows good understanding but struggles with practical application",
        sentiment_label="Neutral",
        domain="engineering"
    )
    
    if result:
        print("✅ Suggestion generated successfully!")
        print(f"   Title: {result['title']}")
        print(f"   Urgency: {result['urgency']}")
        print(f"   Actions: {len(result['immediate_actions'])} items")
    else:
        print("❌ Failed to generate suggestion")
        
except Exception as e:
    print(f"❌ Error: {e}")
```

Run the test:
```bash
python test_gemini.py
```

Expected output:
```
🧪 Testing Gemini API...
✅ Gemini engine initialized with model: gemini-1.5-flash
🚀 Gemini engine initialized with model: gemini-1.5-flash
🤖 Calling Gemini API for: Student shows good understanding but struggles wi...
📥 Gemini response length: 892 characters
✅ Successfully parsed Gemini suggestion
✅ Suggestion generated successfully!
   Title: Bridge Theory-Practice Gap Through Applied Projects
   Urgency: medium
   Actions: 3 items
```

---

## Step 6: Switch Provider in Application

The application automatically detects the provider from `LLM_PROVIDER` in `.env`:

**Use Gemini (Cloud)**:
```env
LLM_PROVIDER=gemini
```

**Use Ollama (Local)**:
```env
LLM_PROVIDER=ollama
```

**Auto-detect** (Gemini first, fallback to Ollama):
```env
# Leave LLM_PROVIDER unset or comment it out
# LLM_PROVIDER=
```

---

## Step 7: Test in Application

1. Start the backend:
```bash
cd backend
python app.py
```

2. Submit feedback via frontend or API:
```bash
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d "{
    \"feedback\": \"Shows strong analytical skills but needs more teamwork\",
    \"domain\": \"engineering\"
  }"
```

3. Check backend logs for:
```
✅ Gemini API configured successfully
🚀 Gemini engine initialized with model: gemini-1.5-flash
🤖 Calling Gemini API for: Shows strong analytical skills but needs more...
✅ Suggestion generated via Gemini API
```

---

## API Limits and Pricing

### Free Tier (Sufficient for Development)
- **Gemini 1.5 Flash**: 15 requests/minute, 1,500 requests/day
- **Gemini 1.5 Pro**: 2 requests/minute, 50 requests/day
- **No credit card required**

### Rate Limit Handling
If you exceed rate limits, the application automatically falls back to:
1. Ollama (if configured and running)
2. Basic rule-based suggestions

### Monitoring Usage
Check your usage at: https://aistudio.google.com/app/apikey

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution**: 
- Verify `.env` file exists in `backend/` directory
- Check `GEMINI_API_KEY` is set correctly
- Restart the Flask server

### Issue: "google-generativeai not installed"
**Solution**:
```bash
pip install google-generativeai
```

### Issue: "API key invalid"
**Solution**:
- Visit https://aistudio.google.com/apikey
- Generate a new API key
- Update `.env` with new key

### Issue: "Rate limit exceeded"
**Solution**:
- Wait 1 minute (for minute limit) or 24 hours (for daily limit)
- Switch to `gemini-1.5-flash` (higher limits)
- Or fall back to Ollama: `LLM_PROVIDER=ollama`

### Issue: "Timeout/Connection error"
**Solution**:
- Check internet connection
- Verify firewall isn't blocking aistudio.google.com
- Try again (transient network issues)

---

## Comparison: Gemini vs Ollama

| Feature | Gemini API | Ollama (Local) |
|---------|-----------|----------------|
| Setup | ✅ Simple (API key) | ⚠️ Complex (3.3GB download, server) |
| Speed | 🚀 Fast (1-2s) | ⏳ Medium (2-4s with GPU) |
| Quality | 💎 Excellent | ✅ Good |
| Offline | ❌ No | ✅ Yes |
| Cost | 💰 Free tier | ✅ Free (local compute) |
| Scalability | 🌐 Cloud (unlimited) | ⚠️ Limited by GPU |
| Maintenance | ✅ Zero | ⚠️ Manual updates |
| Privacy | ⚠️ Data sent to Google | ✅ Fully local |

**Recommendation**: 
- **Development/Demo**: Use Gemini (easier setup, faster)
- **Production (privacy-critical)**: Use Ollama (data stays local)
- **Production (public app)**: Use Gemini (better scalability)

---

## Best Practices

### 1. API Key Security
```bash
# ✅ Good - Use environment variables
GEMINI_API_KEY=AIza...

# ❌ Bad - Never hardcode in code
api_key = "AIzaSyXXXX..."  # DON'T DO THIS!
```

### 2. Error Handling
The application automatically handles:
- API failures → Falls back to Ollama
- Rate limits → Returns error message
- Invalid responses → Uses basic suggestions

### 3. Prompt Engineering
Prompts are optimized in `gemini_suggestions.py`:
- Domain-specific instructions
- Structured JSON output
- Exactly 3 items per section
- Clear, actionable suggestions

### 4. Monitoring
Enable logging to track:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Logs show:
- Which provider is used (Gemini/Ollama)
- Response times
- Errors and fallbacks

---

## Next Steps

1. ✅ Test Gemini with your API key
2. ✅ Compare quality with Ollama
3. ✅ Monitor rate limits during testing
4. ✅ Deploy with environment variables
5. 📖 Read [Advanced Configuration](./ADVANCED_GEMINI_CONFIG.md) (optional)

---

## Support

**Issues?**
1. Check logs: `backend/app.log`
2. Verify API key: https://aistudio.google.com/apikey
3. Test with `test_gemini.py` script
4. Check Google AI Studio status: https://status.cloud.google.com/

**Questions?**
- Google AI Studio Docs: https://ai.google.dev/docs
- Gemini API Reference: https://ai.google.dev/api/python/google/generativeai

---

**Happy coding! 🚀**
