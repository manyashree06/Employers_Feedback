# Quick Start Guide: Running Your App with Ollama

## 🚀 First Time Setup (5 minutes)

### Step 1: Install Ollama
Download from: https://ollama.ai/download
- Windows: Run the installer
- Restart your terminal after installation

### Step 2: Pull the Model
```powershell
ollama pull gemma3
```
This downloads ~2GB, one-time only.

### Step 3: Install Backend Dependencies
```powershell
cd "c:\Users\nites\OneDrive\Desktop\major project\backend"
python -m pip install -r requirements.txt
```
If that doesn't work, try:
```powershell
py -m pip install -r requirements.txt
```

## 🎯 Daily Usage (Every Time You Run)

### Terminal 1: Start Ollama Server (if not already running)
```powershell
ollama serve
```
**Note:** If you get an error like "bind: Only one usage of each socket address", Ollama is already running! Skip this step.

To check if Ollama is running:
```powershell
ollama list
```
If this works, Ollama is already running and you can proceed to Terminal 2.

### Terminal 2: Start Backend
```powershell
cd "c:\Users\nites\OneDrive\Desktop\major project\backend"
python app.py
```
Backend runs on http://localhost:5000

### Terminal 3: Start Frontend
```powershell
cd "c:\Users\nites\OneDrive\Desktop\major project\frontend"
npm start
```
Frontend opens at http://localhost:3000

## ✅ Verify It's Working

1. Open http://localhost:3000
2. Submit feedback like: "The onboarding was confusing and my manager didn't explain expectations."
3. You should see detailed AI-generated suggestions with:
   - Sentiment analysis
   - Key aspects identified
   - Emotional tone
   - Actionable steps
   - Priority levels

## 🔍 Check Ollama Status

```powershell
ollama list    # See installed models
ollama ps      # See running models
```

## 🐛 Troubleshooting

### pip not recognized
- Use `python -m pip` instead of just `pip`
- Or try `py -m pip` if you have Python launcher installed
- Verify Python is installed: `python --version` or `py --version`

### Ollama not found
- Make sure you installed Ollama and restarted your terminal
- Try: `ollama --version`

### Model not pulling
- Check internet connection
- Try: `ollama pull gemma3` again

### "bind: Only one usage of each socket address" error
- **Good news!** This means Ollama is already running
- You don't need to run `ollama serve` again
- Just verify with `ollama list` and proceed to start your backend

### Backend errors about Ollama
- Check if Ollama is running: `ollama list`
- If not running, start it: `ollama serve` (in a separate terminal)
- The app will automatically fall back to rule-based suggestions if Ollama isn't available

### App still uses old suggestions
- Stop and restart the backend (Ctrl+C, then `python app.py` again)
- Clear browser cache and refresh

## 💡 Pro Tips

1. **Keep Ollama running**: Once `ollama serve` is started, you can keep it running all day
2. **Test without Ollama**: Just don't run `ollama serve` - the app works fine with rule-based suggestions
3. **Check logs**: Backend prints "Ollama raw response" when using the LLM
4. **Multiple domains**: Try different domains (engineering, commerce, science, arts, medical, law, management)

## 📊 Run Tests

```powershell
cd backend
pytest tests/test_ollama_integration.py -v
```

## 🎨 Expected Behavior

**With Ollama running:**
- Feedback analysis takes 1-3 seconds
- You get structured JSON responses with detailed insights
- Response type shows "llm" in the API

**Without Ollama:**
- Instant responses (< 100ms)
- Rule-based domain-specific suggestions
- Response type shows "basic" or "advanced" in the API

## 🔒 Privacy Note

Ollama runs **100% locally** on your machine. No data is sent to external servers. The gemma3 model and all processing happen offline.
