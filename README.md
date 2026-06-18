## Employer Feedback Sentiment Analysis — Full Stack App

A full-stack web application to collect employer feedback, analyze sentiment using AI (Transformer + LLM), and visualize insights. Features hybrid sentiment analysis with DistilBERT, Ollama LLM integration, and domain-specific suggestions.

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- **[Quick Start Guide](docs/QUICK_START_OLLAMA.md)** - Get started quickly with setup instructions
- **[Hybrid Sentiment Analysis](docs/HYBRID_SENTIMENT_ANALYSIS.md)** - Understanding the AI sentiment system
- **[Ollama Integration](docs/OLLAMA_INTEGRATION_SUMMARY.md)** - LLM setup and configuration
- **[Performance Guide](docs/PERFORMANCE_OPTIMIZATIONS.md)** - Optimization strategies
- **[More Documentation](docs/)** - See all available documentation

## 🚀 Quick Start
### Prerequisites
- Python 3.13+
- Node.js 18+
- Ollama (recommended for LLM features)
- GPU (optional, for faster sentiment analysis)

### Backend Setup (Flask)
1. Create and activate a virtual environment
```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. (Optional) Configure PostgreSQL
- Create a database (example): `feedback_db`
- Set env var:
```bash
$env:DATABASE_URL = "postgresql+psycopg2://postgres:yourpassword@localhost:5432/feedback_db"
```
If not set, the app will use a local SQLite file `app.db`.

4. Initialize TextBlob corpora (first run only)
```bash
python -m textblob.download_corpora
```
5. Run the server
```bash
python app.py
# Server at http://localhost:5000
```

### Frontend Setup (React + Tailwind)
1. Install dependencies
```bash
cd ../frontend
npm install
```
2. Run the dev server
```bash
npm start
# App at http://localhost:3000 (talks to backend at http://localhost:5000)
```

### API Endpoints
- POST `/api/feedback` — body: `{ "feedback_text": string }` → returns saved feedback with sentiment
- GET `/api/feedback` — returns all feedback entries
- GET `/api/dashboard_stats` — returns totals, avg sentiment score, counts per label, and daily timeseries

### Project Structure
```
major project/
├── backend/
│   ├── app.py                    # Flask API server
│   ├── requirements.txt          # Python dependencies
│   ├── train_model.py           # ML model training script
│   ├── employer_feedback_bangalore.xlsx  # Dataset
│   └── model/
│       └── sentiment_model.joblib # Trained ML model
├── frontend/
│   ├── package.json             # Node.js dependencies
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.js
│   │   ├── index.css
│   │   ├── App.js
│   │   └── components/
│   │       ├── FeedbackForm.js
│   │       ├── FeedbackList.js
│   │       ├── Dashboard.js
│   │       ├── DistributionChart.js
│   │       └── TrendChart.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
```

### Notes
- CORS is enabled on the backend to allow the React dev server.
- For production, set `DATABASE_URL` to a managed PostgreSQL instance and use `npm run build` to produce a static build.

## Domain-Specific Suggestion Feature
✅ Commerce: Excel, financial modeling, CFA/CPA prep, business analysis
✅ Science: Research methodology, lab techniques, statistical analysis, publication
✅ Arts: Portfolio development, exhibitions, creative agencies, artistic identity
✅ Medical: Clinical skills, patient communication, OSCE practice, SOAP notes
✅ Law: Legal research databases, citation formats, case briefs, moot court
✅ Management: Leadership, team delegation, strategic planning, conflict resolution

## Ollama LLM Integration (Optional but Recommended)

The application now uses **Ollama** with the **gemma3** model to generate intelligent, structured feedback suggestions. Ollama runs locally on your machine, providing fast, private AI-powered analysis.

### Setup Ollama (One-time)

1. **Install Ollama** from https://ollama.ai/download
   - For Windows: Download and run the installer
   - For Mac: `brew install ollama`
   - For Linux: `curl https://ollama.ai/install.sh | sh`

2. **Pull the gemma3 model** (one-time download, ~2GB):
   ```bash
   ollama pull gemma3
   ```

### Running with Ollama

**Option 1: Automatic (Recommended)**
Simply start Ollama before running your backend:
```bash
# In a separate terminal, start Ollama server
ollama serve

# Then run your backend as usual (in another terminal)
cd backend
python app.py
```

**Option 2: Without Ollama**
The app works fine without Ollama! It automatically falls back to rule-based suggestions if Ollama isn't running.

### How It Works

- **When Ollama is running**: The advanced suggestion engine uses the gemma3 LLM to analyze feedback and generate:
  - Detailed sentiment analysis (positive/neutral/negative with confidence scores)
  - Key aspects identified (onboarding, pay, communication, workload, manager)
  - Emotional tone detection (anger, sadness, joy, fear, neutral)
  - Actionable suggestions with priorities (1-3)
  - Personalized reply messages
  
- **When Ollama is not available**: Automatically falls back to the existing rule-based suggestion system using domain-specific heuristics

### Testing the Integration

Run the test suite to verify everything works:
```bash
cd backend
pytest tests/test_ollama_integration.py -v
```

### Checking Ollama Status

To verify Ollama is running and gemma3 is available:
```bash
ollama list          # Shows installed models
ollama ps            # Shows running models
```
