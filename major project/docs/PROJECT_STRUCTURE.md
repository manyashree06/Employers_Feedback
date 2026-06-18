# Project Structure

```
major project/
│
├── 📁 backend/                          # Flask Backend Server
│   ├── app.py                          # Main Flask application
│   ├── advanced_suggestions.py         # Advanced suggestion engine with Ollama
│   ├── sentiment_analyzer.py           # Hybrid sentiment analysis (Transformer + Keywords)
│   ├── prompt_templates.py             # LLM prompt templates
│   ├── requirements.txt                # Python dependencies
│   ├── analyze_results.py              # Results analysis script
│   ├── ollama_benchmark.py             # Ollama performance benchmarking
│   │
│   ├── 📁 instance/                    # SQLite database folder
│   │   └── app.db                      # SQLite database file
│   │
│   ├── 📁 tests/                       # Unit tests
│   │   └── test_ollama_integration.py  # Ollama integration tests
│   │
│   └── 📁 .venv/                       # Python virtual environment (not in git)
│
├── 📁 frontend/                         # React Frontend Application
│   ├── package.json                    # Node.js dependencies
│   ├── tailwind.config.js              # Tailwind CSS configuration
│   ├── postcss.config.js               # PostCSS configuration
│   │
│   ├── 📁 public/                      # Static assets
│   │   └── index.html                  # HTML template
│   │
│   └── 📁 src/                         # React source code
│       ├── index.js                    # React entry point
│       ├── index.css                   # Global styles
│       ├── App.js                      # Main App component
│       │
│       ├── 📁 components/              # React components
│       │   ├── Dashboard.js            # Main dashboard
│       │   ├── FeedbackForm.js         # Feedback submission form
│       │   ├── FeedbackList.js         # Feedback list view
│       │   ├── SuggestionDisplay.js    # AI suggestion display
│       │   ├── DistributionChart.js    # Sentiment distribution chart
│       │   ├── TrendChart.js           # Trend analysis chart
│       │   │
│       │   └── 📁 common/              # Shared components
│       │       ├── AuroraBackground.js # Animated background
│       │       └── LoadingComponents.js # Loading indicators
│       │
│       └── 📁 context/                 # React Context
│           └── DataContext.js          # Global state management
│
├── 📁 docs/                             # 📚 DOCUMENTATION
│   ├── README.md                       # Documentation index
│   ├── QUICK_START_OLLAMA.md           # Quick start guide
│   ├── HYBRID_SENTIMENT_ANALYSIS.md    # Sentiment analysis details
│   ├── OLLAMA_INTEGRATION_SUMMARY.md   # Ollama LLM integration
│   ├── PERFORMANCE_OPTIMIZATIONS.md    # Performance guide
│   ├── BACKEND_FIXES_APPLIED.md        # Backend fixes log
│   └── SENTIMENT_INTEGRATION_VERIFICATION.md # Testing documentation
│
├── 📁 .vscode/                          # VS Code settings (optional)
│
├── .gitignore                          # Git ignore rules
├── README.md                           # Main project README
└── employer_feedback_bangalore.xlsx    # Sample dataset

```

## 🎯 Key Files

### Backend Core
- **`app.py`** - Flask REST API server (routes, database models)
- **`sentiment_analyzer.py`** - Hybrid sentiment analysis (DistilBERT transformer + keyword detection)
- **`advanced_suggestions.py`** - AI suggestion generation using Ollama LLM
- **`prompt_templates.py`** - Structured prompts for LLM generation

### Frontend Core
- **`App.js`** - Main React application with routing
- **`Dashboard.js`** - Analytics dashboard with charts
- **`FeedbackForm.js`** - Feedback submission with domain selection
- **`SuggestionDisplay.js`** - AI-generated suggestions display

### Documentation
- **`docs/`** - All project documentation organized in one place
- **`README.md`** - Main project overview and setup instructions

## 📦 Dependencies

### Backend (Python)
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Transformers** - Hugging Face transformers (DistilBERT)
- **PyTorch** - Deep learning framework
- **TextBlob** - Natural language processing
- **ReportLab** - PDF generation
- **Ollama** - Local LLM inference

### Frontend (Node.js)
- **React** - UI framework
- **TailwindCSS** - Utility-first CSS
- **Chart.js** - Data visualization
- **Axios** - HTTP client
- **React Router** - Navigation

## 🗄️ Database Structure

### Feedback Table
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    feedback_text TEXT NOT NULL,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(10),  -- 'Positive', 'Negative', 'Neutral'
    domain VARCHAR(50),           -- 'engineering', 'medical', 'law', etc.
    timestamp DATETIME
);
```

## 🚀 Features

✅ **Hybrid Sentiment Analysis** (Transformer + Keywords + Mixed detection)
✅ **Domain-Specific Suggestions** (8 domains: Engineering, Medical, Law, etc.)
✅ **Ollama LLM Integration** (Local AI with Gemma3 model)
✅ **GPU Acceleration** (CUDA support for faster inference)
✅ **Mixed Feedback Detection** ("but", "however" patterns → Neutral)
✅ **Real-time Dashboard** (Charts, trends, statistics)
✅ **PDF Report Generation** (Comprehensive feedback reports)
✅ **Dark Mode UI** (Modern gradient design with animations)

## 📊 Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React     │ HTTP    │    Flask     │ Python  │   Ollama    │
│  Frontend   │ ←────→  │   Backend    │ ←────→  │  LLM API    │
│  (Port 3000)│         │ (Port 5000)  │         │ (Port 11434)│
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               │ SQLAlchemy
                               ↓
                        ┌──────────────┐
                        │    SQLite    │
                        │   Database   │
                        └──────────────┘
```

## 🔍 Data Flow

1. User submits feedback → **FeedbackForm**
2. Frontend sends POST request → **Flask API** (`/api/feedback`)
3. Backend analyzes sentiment → **sentiment_analyzer.py** (Transformer model)
4. Backend generates suggestions → **advanced_suggestions.py** (Ollama LLM)
5. Store in database → **SQLite** (via SQLAlchemy)
6. Return response → **Frontend** displays results
7. Dashboard updates → **Real-time charts and stats**

## 📝 Notes

- **Test files removed** - All test files cleaned up for production
- **Documentation organized** - All `.md` files moved to `docs/` folder
- **Clean structure** - Minimal files in root directory
- **Ready for deployment** - Organized and documented codebase
