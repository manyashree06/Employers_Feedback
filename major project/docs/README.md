# Documentation

This folder contains comprehensive documentation for the Student Feedback Analysis System.

## 📚 Documentation Files

### Project Overview
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete project structure and file organization

### Quick Start
- **[QUICK_START_OLLAMA.md](QUICK_START_OLLAMA.md)** - Getting started guide for setting up Ollama (local LLM)
- **[GEMINI_API_SETUP.md](GEMINI_API_SETUP.md)** - Setting up Google Gemini API (cloud LLM, recommended)

### Core Features
- **[HYBRID_SENTIMENT_ANALYSIS.md](HYBRID_SENTIMENT_ANALYSIS.md)** - Complete guide to the hybrid sentiment analysis system (Transformer + Keywords)
- **[OLLAMA_INTEGRATION_SUMMARY.md](OLLAMA_INTEGRATION_SUMMARY.md)** - Ollama LLM integration details and configuration

### Performance & Optimization
- **[PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)** - Performance improvements and optimization strategies

### Technical Details
- **[BACKEND_FIXES_APPLIED.md](BACKEND_FIXES_APPLIED.md)** - List of backend fixes and improvements
- **[SENTIMENT_INTEGRATION_VERIFICATION.md](SENTIMENT_INTEGRATION_VERIFICATION.md)** - Sentiment analysis verification and testing

## 🎯 Key Features Documented

### Sentiment Analysis
- **Transformer-first approach** using DistilBERT (90%+ accuracy)
- **Mixed/Balanced feedback detection** (handles "but", "however", "without")
- **Keyword-based fallback** for domain-specific terms
- **GPU acceleration** support (RTX 3050 tested)

### LLM Integration
- **Google Gemini API** (cloud-based, recommended)
  - No local setup required
  - Faster performance
  - gemini-1.5-flash model (15 RPM free tier)
- **Ollama with Gemma3 model** (local, privacy-focused)
  - 3.3GB model download
  - GPU-accelerated inference
- **Domain-aware suggestions** (Engineering, Medical, Law, Management, etc.)
- **Optimized generation** (structured JSON output)
- **3-item structure** for faster generation
- **Automatic fallback** (Gemini → Ollama → Basic)

### Performance
- **Average sentiment analysis**: ~350ms per feedback
- **Fast path for "but/however"**: ~0ms (instant return)
- **100% accuracy** on test cases
- **GPU-accelerated** transformer inference

## 📖 Reading Order

For new developers:
1. Start with **GEMINI_API_SETUP.md** (easiest) or **QUICK_START_OLLAMA.md** (local/privacy)
2. Read **HYBRID_SENTIMENT_ANALYSIS.md** to understand sentiment detection
3. Check **OLLAMA_INTEGRATION_SUMMARY.md** for Ollama-specific details (if using local LLM)
4. Review **PERFORMANCE_OPTIMIZATIONS.md** for optimization strategies

## 🚀 Quick Setup (5 minutes)

### Option 1: Gemini API (Recommended - Easiest)
```bash
# 1. Get API key from https://aistudio.google.com/apikey
# 2. Create .env file
echo "GEMINI_API_KEY=your_key_here" > backend/.env
echo "LLM_PROVIDER=gemini" >> backend/.env

# 3. Install and run
cd backend
pip install -r requirements.txt
python test_gemini.py  # Verify setup
python app.py          # Start server
```

### Option 2: Ollama (Local/Privacy-Focused)
See **QUICK_START_OLLAMA.md** for detailed local setup instructions.

## 🔧 Technical Stack

- **Frontend**: React, TailwindCSS, Chart.js
- **Backend**: Python 3.13, Flask, SQLAlchemy
- **LLM**: Ollama (Gemma3 model)
- **Sentiment**: Transformers (DistilBERT) + Custom keywords
- **Database**: SQLite
- **PDF**: ReportLab

## 📝 Last Updated

October 25, 2025
