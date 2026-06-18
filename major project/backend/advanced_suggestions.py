import re
import json
import os
import random
import hashlib
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pandas as pd
from textblob import TextBlob
from sentiment_analyzer import analyze_sentiment, get_sentiment_analyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from prompt_templates import SUGGESTION_PROMPT, QUALITY_CHECK

# Optional Ollama client for LLM-powered suggestions
try:
    import ollama

    _OLLAMA_AVAILABLE = True
    # Use faster, smaller model for better performance
    # Options: "phi3:mini" (2.2GB, fastest), "gemma3" (3.3GB, balanced), "llama3" (4.7GB, best quality)
    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL", "gemma3"
    )  # Default to gemma3 for better JSON reliability
    print(
        f"✅ Ollama module imported successfully - LLM suggestions enabled with model: {OLLAMA_MODEL}"
    )
except Exception as e:
    ollama = None
    _OLLAMA_AVAILABLE = False
    OLLAMA_MODEL = None
    print(f"⚠️  Ollama not available: {e} - Using rule-based suggestions only")


class AdvancedSuggestionEngine:
    def __init__(self, db_session=None):
        self.suggestion_db = self._load_suggestion_database()
        self.domain_specific_db = self._load_domain_specific_database()
        self.keywords_cache = {}
        self.db_session = db_session
        self.vectorizer = TfidfVectorizer(
            max_features=1500,  # Increased for better context capture
            ngram_range=(1, 4),  # Extended to catch more phrases
            stop_words="english",
            lowercase=True,
            min_df=2,  # Requires terms to appear at least twice
        )
        self._initialize_vectorizer()
        self.feedback_history = []
        self.last_db_update = 0
        self.suggestion_variations = self._load_suggestion_variations()

        # Enhanced LLM response caching
        self.llm_cache = {}
        self.cache_max_size = 200  # Increased cache size
        self.cache_ttl = 3600  # Cache TTL in seconds

        # Configure Ollama for optimal response quality
        if _OLLAMA_AVAILABLE:
            self.ollama_params = {
                "temperature": 0.7,  # Balanced creativity
                "top_p": 0.9,  # More focused sampling
                "max_tokens": 1000,  # Longer responses
                "presence_penalty": 0.3,  # Encourage diversity
                "frequency_penalty": 0.3,  # Reduce repetition
            }
        self.cache_max_size = 100  # Limit cache size

    def _load_suggestion_database(self) -> Dict:
        """Load comprehensive suggestion database with specific improvement areas for students"""
        return {
            "communication": {
                "keywords": [
                    "communication",
                    "communicate",
                    "presentation",
                    "speak",
                    "speaking",
                    "explain",
                    "clarify",
                    "unclear",
                    "confusing",
                    "articulate",
                    "express",
                    "discussion",
                    "feedback",
                    "verbal",
                    "answer",
                    "response",
                    "question",
                    "interview",
                    "confident",
                    "nervous",
                    "fluency",
                ],
                "suggestions": {
                    "beginner": {
                        "title": "Interview Communication Skills Development",
                        "immediate_actions": [
                            "Practice the 'STAR' method (Situation, Task, Action, Result) for answering behavioral questions",
                            "Record yourself answering common interview questions and review your delivery",
                            "Join a study group or mock interview sessions with peers for practice",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Practice speaking clearly at a moderate pace with strategic pauses",
                            "Week 3-4: Work on structuring your answers - introduction, main points, conclusion",
                            "Week 5-6: Improve non-verbal cues - maintain eye contact and confident posture",
                        ],
                        "resources": [
                            "Platform: InterviewBit or Pramp for mock interview practice",
                            "Course: Coursera's 'Successful Interview Techniques'",
                            "Tool: Practice with video recording apps to review your responses",
                        ],
                    },
                    "intermediate": {
                        "title": "Advanced Interview Communication Excellence",
                        "immediate_actions": [
                            "Develop concise elevator pitches for your projects and achievements",
                            "Practice explaining technical concepts in simple, non-technical language",
                            "Prepare examples demonstrating your problem-solving and analytical abilities",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Master articulating your thought process while solving problems",
                            "Week 3-4: Practice handling challenging or unexpected questions gracefully",
                            "Week 5-6: Develop confidence in discussing your strengths and areas for growth",
                        ],
                        "resources": [
                            "Book: 'Cracking the Coding Interview' for technical communication",
                            "Platform: LeetCode Discuss to learn how others explain solutions",
                            "Practice: Conduct peer mock interviews weekly with detailed feedback",
                        ],
                    },
                },
            },
            "preparation": {
                "keywords": [
                    "preparation",
                    "prepare",
                    "unprepared",
                    "practice",
                    "study",
                    "research",
                    "knowledge",
                    "understanding",
                    "concepts",
                    "fundamentals",
                    "basics",
                    "ready",
                    "homework",
                    "revision",
                    "learning",
                    "grasp",
                    "familiar",
                    "background",
                ],
                "suggestions": {
                    "beginner": {
                        "title": "Interview Preparation Foundation",
                        "immediate_actions": [
                            "Create a list of common interview topics and rate your confidence in each area",
                            "Dedicate 2-3 hours daily to focused preparation on weak areas",
                            "Research the company thoroughly - products, culture, recent news, and job requirements",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Master fundamental concepts in your field - core data structures, algorithms, or domain basics",
                            "Week 3-4: Practice 5-10 problems or questions daily with increasing difficulty",
                            "Week 5-6: Conduct mock interviews and review commonly asked questions in your domain",
                        ],
                        "resources": [
                            "Platform: GeeksforGeeks or LeetCode for technical preparation",
                            "Resource: Company Glassdoor reviews for interview-specific insights",
                            "Tool: Notion or OneNote to organize your preparation notes and progress",
                        ],
                    },
                    "intermediate": {
                        "title": "Advanced Interview Readiness Strategy",
                        "immediate_actions": [
                            "Build a portfolio of 3-5 projects that demonstrate your skills and problem-solving ability",
                            "Prepare detailed stories about your academic projects, internships, and achievements",
                            "Study the job description deeply and align your experiences with required skills",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Deep dive into advanced topics relevant to your target role",
                            "Week 3-4: Practice system design concepts or case studies relevant to your field",
                            "Week 5-6: Refine your personal narrative - why this role, why this company, why you",
                        ],
                        "resources": [
                            "Book: Domain-specific interview guides (e.g., 'Cracking the PM Interview', 'Elements of Programming Interviews')",
                            "Platform: YouTube channels featuring mock interviews and expert tips",
                            "Practice: Schedule weekly mock interviews with seniors or mentors",
                        ],
                    },
                },
            },
            "technical_skills": {
                "keywords": [
                    "technical",
                    "coding",
                    "programming",
                    "algorithm",
                    "data structure",
                    "logic",
                    "problem solving",
                    "debugging",
                    "syntax",
                    "code",
                    "implementation",
                    "solution",
                    "approach",
                    "complexity",
                    "optimization",
                    "error",
                    "concept",
                ],
                "suggestions": {
                    "beginner": {
                        "title": "Technical Skills Enhancement for Interviews",
                        "immediate_actions": [
                            "Start with fundamentals - master basic data structures (arrays, linked lists, stacks, queues, trees)",
                            "Practice 3-5 coding problems daily, starting from easy to medium difficulty",
                            "Learn to explain your thought process while solving problems out loud",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Build strong foundation in one programming language and its syntax",
                            "Week 3-4: Focus on common algorithms - sorting, searching, recursion, dynamic programming basics",
                            "Week 5-6: Practice time and space complexity analysis for every solution you write",
                        ],
                        "resources": [
                            "Platform: LeetCode, HackerRank, or CodeChef for structured practice",
                            "Book: 'Introduction to Algorithms' (CLRS) or 'Cracking the Coding Interview'",
                            "YouTube: Channels like NeetCode, Abdul Bari for concept clarity",
                        ],
                    },
                    "intermediate": {
                        "title": "Advanced Problem-Solving Mastery",
                        "immediate_actions": [
                            "Tackle medium to hard problems focusing on optimal solutions",
                            "Study and implement common patterns - sliding window, two pointers, BFS/DFS, backtracking",
                            "Review your past solutions and optimize them for better time/space complexity",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Master advanced topics like graphs, heaps, tries, and segment trees",
                            "Week 3-4: Practice system design basics and understand scalability concepts",
                            "Week 5-6: Work on domain-specific problems relevant to your target companies",
                        ],
                        "resources": [
                            "Platform: Codeforces, AtCoder for competitive programming practice",
                            "Book: 'Elements of Programming Interviews' in your preferred language",
                            "Resource: Company-specific interview preparation guides on LeetCode",
                        ],
                    },
                },
            },
            "confidence": {
                "keywords": [
                    "confidence",
                    "nervous",
                    "anxiety",
                    "stress",
                    "worried",
                    "uncertain",
                    "hesitant",
                    "doubt",
                    "fear",
                    "pressure",
                    "comfortable",
                    "calm",
                    "composed",
                    "self-doubt",
                    "intimidated",
                    "awkward",
                    "shy",
                ],
                "suggestions": {
                    "beginner": {
                        "title": "Building Interview Confidence",
                        "immediate_actions": [
                            "Practice positive self-talk and visualization - imagine yourself succeeding in the interview",
                            "Prepare thoroughly to build natural confidence in your knowledge and abilities",
                            "Start with mock interviews in comfortable settings with friends or family",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Practice power poses and breathing exercises to manage nervousness",
                            "Week 3-4: Record yourself answering questions and watch to build self-awareness",
                            "Week 5-6: Gradually increase pressure - mock interviews with strangers or seniors",
                        ],
                        "resources": [
                            "Book: 'Presence' by Amy Cuddy about building confidence through body language",
                            "Technique: Box breathing (4-4-4-4) before interviews to calm nerves",
                            "App: Calm or Headspace for meditation and anxiety management",
                        ],
                    },
                    "intermediate": {
                        "title": "Advanced Interview Composure",
                        "immediate_actions": [
                            "Develop a pre-interview routine that puts you in peak mental state",
                            "Learn to reframe nervousness as excitement and channel that energy positively",
                            "Practice handling difficult questions without losing composure",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Master techniques to pause, think, and respond thoughtfully under pressure",
                            "Week 3-4: Build confidence in saying 'I don't know' gracefully and showing learning ability",
                            "Week 5-6: Develop your personal brand and authentic interview presence",
                        ],
                        "resources": [
                            "Course: Interview confidence workshops or career counseling sessions",
                            "Practice: Join interview preparation groups or clubs at your institution",
                            "Resource: Watch successful interview examples to model effective behaviors",
                        ],
                    },
                },
            },
            "projects_experience": {
                "keywords": [
                    "project",
                    "experience",
                    "portfolio",
                    "work",
                    "internship",
                    "achievement",
                    "accomplishment",
                    "build",
                    "create",
                    "develop",
                    "real world",
                    "practical",
                    "hands on",
                    "showcase",
                    "demonstrate",
                ],
                "suggestions": {
                    "beginner": {
                        "title": "Building Strong Project Portfolio",
                        "immediate_actions": [
                            "Start with 2-3 well-documented projects that solve real problems",
                            "Ensure each project demonstrates different skills and technologies",
                            "Create detailed README files explaining your project's purpose, tech stack, and your contributions",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Complete one personal project from scratch - even a simple one done well is valuable",
                            "Week 3-4: Add projects to GitHub with clean code, comments, and version control",
                            "Week 5-6: Prepare a compelling narrative for each project - challenges faced and solutions implemented",
                        ],
                        "resources": [
                            "Platform: GitHub to showcase your code and maintain a professional profile",
                            "Ideas: Build projects based on daily problems - calculator, to-do app, weather app, etc.",
                            "Tool: Canva or similar for creating project demos and presentations",
                        ],
                    },
                    "intermediate": {
                        "title": "Advanced Portfolio Development",
                        "immediate_actions": [
                            "Build 1-2 complex projects that demonstrate system design and scalability thinking",
                            "Contribute to open-source projects to show collaboration and code quality skills",
                            "Document your learning journey and technical decisions through blogs or tech talks",
                        ],
                        "weekly_goals": [
                            "Week 1-2: Add features like authentication, databases, APIs to make projects production-ready",
                            "Week 3-4: Deploy your projects online so interviewers can see live demos",
                            "Week 5-6: Quantify your project impact - performance metrics, users, problem solved",
                        ],
                        "resources": [
                            "Platform: Deploy on Heroku, Vercel, or AWS to show deployment skills",
                            "Resource: Study how top students present their portfolios on LinkedIn",
                            "Practice: Present your projects to peers and refine your explanation",
                        ],
                    },
                },
            },
        }

    def _load_domain_specific_database(self) -> Dict:
        """Load domain-specific suggestion categories and keywords for different student domains"""
        return {
            "commerce": {
                "financial_analysis": {
                    "keywords": [
                        "accounting",
                        "finance",
                        "financial",
                        "balance sheet",
                        "income statement",
                        "ratio",
                        "analysis",
                        "excel",
                        "spreadsheet",
                        "calculation",
                        "numbers",
                        "profit",
                        "loss",
                        "revenue",
                        "cost",
                        "budget",
                        "audit",
                        "tax",
                        "bookkeeping",
                        "ledger",
                        "journal entry",
                        "cash flow",
                        "working capital",
                        "return on investment",
                        "roi",
                        "asset",
                        "liability",
                        "equity",
                        "depreciation",
                        "amortization",
                        "variance analysis",
                        "cost accounting",
                        "managerial accounting",
                        "quickbooks",
                        "tally",
                        "sap",
                        "financial statements",
                        "trial balance",
                        "general ledger",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Financial Analysis Skills Foundation",
                            "immediate_actions": [
                                "Master Excel basics: pivot tables, VLOOKUP, and essential financial formulas",
                                "Practice creating balance sheets and income statements from sample data",
                                "Learn fundamental financial ratios: liquidity, profitability, and efficiency ratios",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete Excel for Finance courses on Coursera or LinkedIn Learning",
                                "Week 3-4: Analyze 3-5 company financial statements and calculate key ratios",
                                "Week 5-6: Build a personal portfolio of financial analysis case studies",
                            ],
                            "resources": [
                                "Platform: Coursera 'Financial Analysis' or edX accounting courses",
                                "Tool: Excel practice with real company data from Yahoo Finance",
                                "Book: 'Financial Intelligence' by Karen Berman",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Financial Analysis Mastery",
                            "immediate_actions": [
                                "Master advanced Excel: macros, Power Query, and financial modeling",
                                "Learn industry-specific financial analysis (retail, tech, manufacturing)",
                                "Practice building complete financial models with forecasting",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete advanced financial modeling courses",
                                "Week 3-4: Build 3-year forecast models for different industries",
                                "Week 5-6: Prepare for CFA Level 1 or CPA fundamentals",
                            ],
                            "resources": [
                                "Platform: Wall Street Prep or CFI financial modeling courses",
                                "Certification: Begin CFA Level 1 or CPA preparation",
                                "Practice: Participate in case competitions (Bloomberg, CFA challenge)",
                            ],
                        },
                    },
                },
                "business_communication": {
                    "keywords": [
                        "presentation",
                        "pitch",
                        "client",
                        "stakeholder",
                        "meeting",
                        "negotiation",
                        "proposal",
                        "business writing",
                        "email",
                        "report",
                        "executive summary",
                        "powerpoint",
                        "slides",
                        "public speaking",
                        "corporate communication",
                        "interpersonal",
                        "networking",
                        "rapport",
                        "persuasion",
                        "influence",
                        "body language",
                        "professional etiquette",
                        "business correspondence",
                        "memo",
                        "minutes",
                        "agenda",
                        "boardroom",
                        "conference",
                        "articulation",
                        "clarity",
                        "conciseness",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Business Communication Excellence",
                            "immediate_actions": [
                                "Practice elevator pitches for business ideas (30-second and 2-minute versions)",
                                "Learn business email etiquette and professional correspondence",
                                "Join Toastmasters or business presentation clubs",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Master business writing fundamentals - clarity, conciseness, impact",
                                "Week 3-4: Practice presenting business proposals to peers",
                                "Week 5-6: Develop skills in creating executive summaries and reports",
                            ],
                            "resources": [
                                "Course: 'Business Writing' on LinkedIn Learning",
                                "Platform: Toastmasters International for public speaking",
                                "Book: 'The Pyramid Principle' by Barbara Minto",
                            ],
                        }
                    },
                },
                "market_research": {
                    "keywords": [
                        "market",
                        "research",
                        "survey",
                        "consumer",
                        "customer",
                        "trends",
                        "marketing",
                        "strategy",
                        "segmentation",
                        "competition",
                        "analysis",
                        "target audience",
                        "demographics",
                        "psychographics",
                        "focus group",
                        "questionnaire",
                        "sampling",
                        "primary research",
                        "secondary research",
                        "competitive analysis",
                        "swot",
                        "pest analysis",
                        "porter five forces",
                        "market size",
                        "market share",
                        "brand positioning",
                        "pricing strategy",
                        "product launch",
                        "go-to-market",
                        "buyer persona",
                        "customer journey",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Market Research & Analysis Skills",
                            "immediate_actions": [
                                "Learn survey design and data collection methodologies",
                                "Study market segmentation and targeting strategies",
                                "Practice competitor analysis using Porter's Five Forces",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete a market research course (Google Digital Garage)",
                                "Week 3-4: Conduct a mini market research project for a local business",
                                "Week 5-6: Create comprehensive market analysis reports",
                            ],
                            "resources": [
                                "Course: Google Digital Marketing & Analytics courses",
                                "Tool: Google Trends, SurveyMonkey for research",
                                "Book: 'Marketing Research' by Naresh Malhotra",
                            ],
                        }
                    },
                },
                "economics_trade": {
                    "keywords": [
                        "economics",
                        "microeconomics",
                        "macroeconomics",
                        "supply",
                        "demand",
                        "elasticity",
                        "gdp",
                        "inflation",
                        "monetary policy",
                        "fiscal policy",
                        "international trade",
                        "import",
                        "export",
                        "tariff",
                        "trade policy",
                        "exchange rate",
                        "forex",
                        "economic theory",
                        "market equilibrium",
                        "game theory",
                        "behavioral economics",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Economics & Trade Fundamentals",
                            "immediate_actions": [
                                "Master core economic concepts: supply-demand, elasticity, market structures",
                                "Study international trade theories and trade policy mechanisms",
                                "Learn to interpret economic indicators and their business implications",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete microeconomics and macroeconomics foundation courses",
                                "Week 3-4: Analyze real-world economic scenarios and policy decisions",
                                "Week 5-6: Practice economic modeling and forecasting techniques",
                            ],
                            "resources": [
                                "Course: 'Principles of Economics' on Khan Academy or Coursera",
                                "Tool: FRED Economic Data for real-time economic analysis",
                                "Book: 'Economics' by Paul Samuelson or 'Principles of Economics' by Mankiw",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Economics & Global Trade",
                            "immediate_actions": [
                                "Study econometrics and advanced statistical analysis for economic data",
                                "Learn trade finance, foreign exchange, and international business transactions",
                                "Master economic policy analysis and impact assessment methodologies",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete econometrics courses and practice with real datasets",
                                "Week 3-4: Analyze global trade patterns and international economic policies",
                                "Week 5-6: Build economic models and conduct scenario analysis",
                            ],
                            "resources": [
                                "Platform: World Bank Open Data, IMF resources for global economics",
                                "Software: STATA, R, or Python for econometric analysis",
                                "Certification: Prepare for economics certifications or graduate studies",
                            ],
                        },
                    },
                },
            },
            "science": {
                "research_methodology": {
                    "keywords": [
                        "research",
                        "experiment",
                        "hypothesis",
                        "methodology",
                        "data",
                        "analysis",
                        "laboratory",
                        "protocol",
                        "scientific method",
                        "results",
                        "conclusion",
                        "peer review",
                        "publication",
                        "journal",
                        "variable",
                        "control group",
                        "experimental design",
                        "replication",
                        "validity",
                        "reliability",
                        "literature review",
                        "research proposal",
                        "thesis",
                        "dissertation",
                        "citations",
                        "references",
                        "bibliography",
                        "abstract",
                        "methodology section",
                        "data collection",
                        "qualitative",
                        "quantitative",
                        "mixed methods",
                        "correlation",
                        "causation",
                        "statistical significance",
                        "p-value",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Research Methodology Fundamentals",
                            "immediate_actions": [
                                "Learn proper experimental design: controls, variables, and replication",
                                "Master laboratory notebook keeping and documentation standards",
                                "Practice writing clear hypotheses and research questions",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Study research ethics and proper citation practices",
                                "Week 3-4: Design and conduct a small-scale research project",
                                "Week 5-6: Practice data analysis using appropriate statistical methods",
                            ],
                            "resources": [
                                "Course: 'Research Methods' on Coursera or edX",
                                "Tool: R or Python for statistical analysis, Mendeley for references",
                                "Book: 'The Craft of Research' by Booth et al.",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Research Excellence",
                            "immediate_actions": [
                                "Work on publishable research projects with faculty mentors",
                                "Learn advanced statistical techniques and data visualization",
                                "Practice presenting research at seminars and conferences",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Draft a research paper following journal guidelines",
                                "Week 3-4: Master advanced lab techniques specific to your field",
                                "Week 5-6: Apply for research grants or present at conferences",
                            ],
                            "resources": [
                                "Platform: ResearchGate for networking and collaboration",
                                "Tool: GraphPad Prism, SPSS for advanced analysis",
                                "Resource: Nature Masterclasses on scientific writing",
                            ],
                        },
                    },
                },
                "technical_skills": {
                    "keywords": [
                        "equipment",
                        "instrument",
                        "technique",
                        "procedure",
                        "calibration",
                        "measurement",
                        "precision",
                        "accuracy",
                        "troubleshooting",
                        "microscope",
                        "spectroscopy",
                        "chromatography",
                        "centrifuge",
                        "pipetting",
                        "titration",
                        "sterilization",
                        "aseptic technique",
                        "safety protocols",
                        "ppe",
                        "lab safety",
                        "chemical handling",
                        "waste disposal",
                        "lab notebook",
                        "sop",
                        "standard operating procedure",
                        "glassware",
                        "reagent",
                        "buffer preparation",
                        "dilution",
                        "pcr",
                        "electrophoresis",
                        "cell culture",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Laboratory Skills Development",
                            "immediate_actions": [
                                "Master fundamental lab techniques: pipetting, weighing, dilutions",
                                "Learn proper equipment handling and safety protocols",
                                "Practice maintaining accurate lab records and calculations",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete lab safety certification and equipment training",
                                "Week 3-4: Practice key techniques until proficient and reproducible",
                                "Week 5-6: Volunteer for additional lab time to build confidence",
                            ],
                            "resources": [
                                "Resource: Lab technique videos on JoVE (Journal of Visualized Experiments)",
                                "Practice: Shadow experienced researchers during experiments",
                                "Course: Lab-specific training workshops at your institution",
                            ],
                        }
                    },
                },
                "data_analysis": {
                    "keywords": [
                        "statistics",
                        "data analysis",
                        "spss",
                        "r programming",
                        "python",
                        "data visualization",
                        "graphs",
                        "charts",
                        "anova",
                        "t-test",
                        "regression",
                        "standard deviation",
                        "mean",
                        "median",
                        "normal distribution",
                        "confidence interval",
                        "hypothesis testing",
                        "null hypothesis",
                        "alternative hypothesis",
                        "sample size",
                        "outliers",
                        "dataset",
                        "coding",
                        "programming",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Scientific Data Analysis Fundamentals",
                            "immediate_actions": [
                                "Learn basic statistics: descriptive statistics, probability, distributions",
                                "Master one statistical software: R, Python, or SPSS for data analysis",
                                "Practice creating clear data visualizations and interpreting results",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete intro to statistics and data analysis courses",
                                "Week 3-4: Analyze sample datasets and perform basic statistical tests",
                                "Week 5-6: Learn to interpret p-values and statistical significance",
                            ],
                            "resources": [
                                "Platform: DataCamp, Coursera for statistics and R/Python courses",
                                "Software: R Studio, Jupyter Notebooks for practice",
                                "Book: 'Statistics' by Freedman, Pisani, and Purves",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Scientific Data Analytics",
                            "immediate_actions": [
                                "Master advanced statistical methods: multivariate analysis, time series",
                                "Learn machine learning basics for pattern recognition in scientific data",
                                "Develop skills in reproducible research and data management",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Practice complex statistical analyses on research data",
                                "Week 3-4: Learn data visualization best practices for scientific publications",
                                "Week 5-6: Master version control and reproducible workflows (Git, Docker)",
                            ],
                            "resources": [
                                "Platform: Kaggle for data science practice and competitions",
                                "Tool: GraphPad Prism, OriginLab for scientific graphing",
                                "Course: 'Statistical Learning' by Stanford on edX",
                            ],
                        },
                    },
                },
            },
            "arts": {
                "creative_portfolio": {
                    "keywords": [
                        "portfolio",
                        "artwork",
                        "design",
                        "creative",
                        "project",
                        "exhibition",
                        "style",
                        "technique",
                        "composition",
                        "visual",
                        "aesthetic",
                        "gallery",
                        "curator",
                        "showcase",
                        "presentation",
                        "layout",
                        "typography",
                        "color theory",
                        "branding",
                        "identity",
                        "logo",
                        "illustration",
                        "digital art",
                        "graphic design",
                        "web design",
                        "ui ux",
                        "adobe",
                        "photoshop",
                        "illustrator",
                        "indesign",
                        "figma",
                        "sketch",
                        "behance",
                        "dribbble",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Building Professional Creative Portfolio",
                            "immediate_actions": [
                                "Curate 10-15 of your best works that showcase different skills",
                                "Create a professional online portfolio (Behance, ArtStation, or personal website)",
                                "Document your creative process for each major project",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Photograph/digitize work professionally with good lighting",
                                "Week 3-4: Write artist statements and project descriptions",
                                "Week 5-6: Get feedback from instructors and refine portfolio",
                            ],
                            "resources": [
                                "Platform: Behance, Dribbble, or ArtStation for portfolio hosting",
                                "Course: 'Portfolio Development' courses on Skillshare",
                                "Resource: Study portfolios of professionals in your field",
                            ],
                        },
                        "intermediate": {
                            "title": "Professional Portfolio Excellence",
                            "immediate_actions": [
                                "Develop a cohesive personal brand and artistic identity",
                                "Create case studies showing your creative problem-solving process",
                                "Network with galleries, clients, or creative agencies",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Submit work to juried exhibitions or competitions",
                                "Week 3-4: Collaborate with other artists on ambitious projects",
                                "Week 5-6: Develop specialized portfolio for target opportunities",
                            ],
                            "resources": [
                                "Platform: Enter design competitions (AIGA, Red Dot, D&AD)",
                                "Networking: Attend gallery openings and creative meetups",
                                "Resource: Creative agency portfolio guidelines and examples",
                            ],
                        },
                    },
                },
                "artistic_technique": {
                    "keywords": [
                        "skill",
                        "technique",
                        "practice",
                        "fundamentals",
                        "drawing",
                        "painting",
                        "sculpting",
                        "medium",
                        "tool",
                        "craft",
                        "execution",
                        "brushwork",
                        "shading",
                        "perspective",
                        "anatomy",
                        "proportion",
                        "rendering",
                        "sketching",
                        "linework",
                        "watercolor",
                        "acrylic",
                        "oil painting",
                        "charcoal",
                        "pencil",
                        "pastels",
                        "digital painting",
                        "3d modeling",
                        "animation",
                        "texture",
                        "lighting",
                        "form",
                        "gesture drawing",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Artistic Skill Development",
                            "immediate_actions": [
                                "Commit to daily practice sessions (even 30 minutes builds skill)",
                                "Study fundamentals: perspective, color theory, composition, anatomy",
                                "Join critique groups to get constructive feedback",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Focus on one fundamental skill intensively",
                                "Week 3-4: Complete studies of master works in your medium",
                                "Week 5-6: Create finished pieces applying learned techniques",
                            ],
                            "resources": [
                                "Platform: Skillshare or New Masters Academy for technique courses",
                                "Practice: Daily sketching or creative exercises",
                                "Book: Domain-specific technique books (e.g., 'Drawing on the Right Side of the Brain')",
                            ],
                        }
                    },
                },
                "creative_concept": {
                    "keywords": [
                        "concept",
                        "idea",
                        "brainstorm",
                        "creativity",
                        "innovation",
                        "imagination",
                        "inspiration",
                        "mood board",
                        "research",
                        "reference",
                        "storytelling",
                        "narrative",
                        "theme",
                        "message",
                        "symbolism",
                        "metaphor",
                        "artistic vision",
                        "original",
                        "unique",
                        "experimentation",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Creative Concept Development",
                            "immediate_actions": [
                                "Develop daily ideation practice: keep a sketchbook or idea journal",
                                "Create mood boards and visual research for each project",
                                "Study how successful artists develop and communicate concepts",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Generate 10+ concept ideas for different themes or briefs",
                                "Week 3-4: Develop complete concept presentations with visual references",
                                "Week 5-6: Execute 2-3 concept-driven projects from ideation to completion",
                            ],
                            "resources": [
                                "Platform: Pinterest, Behance for visual research and inspiration",
                                "Book: 'Steal Like an Artist' by Austin Kleon",
                                "Practice: Daily observation and documentation exercises",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Creative Thinking & Innovation",
                            "immediate_actions": [
                                "Develop signature style while maintaining creative flexibility",
                                "Master storytelling through visual elements and composition",
                                "Learn to pitch and defend creative concepts to clients or stakeholders",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Create concept-driven series exploring complex themes",
                                "Week 3-4: Practice presenting work with strong conceptual narratives",
                                "Week 5-6: Collaborate with others to strengthen concept development",
                            ],
                            "resources": [
                                "Platform: CreativeMornings talks for inspiration and community",
                                "Book: 'Creative Confidence' by Tom and David Kelley",
                                "Workshop: Join design thinking or concept development workshops",
                            ],
                        },
                    },
                },
            },
            "medical": {
                "clinical_skills": {
                    "keywords": [
                        "patient",
                        "diagnosis",
                        "clinical",
                        "medical",
                        "healthcare",
                        "treatment",
                        "symptoms",
                        "examination",
                        "bedside",
                        "communication",
                        "empathy",
                        "history taking",
                        "physical exam",
                        "vital signs",
                        "auscultation",
                        "palpation",
                        "percussion",
                        "inspection",
                        "differential diagnosis",
                        "clinical reasoning",
                        "patient care",
                        "rounds",
                        "ward",
                        "osce",
                        "soap notes",
                        "medical records",
                        "documentation",
                        "professionalism",
                        "ethics",
                        "compassion",
                        "bedside manner",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Clinical Skills Foundation",
                            "immediate_actions": [
                                "Practice history-taking and physical examination systematically",
                                "Master patient communication with empathy and clarity",
                                "Learn to present cases in standard medical format (SOAP notes)",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Shadow experienced clinicians and observe consultations",
                                "Week 3-4: Practice on standardized patients or simulation labs",
                                "Week 5-6: Master documentation and medical record keeping",
                            ],
                            "resources": [
                                "Resource: OSCE practice videos and clinical skills workshops",
                                "Platform: Osmosis or Medscape for clinical knowledge",
                                "Practice: Volunteer at clinics for patient interaction experience",
                            ],
                        }
                    },
                },
                "medical_knowledge": {
                    "keywords": [
                        "anatomy",
                        "physiology",
                        "pathology",
                        "pharmacology",
                        "biochemistry",
                        "disease",
                        "mechanism",
                        "understanding",
                        "concepts",
                        "medical knowledge",
                        "microbiology",
                        "immunology",
                        "genetics",
                        "neurology",
                        "cardiology",
                        "respiratory",
                        "gastrointestinal",
                        "endocrine",
                        "renal",
                        "hematology",
                        "oncology",
                        "pathophysiology",
                        "drug mechanism",
                        "side effects",
                        "contraindications",
                        "clinical medicine",
                        "internal medicine",
                        "surgery",
                        "pediatrics",
                        "obstetrics",
                        "gynecology",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Medical Knowledge Mastery",
                            "immediate_actions": [
                                "Use active learning: flashcards (Anki), concept maps, and practice questions",
                                "Join study groups to discuss complex medical concepts",
                                "Relate basic science to clinical applications regularly",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Master one body system completely before moving forward",
                                "Week 3-4: Practice MCQs and clinical vignettes daily",
                                "Week 5-6: Create connections between different subjects",
                            ],
                            "resources": [
                                "App: Anki for spaced repetition learning",
                                "Platform: UWorld, Amboss, or Lecturio for practice questions",
                                "Resource: First Aid, Pathoma, or Boards and Beyond",
                            ],
                        }
                    },
                },
            },
            "law": {
                "legal_research": {
                    "keywords": [
                        "legal",
                        "research",
                        "case",
                        "statute",
                        "precedent",
                        "citation",
                        "legal writing",
                        "brief",
                        "memo",
                        "argument",
                        "analysis",
                        "Westlaw",
                        "LexisNexis",
                        "Bluebook",
                        "IRAC method",
                        "case law",
                        "statutory interpretation",
                        "legal database",
                        "case brief",
                        "legal memo",
                        "legal opinion",
                        "shepardize",
                        "KeyCite",
                        "headnotes",
                        "digests",
                        "treatise",
                        "law review",
                        "legal periodicals",
                        "secondary sources",
                        "primary sources",
                        "binding authority",
                        "persuasive authority",
                        "dictum",
                        "holding",
                        "ratio decidendi",
                        "obiter dictum",
                        "stare decisis",
                        "distinguishing cases",
                        "overruling",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Legal Research & Writing Skills",
                            "immediate_actions": [
                                "Master legal research databases: Westlaw, LexisNexis, or Google Scholar",
                                "Learn proper legal citation format (Bluebook or local standard)",
                                "Practice IRAC method: Issue, Rule, Application, Conclusion",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete legal research tutorials and database training",
                                "Week 3-4: Analyze landmark cases and write case briefs",
                                "Week 5-6: Draft legal memos on hypothetical scenarios",
                            ],
                            "resources": [
                                "Course: Legal writing workshops at your institution",
                                "Resource: 'Legal Writing in Plain English' by Bryan Garner",
                                "Platform: Practice with moot court or legal aid clinics",
                            ],
                        }
                    },
                },
                "advocacy_skills": {
                    "keywords": [
                        "advocacy",
                        "argument",
                        "moot court",
                        "debate",
                        "oral",
                        "persuasion",
                        "courtroom",
                        "litigation",
                        "negotiation",
                        "oral argument",
                        "cross-examination",
                        "direct examination",
                        "opening statement",
                        "closing argument",
                        "rebuttal",
                        "objection",
                        "evidence presentation",
                        "witness preparation",
                        "trial advocacy",
                        "appellate advocacy",
                        "mediation",
                        "arbitration",
                        "ADR",
                        "settlement negotiation",
                        "client counseling",
                        "legal ethics",
                        "professional responsibility",
                        "courtroom etiquette",
                        "legal strategy",
                        "case theory",
                        "storytelling",
                        "jury selection",
                        "voir dire",
                        "impeachment",
                        "redirect examination",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Advocacy & Argumentation Skills",
                            "immediate_actions": [
                                "Join moot court or mock trial teams at your institution",
                                "Practice oral arguments with structured feedback",
                                "Study effective advocates and their techniques",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Watch and analyze recorded oral arguments",
                                "Week 3-4: Practice responding to tough questions on the spot",
                                "Week 5-6: Participate in internal moot competitions",
                            ],
                            "resources": [
                                "Platform: Oyez.org for Supreme Court oral argument recordings",
                                "Activity: Join debate society or moot court society",
                                "Resource: 'Point Made' by Ross Guberman for persuasive writing",
                            ],
                        }
                    },
                },
                "legal_practice": {
                    "keywords": [
                        "contract law",
                        "torts",
                        "criminal law",
                        "constitutional law",
                        "property law",
                        "corporate law",
                        "intellectual property",
                        "legal ethics",
                        "professional conduct",
                        "attorney-client privilege",
                        "confidentiality",
                        "conflict of interest",
                        "legal drafting",
                        "contract drafting",
                        "due diligence",
                        "compliance",
                        "regulatory",
                        "jurisprudence",
                        "legal theory",
                        "civil procedure",
                        "criminal procedure",
                        "evidence law",
                        "administrative law",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Legal Practice & Professional Skills",
                            "immediate_actions": [
                                "Study foundational subjects: Contracts, Torts, Criminal Law",
                                "Learn professional ethics and attorney-client responsibilities",
                                "Practice legal drafting with real-world templates",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete case readings and briefings for core subjects",
                                "Week 3-4: Study Rules of Professional Conduct thoroughly",
                                "Week 5-6: Draft contracts, NDAs, and legal correspondence",
                            ],
                            "resources": [
                                "Book: 'Getting to Maybe' by Fischl & Paul for exam preparation",
                                "Platform: Practical Law or LawDepot for document templates",
                                "Course: Professional responsibility and legal ethics modules",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Legal Practice",
                            "immediate_actions": [
                                "Seek internships at law firms, courts, or legal aid organizations",
                                "Specialize in 1-2 practice areas of interest",
                                "Build practical skills through clinical programs",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Work on real client matters under supervision",
                                "Week 3-4: Develop expertise in chosen specialization",
                                "Week 5-6: Network with practicing attorneys and attend CLEs",
                            ],
                            "resources": [
                                "Opportunity: Apply for judicial clerkships or externships",
                                "Platform: Bar exam prep courses (Barbri, Themis, Kaplan)",
                                "Activity: Attend bar association meetings and CLE events",
                            ],
                        },
                    },
                },
            },
            "management": {
                "leadership": {
                    "keywords": [
                        "leadership",
                        "team",
                        "management",
                        "delegation",
                        "motivation",
                        "decision making",
                        "strategic",
                        "organizational",
                        "planning",
                        "team building",
                        "conflict resolution",
                        "emotional intelligence",
                        "coaching",
                        "mentoring",
                        "performance management",
                        "change management",
                        "transformational leadership",
                        "servant leadership",
                        "situational leadership",
                        "visionary leadership",
                        "employee engagement",
                        "talent development",
                        "succession planning",
                        "organizational culture",
                        "team dynamics",
                        "communication skills",
                        "active listening",
                        "feedback delivery",
                        "problem solving",
                        "critical thinking",
                        "innovation management",
                        "empowerment",
                        "accountability",
                        "KPI management",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Leadership & Management Skills",
                            "immediate_actions": [
                                "Take leadership roles in student organizations or projects",
                                "Learn delegation and team motivation techniques",
                                "Practice giving constructive feedback to peers",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Study leadership theories and management frameworks",
                                "Week 3-4: Lead a small team project from inception to completion",
                                "Week 5-6: Seek mentorship from experienced managers",
                            ],
                            "resources": [
                                "Course: 'Leadership Principles' on Coursera or edX",
                                "Book: 'Leaders Eat Last' by Simon Sinek",
                                "Practice: Volunteer to lead committees or organize events",
                            ],
                        }
                    },
                },
                "business_strategy": {
                    "keywords": [
                        "strategy",
                        "business model",
                        "competitive advantage",
                        "swot",
                        "market analysis",
                        "planning",
                        "execution",
                        "growth",
                        "Porter's Five Forces",
                        "BCG matrix",
                        "Ansoff matrix",
                        "value chain analysis",
                        "core competencies",
                        "strategic planning",
                        "vision statement",
                        "mission statement",
                        "strategic objectives",
                        "balanced scorecard",
                        "blue ocean strategy",
                        "differentiation strategy",
                        "cost leadership",
                        "market penetration",
                        "diversification",
                        "vertical integration",
                        "horizontal integration",
                        "strategic alliances",
                        "mergers and acquisitions",
                        "corporate strategy",
                        "business unit strategy",
                        "competitive positioning",
                        "market segmentation",
                        "strategic fit",
                        "scenario planning",
                        "strategic roadmap",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Strategic Thinking Development",
                            "immediate_actions": [
                                "Learn strategic frameworks: SWOT, Porter's 5 Forces, BCG Matrix",
                                "Analyze case studies from Harvard Business Review",
                                "Practice developing business strategies for real companies",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Study one strategic framework deeply each week",
                                "Week 3-4: Apply frameworks to analyze 3-5 companies",
                                "Week 5-6: Participate in strategy case competitions",
                            ],
                            "resources": [
                                "Platform: Harvard Business Review case studies",
                                "Course: 'Business Strategy' specialization on Coursera",
                                "Book: 'Good Strategy Bad Strategy' by Richard Rumelt",
                            ],
                        }
                    },
                },
                "operations_management": {
                    "keywords": [
                        "operations",
                        "supply chain",
                        "logistics",
                        "inventory management",
                        "quality management",
                        "process optimization",
                        "lean management",
                        "six sigma",
                        "project management",
                        "agile",
                        "scrum",
                        "kaizen",
                        "total quality management",
                        "TQM",
                        "just-in-time",
                        "JIT",
                        "production planning",
                        "capacity planning",
                        "workflow optimization",
                        "efficiency",
                        "productivity",
                        "resource allocation",
                        "vendor management",
                        "procurement",
                        "cost reduction",
                        "process improvement",
                        "continuous improvement",
                        "operational excellence",
                    ],
                    "suggestions": {
                        "beginner": {
                            "title": "Operations & Process Management",
                            "immediate_actions": [
                                "Learn operations management fundamentals: supply chain, inventory, quality",
                                "Study lean principles and waste elimination techniques",
                                "Understand project management methodologies: Agile, Waterfall, Scrum",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Complete course on operations management basics",
                                "Week 3-4: Practice process mapping and optimization exercises",
                                "Week 5-6: Apply lean or six sigma tools to real scenarios",
                            ],
                            "resources": [
                                "Course: 'Operations Management' on edX or Coursera",
                                "Certification: Google Project Management Certificate",
                                "Tool: Lucidchart or Miro for process mapping",
                            ],
                        },
                        "intermediate": {
                            "title": "Advanced Operations Excellence",
                            "immediate_actions": [
                                "Pursue Six Sigma Green Belt or PMP certification",
                                "Analyze real supply chains and identify optimization opportunities",
                                "Lead process improvement projects in internships or organizations",
                            ],
                            "weekly_goals": [
                                "Week 1-2: Work on supply chain case studies and simulations",
                                "Week 3-4: Implement lean techniques in a real project",
                                "Week 5-6: Track KPIs and measure operational improvements",
                            ],
                            "resources": [
                                "Certification: Six Sigma Green/Black Belt, PMP, CAPM",
                                "Software: MS Project, Asana, Jira for project tracking",
                                "Platform: Supply chain simulation games and case competitions",
                            ],
                        },
                    },
                },
            },
        }

    def _load_suggestion_variations(self) -> Dict:
        """Load comprehensive variations for making suggestions unique each time"""
        return {
            "communication": {
                "beginner": {
                    "actions": [
                        [
                            "Master the STAR framework (Situation, Task, Action, Result) for answering behavioral interview questions",
                            "Practice articulating your answers using the STAR approach - describe context, objectives, actions, and outcomes",
                            "Apply the STAR storytelling technique to structure responses: set scene, define goals, outline steps, highlight impact",
                            "Learn to respond systematically with STAR: establish background, state challenge, detail solution, share results",
                        ],
                        [
                            "Record yourself answering common interview questions and analyze areas needing improvement",
                            "Create video recordings of your mock interview responses to identify refinement opportunities",
                            "Film yourself discussing technical topics and review for clarity and confidence enhancement",
                            "Use self-recording as a tool to spot communication gaps and improve delivery",
                        ],
                        [
                            "Join a study group or peer mock interview sessions for structured practice",
                            "Participate in mock interview clubs at your college to develop your response abilities",
                            "Enroll in interview preparation groups or workshops for regular practice",
                            "Become part of a practice community where students conduct mock interviews",
                        ],
                    ],
                    "goals": [
                        [
                            "Initial phase: Concentrate on speaking at a measured pace with deliberate pauses",
                            "First fortnight: Work on slowing your speech tempo and adding strategic breaks",
                            "Opening two weeks: Focus on controlled speech rate with thoughtful pausing",
                            "Weeks 1-2: Practice measured delivery with intentional silence between points",
                        ],
                        [
                            "Mid-phase: Develop active listening by paraphrasing others before replying",
                            "Weeks 3-4: Build listening skills through summarizing what you hear before responding",
                            "Next fortnight: Strengthen engagement by reflecting back what others communicate",
                            "Following period: Enhance understanding by restating others' input prior to your response",
                        ],
                        [
                            "Final phase: Enhance non-verbal signals including eye contact and body language",
                            "Weeks 5-6: Refine physical communication through gaze and gesture awareness",
                            "Concluding period: Polish unspoken communication via visual connection and movement",
                            "Last segment: Improve silent communication elements like facial engagement and gestures",
                        ],
                    ],
                },
                "intermediate": {
                    "actions": [
                        [
                            "Develop concise elevator pitches for your projects and academic achievements",
                            "Build compelling 30-second summaries of your key accomplishments and skills",
                            "Design brief, impactful introductions that highlight your strengths and experiences",
                            "Create clear, memorable descriptions of your projects and what makes you unique",
                        ],
                        [
                            "Work on explaining technical concepts in simple, accessible language for non-technical interviewers",
                            "Develop ability to break down complex algorithms and projects for general understanding",
                            "Practice simplifying technical knowledge without losing important details",
                            "Hone skills in making complicated topics clear to HR or non-technical stakeholders",
                        ],
                        [
                            "Prepare detailed examples demonstrating your problem-solving and analytical thinking",
                            "Document stories that showcase your learning ability and adaptability",
                            "Gather evidence of times you overcame challenges or learned new skills quickly",
                            "Compile examples of projects where you showed initiative and critical thinking",
                        ],
                    ]
                },
            },
            "preparation": {
                "beginner": {
                    "actions": [
                        [
                            "Create a comprehensive list of interview topics and assess your confidence level in each area",
                            "Map out all key subjects you might be asked about and rate your readiness honestly",
                            "Develop a topic inventory with self-assessment scores to identify preparation gaps",
                            "Build a knowledge checklist covering interview areas and mark your comfort level for each",
                        ],
                        [
                            "Dedicate 2-3 focused hours daily to studying and practicing weak areas",
                            "Allocate consistent daily time blocks for strengthening areas where you lack confidence",
                            "Commit to regular study sessions targeting your identified knowledge gaps",
                            "Set aside dedicated preparation time each day for topics needing improvement",
                        ],
                        [
                            "Research the company thoroughly - products, culture, recent news, and specific job requirements",
                            "Study the organization in depth including their services, values, latest updates, and role expectations",
                            "Investigate the company comprehensively from their offerings to their work environment and position details",
                            "Conduct detailed research on the employer covering their business, atmosphere, current events, and job specifications",
                        ],
                    ]
                },
                "intermediate": {
                    "actions": [
                        [
                            "Build a portfolio of 3-5 strong projects that clearly demonstrate your skills and problem-solving ability",
                            "Develop several well-documented projects showcasing your technical capabilities and analytical thinking",
                            "Create a collection of quality projects that prove your competence and innovative approach",
                            "Assemble multiple substantial projects that highlight your expertise and solution-oriented mindset",
                        ],
                        [
                            "Prepare detailed stories about your academic projects, internships, and notable achievements",
                            "Craft compelling narratives around your coursework, practical experiences, and accomplishments",
                            "Document rich examples from your education, hands-on work, and successes",
                            "Develop thorough accounts of your college projects, training periods, and key wins",
                        ],
                    ]
                },
            },
            "technical_skills": {
                "beginner": {
                    "actions": [
                        [
                            "Start with fundamentals - master basic data structures like arrays, linked lists, stacks, queues, and trees",
                            "Build strong foundation in core data structures including lists, arrays, stacks, queues, and binary trees",
                            "Focus on essential building blocks - arrays, linked structures, stacks, queues, and tree fundamentals",
                            "Begin with data structure basics covering arrays, lists, stacks, queues, and elementary trees",
                        ],
                        [
                            "Practice 3-5 coding problems daily, progressing from easy to medium difficulty levels",
                            "Solve multiple programming challenges each day, gradually increasing complexity",
                            "Work through several coding exercises daily, starting simple and building up difficulty",
                            "Complete 3-5 algorithm problems per day, moving from beginner to intermediate level",
                        ],
                        [
                            "Learn to explain your thought process out loud while solving problems during practice",
                            "Develop the habit of verbalizing your approach as you work through coding challenges",
                            "Practice thinking aloud technique - articulate your logic while solving algorithms",
                            "Train yourself to speak through your reasoning as you tackle programming problems",
                        ],
                    ]
                },
                "intermediate": {
                    "actions": [
                        [
                            "Tackle medium to hard difficulty problems with focus on finding optimal, efficient solutions",
                            "Work on challenging problems prioritizing time and space complexity optimization",
                            "Practice advanced difficulty questions while emphasizing most efficient approaches",
                            "Solve complex algorithmic challenges concentrating on optimal performance solutions",
                        ],
                        [
                            "Study and implement common coding patterns - sliding window, two pointers, BFS/DFS, backtracking",
                            "Master frequently-used techniques like window sliding, pointer methods, graph traversals, and backtracking",
                            "Learn standard problem-solving patterns including two-pointer, sliding window, tree/graph traversal approaches",
                            "Practice essential algorithms: sliding windows, dual pointers, breadth/depth-first search, recursive backtracking",
                        ],
                    ]
                },
            },
            "confidence": {
                "beginner": {
                    "actions": [
                        [
                            "Practice positive self-talk and visualization - mentally rehearse succeeding in your interview",
                            "Use affirmations and mental imagery techniques to envision performing well",
                            "Employ positive thinking and imagination exercises picturing your interview success",
                            "Apply confidence-building visualization where you see yourself answering questions excellently",
                        ],
                        [
                            "Prepare thoroughly to build natural confidence in your knowledge and abilities",
                            "Study comprehensively so your preparation creates genuine self-assurance",
                            "Practice extensively to develop authentic confidence through mastery",
                            "Invest in deep preparation which organically builds your self-belief and composure",
                        ],
                        [
                            "Start with mock interviews in comfortable settings with friends or family members",
                            "Begin practice sessions in relaxed environments with supportive peers or relatives",
                            "Initiate interview rehearsals in safe spaces with people you trust",
                            "Launch mock interview practice in low-pressure situations with familiar people",
                        ],
                    ]
                },
                "intermediate": {
                    "actions": [
                        [
                            "Develop a pre-interview routine that consistently puts you in peak mental state",
                            "Create a preparation ritual that helps you reach optimal performance mindset",
                            "Establish a before-interview protocol for achieving your best psychological condition",
                            "Build a warm-up sequence that brings out your strongest mental game",
                        ],
                        [
                            "Learn to reframe nervousness as excitement and channel that energy positively",
                            "Practice converting anxiety into enthusiasm and using it as motivational fuel",
                            "Master transforming nervous energy into productive, positive drive",
                            "Develop skills to redirect stress into focused, energetic performance",
                        ],
                    ]
                },
            },
            "projects_experience": {
                "beginner": {
                    "actions": [
                        [
                            "Start with 2-3 well-documented projects that solve real-world problems or meet actual needs",
                            "Build a few quality projects with clear documentation addressing genuine use cases",
                            "Create several thoroughly explained projects that tackle practical challenges",
                            "Develop 2-3 projects with strong documentation solving problems people actually face",
                        ],
                        [
                            "Ensure each project demonstrates different skills, technologies, and problem-solving approaches",
                            "Make sure your projects showcase variety in tech stacks, methods, and capabilities",
                            "Design your portfolio so each project highlights distinct technical strengths",
                            "Structure projects to display diverse abilities, tools, and solution strategies",
                        ],
                        [
                            "Create detailed README files explaining your project's purpose, tech stack, and your specific contributions",
                            "Write comprehensive project documentation covering objectives, technologies used, and what you built",
                            "Develop thorough README content describing the problem, your solution, and technical choices",
                            "Craft clear project descriptions outlining goals, implementation details, and your role",
                        ],
                    ]
                },
                "intermediate": {
                    "actions": [
                        [
                            "Build 1-2 complex projects that demonstrate system design thinking and scalability considerations",
                            "Develop advanced projects showing your understanding of architecture and growth planning",
                            "Create sophisticated applications that prove you can think about larger system implications",
                            "Construct challenging projects revealing your grasp of design patterns and scaling concepts",
                        ],
                        [
                            "Contribute to open-source projects to demonstrate collaboration skills and code quality standards",
                            "Participate in open-source communities showing teamwork ability and professional coding practices",
                            "Engage with open-source development proving you can work with others on shared codebases",
                            "Join open-source initiatives to showcase collaborative development and quality awareness",
                        ],
                    ]
                },
            },
        }

    def _get_varied_suggestion_component(
        self,
        category: str,
        level: str,
        component_type: str,
        index: int,
        feedback_text: str,
    ) -> str:
        """Get a varied version of a suggestion component based on feedback context"""
        variations_db = (
            self.suggestion_variations.get(category, {})
            .get(level, {})
            .get(component_type, [])
        )

        if not variations_db or index >= len(variations_db):
            return None

        options = variations_db[index]
        if not options:
            return None

        # Use feedback text as seed for deterministic but varied selection
        seed = hashlib.md5(feedback_text.encode()).hexdigest()
        index_choice = int(seed[:8], 16) % len(options)

        return options[index_choice]

    def _initialize_vectorizer(self):
        """Initialize the vectorizer with all suggestion texts and database feedback"""
        all_texts = []

        # Add static keywords from suggestion database
        for category in self.suggestion_db.values():
            for keyword in category["keywords"]:
                all_texts.append(keyword)

        # Load feedback from database if available
        if self.db_session:
            try:
                from app import Feedback

                feedbacks = self.db_session.query(Feedback).all()
                self.feedback_history = [
                    (f.feedback_text, f.sentiment_label) for f in feedbacks
                ]
                all_texts.extend([f.feedback_text for f in feedbacks])
            except Exception as e:
                print(f"Could not load feedback history: {e}")

        if all_texts:
            self.vectorizer.fit(all_texts)

    def update_with_new_feedback(
        self, feedback_text: str, sentiment_label: str, domain: str = "engineering"
    ):
        """Update the engine with new feedback to improve future suggestions"""
        self.feedback_history.append((feedback_text, sentiment_label, domain))

        # Retrain vectorizer periodically (every 10 feedbacks)
        if len(self.feedback_history) % 10 == 0:
            all_texts = []
            for category in self.suggestion_db.values():
                for keyword in category["keywords"]:
                    all_texts.append(keyword)
            # Add domain-specific keywords
            for domain_data in self.domain_specific_db.values():
                for category in domain_data.values():
                    if isinstance(category, dict) and "keywords" in category:
                        all_texts.extend(category["keywords"])
            all_texts.extend([fb[0] for fb in self.feedback_history])

            if all_texts:
                self.vectorizer.fit(all_texts)

    def find_similar_past_feedback(
        self, text: str, top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """Find similar feedback from history using semantic similarity"""
        if not self.feedback_history:
            return []

        try:
            text_vector = self.vectorizer.transform([text])
            feedback_texts = [fb[0] for fb in self.feedback_history]
            feedback_vectors = self.vectorizer.transform(feedback_texts)

            similarities = cosine_similarity(text_vector, feedback_vectors)[0]
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Only include somewhat similar feedback
                    results.append(
                        (
                            self.feedback_history[idx][0],
                            self.feedback_history[idx][1],
                            similarities[idx],
                        )
                    )

            return results
        except Exception as e:
            print(f"Error finding similar feedback: {e}")
            return []

    def extract_key_themes(
        self, text: str, domain: str = "engineering"
    ) -> List[Tuple[str, float]]:
        """Extract key themes from feedback text using advanced NLP with context awareness"""
        text_lower = text.lower()
        themes = []

        # Use TF-IDF to find important keywords
        try:
            text_vector = self.vectorizer.transform([text_lower])
            feature_names = self.vectorizer.get_feature_names_out()
            scores = text_vector.toarray()[0]

            # Get top keywords with scores
            top_indices = np.argsort(scores)[-10:][::-1]
            keywords = [
                (feature_names[i], scores[i]) for i in top_indices if scores[i] > 0
            ]
        except:
            keywords = []

        # First, check domain-specific categories
        if domain in self.domain_specific_db:
            for category, category_data in self.domain_specific_db[domain].items():
                if isinstance(category_data, dict) and "keywords" in category_data:
                    category_score = 0
                    matched_keywords = []

                    # Direct keyword matching with weight
                    for keyword in category_data["keywords"]:
                        # Full word matching with boundaries
                        pattern = r"\b" + re.escape(keyword) + r"\b"
                        matches = re.findall(pattern, text_lower)
                        if matches:
                            match_count = len(matches)
                            category_score += (
                                match_count * 3
                            )  # Higher weight for domain-specific
                            matched_keywords.append(keyword)

                    # Partial matching for compound keywords
                    for keyword in category_data["keywords"]:
                        if (
                            len(keyword) > 4
                            and keyword in text_lower
                            and keyword not in matched_keywords
                        ):
                            category_score += 1.5
                            matched_keywords.append(keyword)

                    # Boost score based on TF-IDF matches
                    for kw, score in keywords:
                        if any(
                            kw in cat_kw or cat_kw in kw
                            for cat_kw in category_data["keywords"]
                        ):
                            category_score += (
                                score * 4
                            )  # Higher weight for domain-specific TF-IDF matches

                    if category_score > 0:
                        themes.append(
                            (f"{domain}_{category}", category_score, matched_keywords)
                        )

        # Enhanced matching with context and synonyms for general categories
        for category, data in self.suggestion_db.items():
            category_score = 0
            matched_keywords = []

            # Direct keyword matching with weight
            for keyword in data["keywords"]:
                # Full word matching with boundaries
                pattern = r"\b" + re.escape(keyword) + r"\b"
                matches = re.findall(pattern, text_lower)
                if matches:
                    match_count = len(matches)
                    category_score += match_count * 2  # Weight for exact matches
                    matched_keywords.append(keyword)

            # Partial matching for compound keywords
            for keyword in data["keywords"]:
                if (
                    len(keyword) > 4
                    and keyword in text_lower
                    and keyword not in matched_keywords
                ):
                    category_score += 1
                    matched_keywords.append(keyword)

            # Boost score based on TF-IDF matches
            for kw, score in keywords:
                if any(kw in cat_kw or cat_kw in kw for cat_kw in data["keywords"]):
                    category_score += score * 3  # Increased weight for TF-IDF matches

            # Contextual boosting - look for related phrases
            context_phrases = {
                "communication": [
                    "need to improve communication",
                    "better at explaining",
                    "more clarity",
                    "hard to understand",
                    "couldn't explain",
                    "poor communication",
                    "hesitant speaking",
                ],
                "preparation": [
                    "not prepared",
                    "lacked knowledge",
                    "insufficient preparation",
                    "unprepared for questions",
                    "didn't know",
                    "poor understanding",
                ],
                "technical_skills": [
                    "weak in coding",
                    "algorithm problems",
                    "poor technical",
                    "couldn't solve",
                    "coding issues",
                    "logic errors",
                ],
                "confidence": [
                    "too nervous",
                    "lacked confidence",
                    "very anxious",
                    "seemed hesitant",
                    "not confident",
                    "appeared stressed",
                ],
                "projects_experience": [
                    "no projects",
                    "weak portfolio",
                    "limited experience",
                    "no practical work",
                    "few projects",
                    "insufficient examples",
                ],
            }

            if category in context_phrases:
                for phrase in context_phrases[category]:
                    if phrase in text_lower:
                        category_score += 3  # Boost for contextual phrases
                        if phrase.split()[0] not in matched_keywords:
                            matched_keywords.append(phrase.split()[0])

            if category_score > 0:
                themes.append((category, category_score, matched_keywords))

        # Sort by score
        themes.sort(key=lambda x: x[1], reverse=True)
        return themes

    def analyze_sentiment_depth(self, text: str) -> Dict:
        """
        Perform deep sentiment analysis using hybrid approach:
        - Transformer model (pre-trained BERT)
        - Keyword detection
        - TextBlob fallback
        """
        # Use the hybrid sentiment analyzer
        label, confidence, details = analyze_sentiment(text)

        # Get TextBlob polarity for compatibility
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Map label to tone
        tone_map = {
            "Positive": "positive",
            "Negative": "critical",
            "Neutral": "neutral",
        }

        # Get indicator counts from details if available
        negative_count = details.get("negative_count", 0)
        positive_count = details.get("positive_count", 0)
        neutral_count = details.get("neutral_count", 0)
        constructive_count = details.get("constructive_count", 0)

        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "sentiment_label": label,
            "confidence": confidence,
            "method": details.get("method", "unknown"),
            "negative_indicators": negative_count,
            "positive_indicators": positive_count,
            "constructive_indicators": constructive_count,
            "neutral_indicators": neutral_count,
            "overall_tone": tone_map.get(label, "neutral"),
        }

    # Keep old implementation as backup
    def analyze_sentiment_depth_legacy(self, text: str) -> Dict:
        """Legacy sentiment analysis with comprehensive keyword detection"""
        blob = TextBlob(text)

        # Basic sentiment
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Comprehensive negative indicators (ability/knowledge deficits)
        negative_indicators = [
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
            "should improve",
            "needs work",
            "needs attention",
            "requires improvement",
            "needs to learn",
            "must learn",
            "should learn",
            "needs practice",
            "requires practice",
            "not good",
            "not great",
            "not strong",
            "not clear",
            "no understanding",
            "no knowledge",
            "no grasp",
            "no clarity",
            "little understanding",
            "limited knowledge",
            "minimal grasp",
            "doesn't understand",
            "does not understand",
            "hasn't grasped",
            "below average",
            "below expectations",
            "subpar",
            "unsatisfactory",
            "disappointed",
            "disappointing",
            "frustrating",
            "frustrated",
            "concerning",
            "concern",
            "worried",
            "worrying",
            "worrisome",
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
            "missing",
            "absent",
            "incomplete",
            "slow",
            "slower",
            "slowest",
            "behind",
            "average",
            "mediocre",
            "okay",
            "acceptable",
            "basic",
            "fundamental gaps",
            "foundational issues",
        ]

        # Comprehensive positive indicators (achievements/excellence)
        positive_indicators = [
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
            "good",
            "better",
            "best",
            "well",
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
            "successful",
            "achieve",
            "achieves",
            "achieved",
            "achieving",
            "achievement",
            "progress",
            "progressing",
            "progressed",
            "progressive",
            "improve",
            "improves",
            "improved",
            "improving",
            "improvement",
            "develop",
            "develops",
            "developed",
            "developing",
            "development",
            "advance",
            "advances",
            "advanced",
            "advancing",
            "enhance",
            "enhances",
            "enhanced",
            "enhancing",
            "thorough",
            "comprehensive",
            "complete",
            "detailed",
            "clear",
            "clarity",
            "clearer",
            "clearest",
            "deep",
            "deeper",
            "deepest",
            "depth",
            "understand",
            "understands",
            "understanding",
            "understood",
            "grasp",
            "grasps",
            "grasped",
            "grasping",
            "innovative",
            "creative",
            "original",
            "efficient",
            "effective",
            "productive",
            "consistent",
            "reliable",
            "dependable",
            "professional",
            "polished",
            "refined",
            "collaborative",
            "cooperative",
            "team player",
            "proactive",
            "initiative",
            "self-motivated",
            "enthusiastic",
            "passionate",
            "dedicated",
            "committed",
            "above average",
            "exceeds expectations",
            "surpasses",
        ]

        constructive_indicators = [
            "improve",
            "develop",
            "enhance",
            "better",
            "growth",
            "potential",
            "opportunity",
            "suggestion",
            "recommend",
            "consider",
            "explore",
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
            "fair",
            "reasonable",
            "adequate",
            "mixed",
            "varied",
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
            "certain areas",
            "some aspects",
            "in parts",
            "shows potential",
            "room for",
            "could be",
            "generally",
            "usually",
            "mostly",
            "fairly",
            "progressing",
            "developing",
            "learning",
            "working on",
            "steady",
            "consistent effort",
            "making effort",
            "attentive",
            "participates",
            "engaged",
            "present",
            "follows",
            "completes",
            "submits",
            "attends",
            "basic understanding",
            "fundamental grasp",
            "foundational knowledge",
        ]

        text_lower = text.lower()

        negative_count = sum(
            1 for indicator in negative_indicators if indicator in text_lower
        )
        positive_count = sum(
            1 for indicator in positive_indicators if indicator in text_lower
        )
        constructive_count = sum(
            1 for indicator in constructive_indicators if indicator in text_lower
        )
        neutral_count = sum(
            1 for indicator in neutral_indicators if indicator in text_lower
        )

        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "negative_indicators": negative_count,
            "positive_indicators": positive_count,
            "constructive_indicators": constructive_count,
            "neutral_indicators": neutral_count,
            "overall_tone": self._determine_tone(
                polarity,
                negative_count,
                positive_count,
                constructive_count,
                neutral_count,
            ),
        }

    def _determine_tone(
        self,
        polarity: float,
        negative: int,
        positive: int,
        constructive: int,
        neutral: int = 0,
    ) -> str:
        """Determine the overall tone of feedback with neutral detection"""
        # Strong neutral indicators take priority
        if neutral >= 3:
            return "neutral"

        # Constructive feedback
        if constructive >= 2:
            return "constructive"

        # Clear positive feedback
        elif positive > negative and polarity > 0.1:
            return "positive"

        # Clear negative/critical feedback
        elif negative > positive and polarity < -0.1:
            return "critical"

        # Mixed or neutral by default
        else:
            return "neutral"

    def determine_skill_level(
        self, themes: List[Tuple], sentiment_analysis: Dict
    ) -> str:
        """Determine appropriate skill level for suggestions"""
        # Simple heuristic - can be enhanced with user profile data
        if sentiment_analysis["constructive_indicators"] >= 3:
            return "intermediate"
        elif sentiment_analysis["negative_indicators"] >= 3:
            return "beginner"
        else:
            return "intermediate"

    def _try_ollama_suggestion(self, text: str, domain: str) -> Dict:
        """Try to generate suggestion using Ollama LLM. Returns parsed JSON or raises."""
        if not _OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama not available")

        # Check cache first for speed
        cache_key = hashlib.md5(f"{text}:{domain}".encode()).hexdigest()
        if cache_key in self.llm_cache:
            logging.info("✨ Returning cached LLM response")
            return self.llm_cache[cache_key]

        # Enhanced prompt for comprehensive, detailed suggestions
        from prompt_templates import SUGGESTION_PROMPT

        # Build a short domain note to disambiguate terms and nudge specificity
        domain_notes = {
            "law": (
                "In this context, IPC refers to the Indian Penal Code. Use legal vocabulary, cite IPC section numbers, case briefs, bare acts, SCC Online, LiveLaw, Lawctopus, and legal drafting resources. Avoid engineering meanings of IPC."
            ),
            "medical": (
                "Use precise medical terminology, clinical case studies, textbooks, PubMed, Osmosis, Coursera medical tracks, Anki decks, and evidence-based sources."
            ),
            "engineering": (
                "Use programming languages, frameworks, GitHub projects, LeetCode/HackerRank, system design, and tooling specifics."
            ),
            "management": (
                "Use business case frameworks (SWOT, 4P/7P, Porter), analytics dashboards, Excel/Sheets, Power BI/Tableau, OKRs, and stakeholder communication."
            ),
        }
        domain_note = domain_notes.get(
            domain, "Tailor all content tightly to the domain."
        )

        # Format the prompt with actual values (include domain and note for specificity)
        prompt = SUGGESTION_PROMPT.format(
            feedback_text=text,
            sentiment="analyzing",
            level="professional",
            domain=domain,
            domain_note=domain_note,
        )

        # Correct Ollama Python client usage
        import ollama

        # Call ollama.generate with OPTIMIZED parameters for BALANCED speed and quality
        # Optimized settings: Good detail while keeping response under 120 seconds
        resp = ollama.generate(
            model=OLLAMA_MODEL,  # Use configured model (default: gemma3)
            prompt=prompt,
            options={
                "num_predict": 900,  # With 3 items per section, 900 is sufficient and faster
                "temperature": 0.45,  # Slightly lower for consistency and brevity
                "top_k": 25,  # Reduced for faster token selection
                "top_p": 0.85,  # Balanced sampling
                "num_ctx": 1536,  # Slightly reduced context for speed
                "num_thread": 8,  # Max CPU parallelization
                "repeat_penalty": 1.15,  # Stronger penalty to avoid repetition
                "num_gpu": 1,  # Use GPU if available
            },
        )

        # Response is a dict with 'response' key containing the text
        raw_text = resp.get("response", "")

        # Log response length to track truncation
        logging.info(f"Ollama response length: {len(raw_text)} characters")

        logging.info("Ollama raw response: %s", raw_text[:500])

        # Clean markdown code blocks if present (```json ... ```)
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            # Remove markdown code fence
            lines = cleaned_text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        # Parse JSON with improved fallback extraction and auto-completion for truncated responses
        try:
            parsed = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logging.warning(
                f"JSON parse error: {e}. Attempting to fix truncated JSON..."
            )
            # Try extracting and auto-completing {...} block
            start = cleaned_text.find("{")
            if start != -1:
                candidate = cleaned_text[start:]

                # Enhanced truncation fixing
                try:
                    # First try: find last complete closing brace
                    end = candidate.rfind("}")
                    if end != -1:
                        candidate = candidate[: end + 1]
                        parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    # Second try: Aggressive completion of truncated JSON
                    # Remove any trailing incomplete text after last comma or bracket
                    for i in range(len(candidate) - 1, -1, -1):
                        if candidate[i] in [",", "[", "{"]:
                            candidate = candidate[: i + 1]
                            break

                    # Count unclosed structures
                    open_braces = candidate.count("{") - candidate.count("}")
                    open_brackets = candidate.count("[") - candidate.count("]")
                    open_quotes = candidate.count('"') % 2

                    # Build completion string
                    completion = ""
                    if open_quotes != 0:
                        completion += '"'  # Close unterminated string

                    # Close arrays first, then objects
                    completion += "]" * open_brackets
                    completion += "}" * open_braces

                    candidate_fixed = candidate + completion
                    logging.info(
                        f"Attempting auto-completed JSON with {open_braces} braces, {open_brackets} brackets"
                    )
                    try:
                        parsed = json.loads(candidate_fixed)
                    except json.JSONDecodeError:
                        # Last resort: return minimal valid structure
                        logging.error("Could not parse JSON, using fallback structure")
                        raise
            else:
                raise

        # Cache the successful result
        if len(self.llm_cache) >= self.cache_max_size:
            # Remove oldest entry (simple FIFO)
            self.llm_cache.pop(next(iter(self.llm_cache)))
        self.llm_cache[cache_key] = parsed

        # Log the final parsed structure to verify completeness
        logging.info(f"✅ Successfully parsed JSON with fields: {list(parsed.keys())}")
        logging.info(
            f"   - immediate_actions: {len(parsed.get('immediate_actions', []))} items"
        )
        logging.info(f"   - weekly_goals: {len(parsed.get('weekly_goals', []))} items")
        logging.info(f"   - resources: {len(parsed.get('resources', []))} items")
        logging.info(
            f"   - success_metrics: {len(parsed.get('success_metrics', []))} items"
        )

        return parsed

    def generate_comprehensive_suggestion(
        self, text: str, sentiment_label: str, domain: str = "engineering"
    ) -> Dict:
        """Generate comprehensive, personalized suggestions based on feedback and history"""

        # Try Ollama first if available
        print(f"🔍 Ollama available: {_OLLAMA_AVAILABLE}")
        if _OLLAMA_AVAILABLE:
            try:
                print(f"🚀 Calling Ollama for feedback: {text[:50]}...")
                parsed = self._try_ollama_suggestion(text, domain)
                # Retry once on parse failure
                if not isinstance(parsed, dict):
                    logging.warning("Ollama returned non-dict, retrying")
                    parsed = self._try_ollama_suggestion(text, domain)

                print("✅ Ollama suggestion generated successfully")

                # Direct model output path: keep Ollama content as the single source of truth
                # Normalize keys minimally so the frontend can render without defaults

                def to_string_list(val):
                    if not val:
                        return []
                    if isinstance(val, list):
                        return [
                            str(x)
                            for x in val
                            if isinstance(x, (str, int, float)) and str(x).strip()
                        ]
                    if isinstance(val, (str, int, float)):
                        return [str(val)]
                    return []

                # Map potential alternate keys produced by the model
                weekly_goals = parsed.get("weekly_goals") or parsed.get("weekly_plan")
                primary_focus = (
                    parsed.get("primary_focus")
                    or parsed.get("primary_aspect")
                    or (
                        parsed.get("aspects", [{}])[0].get("name")
                        if parsed.get("aspects")
                        else None
                    )
                )

                direct = {
                    "type": "llm",
                    "domain": domain,
                    "title": parsed.get("title")
                    or f"{domain.title()} Development Plan",
                    "primary_focus": primary_focus or "communication",
                    "urgency": parsed.get("urgency") or "medium",
                    "immediate_actions": to_string_list(
                        parsed.get("immediate_actions")
                    )[:3],
                    "weekly_goals": to_string_list(weekly_goals)[:3],
                    "resources": to_string_list(parsed.get("resources"))[:3],
                    "success_metrics": to_string_list(parsed.get("success_metrics"))[
                        :3
                    ],
                    "timeline": parsed.get("timeline", "6-8 weeks"),
                }

                return direct
            except Exception as e:
                print(f"❌ Ollama failed: {e}")
                logging.exception(
                    "Ollama generation failed, falling back to rule-based: %s", e
                )
                # Fall through to existing logic below

        # Existing rule-based suggestion logic
        themes = self.extract_key_themes(text, domain)
        sentiment_analysis = self.analyze_sentiment_depth(text)
        skill_level = self.determine_skill_level(themes, sentiment_analysis)

        # Find similar past feedback to provide context
        similar_feedback = self.find_similar_past_feedback(text)

        # Analyze patterns from similar feedback
        pattern_insights = self._analyze_feedback_patterns(similar_feedback)

        if not themes:
            return self._generate_generic_suggestion(
                sentiment_label, sentiment_analysis, pattern_insights, text, domain
            )

        # Get the top theme
        primary_theme = themes[0][0]
        matched_keywords = themes[0][2]

        # Check if this is a domain-specific theme
        suggestion_data = None
        is_domain_specific = False

        # First check domain-specific suggestions
        if domain in self.domain_specific_db:
            for category, category_data in self.domain_specific_db[domain].items():
                if isinstance(category_data, dict) and "suggestions" in category_data:
                    # Check if any keywords match
                    if any(
                        kw in matched_keywords
                        for kw in category_data.get("keywords", [])
                    ):
                        suggestion_data = category_data["suggestions"].get(
                            skill_level, category_data["suggestions"].get("beginner")
                        )
                        primary_theme = f"{domain}_{category}"
                        is_domain_specific = True
                        break

        # Fall back to general suggestions if no domain-specific match
        if not suggestion_data and primary_theme in self.suggestion_db:
            suggestion_data = self.suggestion_db[primary_theme]["suggestions"].get(
                skill_level,
                self.suggestion_db[primary_theme]["suggestions"]["beginner"],
            )

        if not suggestion_data:
            return self._generate_generic_suggestion(
                sentiment_label, sentiment_analysis, pattern_insights, text, domain
            )

        # Customize based on specific keywords found AND historical patterns
        # But skip customization for domain-specific suggestions to preserve their content
        if is_domain_specific:
            customized_suggestion = suggestion_data.copy()
        else:
            customized_suggestion = self._customize_suggestion(
                suggestion_data,
                matched_keywords,
                text,
                sentiment_analysis,
                pattern_insights,
            )

        # Add variation to make suggestions feel unique (only for non-domain-specific)
        if not is_domain_specific:
            customized_suggestion = self._vary_suggestion_wording(
                customized_suggestion, text
            )

        result = {
            "primary_focus": primary_theme,
            "confidence_score": min(themes[0][1] / 5.0, 1.0),  # Normalize to 0-1
            "skill_level": skill_level,
            "sentiment_tone": sentiment_analysis["overall_tone"],
            "matched_keywords": matched_keywords,
            "domain": domain,
            "is_domain_specific": is_domain_specific,
            **customized_suggestion,
        }

        # Only add pattern insights for non-domain-specific suggestions
        if not is_domain_specific:
            result["similar_cases"] = len(similar_feedback)
            result["pattern_insights"] = pattern_insights

        return result

    def _analyze_feedback_patterns(self, similar_feedback: List[Tuple]) -> Dict:
        """Analyze patterns from similar historical feedback"""
        if not similar_feedback:
            return {
                "recurring_themes": [],
                "common_sentiments": "Not enough historical data",
                "trend": "No trend data available",
            }

        # Analyze sentiment distribution
        sentiments = [fb[1] for fb in similar_feedback]
        sentiment_counts = defaultdict(int)
        for sent in sentiments:
            sentiment_counts[sent] += 1

        most_common_sentiment = (
            max(sentiment_counts.items(), key=lambda x: x[1])[0]
            if sentiment_counts
            else "Unknown"
        )

        # Extract common themes
        all_text = " ".join([fb[0].lower() for fb in similar_feedback])
        recurring_themes = []

        for category, data in self.suggestion_db.items():
            theme_score = sum(1 for kw in data["keywords"] if kw in all_text)
            if theme_score > 0:
                recurring_themes.append((category, theme_score))

        recurring_themes.sort(key=lambda x: x[1], reverse=True)

        return {
            "recurring_themes": [theme[0] for theme in recurring_themes[:3]],
            "common_sentiments": most_common_sentiment,
            "trend": f"Found {len(similar_feedback)} similar past feedback(s)",
            "sentiment_distribution": dict(sentiment_counts),
        }

    def _contextualize_actions(
        self, actions: List[str], feedback_text: str, keywords: List[str]
    ) -> List[str]:
        """Make actions more contextual by referencing the actual feedback"""
        seed = hashlib.md5((feedback_text + "context").encode()).hexdigest()
        base_seed = int(seed[:8], 16)

        # Extract key phrases from feedback (first few words that aren't common)
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "be",
            "been",
            "being",
        }
        words = [
            w
            for w in feedback_text.lower().split()
            if w not in common_words and len(w) > 3
        ]
        key_phrases = words[:3] if len(words) >= 3 else words

        # Variation templates for making suggestions sound different
        action_prefixes = [
            "Begin by",
            "Start with",
            "Focus on",
            "Prioritize",
            "Take immediate action to",
            "Work on",
            "Concentrate on",
            "Make it a priority to",
            "Address this by",
            "Tackle this by",
        ]

        contextualized = []
        for i, action in enumerate(actions):
            # Add variety by deterministically selecting prefixes
            choice = (base_seed + i) % 10
            if choice < 4 and i < 2:  # 40% chance to add prefix for first two actions
                prefix = action_prefixes[(base_seed + i) % len(action_prefixes)]
                # Make first letter lowercase for smooth prefix integration
                action_lower = action[0].lower() + action[1:]
                contextualized.append(f"{prefix} {action_lower}")
            else:
                contextualized.append(action)

        return contextualized

    def _vary_suggestion_wording(self, suggestion: Dict, feedback_text: str) -> Dict:
        """Add variation to suggestion wording to make it feel more personalized"""
        seed = hashlib.md5(feedback_text.encode()).hexdigest()
        base_seed = int(seed[:8], 16)

        # Vary the title with more options
        if "title" in suggestion:
            title_variations = {
                "Communication Skills Development Plan": [
                    "Effective Communication Roadmap",
                    "Communication Excellence Program",
                    "Clear Communication Strategy",
                    "Professional Communication Development",
                    "Articulation Improvement Framework",
                    "Message Clarity Enhancement Plan",
                    "Interpersonal Communication Advancement",
                    "Expressive Skills Development Path",
                ],
                "Advanced Communication Mastery": [
                    "Communication Leadership Program",
                    "Strategic Communication Excellence",
                    "Senior Communication Skills Development",
                    "Executive Communication Mastery",
                    "High-Impact Communication Framework",
                    "Influential Communication Strategy",
                    "Advanced Articulation Leadership",
                    "Expert-Level Communication Program",
                ],
                "Time Management Foundation": [
                    "Productivity Enhancement Plan",
                    "Time Optimization Strategy",
                    "Efficient Time Management Program",
                    "Deadline Mastery Framework",
                    "Schedule Optimization Roadmap",
                    "Priority Management Development",
                    "Efficiency Building Strategy",
                    "Temporal Organization System",
                ],
                "Advanced Time Optimization": [
                    "Peak Productivity System",
                    "Strategic Time Management",
                    "Advanced Efficiency Framework",
                    "Time Leadership Excellence",
                    "Elite Performance Scheduling",
                    "Executive Time Mastery",
                    "High-Efficiency Operating Model",
                    "Premium Productivity Strategy",
                ],
                "Technical Excellence Development": [
                    "Code Quality Improvement Plan",
                    "Technical Skills Enhancement",
                    "Software Craftsmanship Program",
                    "Development Quality Framework",
                    "Engineering Excellence Roadmap",
                    "Technical Proficiency Growth Path",
                    "Quality-Driven Development Strategy",
                    "Codebase Excellence Initiative",
                ],
                "Senior Technical Leadership": [
                    "Technical Leadership Excellence",
                    "Advanced Engineering Leadership",
                    "Senior Developer Mastery",
                    "Technical Team Leadership Program",
                    "Engineering Leadership Framework",
                    "Technical Direction Strategy",
                    "Senior Engineering Excellence",
                    "Tech Lead Development Path",
                ],
                "Leadership Foundations": [
                    "Emerging Leader Development",
                    "Leadership Skills Framework",
                    "Team Leadership Essentials",
                    "Professional Leadership Growth",
                    "Foundational Leadership Program",
                    "Leader Capability Building",
                    "Management Fundamentals Path",
                    "Leadership Competency Development",
                ],
                "Strategic Leadership Excellence": [
                    "Executive Leadership Development",
                    "Advanced Leadership Mastery",
                    "Strategic Team Leadership",
                    "Senior Leadership Program",
                    "Visionary Leadership Framework",
                    "High-Impact Leadership Strategy",
                    "Strategic Management Excellence",
                    "Executive-Level Leadership Path",
                ],
                "Continuous Learning Framework": [
                    "Ongoing Development Strategy",
                    "Perpetual Learning Program",
                    "Knowledge Expansion Roadmap",
                    "Skill Evolution Framework",
                    "Growth Mindset Development",
                    "Continuous Improvement Path",
                    "Learning Agility Enhancement",
                    "Professional Development System",
                ],
            }

            original_title = suggestion["title"]
            if original_title in title_variations:
                options = title_variations[original_title]
                suggestion["title"] = options[base_seed % len(options)]

        # Vary resource descriptions with deterministic selection
        if "resources" in suggestion:
            resource_variations = {
                "Book:": [
                    "Reading:",
                    "Recommended book:",
                    "Book recommendation:",
                    "Study:",
                    "Literature:",
                    "Text:",
                ],
                "Course:": [
                    "Training:",
                    "Learn from:",
                    "Online course:",
                    "Educational resource:",
                    "Program:",
                    "Curriculum:",
                ],
                "Tool:": [
                    "Utilize:",
                    "Software:",
                    "Platform:",
                    "Use tool:",
                    "Application:",
                    "System:",
                ],
                "App:": [
                    "Application:",
                    "Software:",
                    "Tool:",
                    "Platform:",
                    "Digital tool:",
                    "Mobile app:",
                ],
                "Workshop:": [
                    "Training:",
                    "Seminar:",
                    "Program:",
                    "Course:",
                    "Session:",
                    "Masterclass:",
                ],
                "Practice:": [
                    "Exercise:",
                    "Activity:",
                    "Training:",
                    "Drill:",
                    "Routine:",
                    "Habit:",
                ],
                "Technique:": [
                    "Method:",
                    "Approach:",
                    "Strategy:",
                    "System:",
                    "Framework:",
                    "Process:",
                ],
                "Platform:": [
                    "Service:",
                    "System:",
                    "Resource:",
                    "Tool:",
                    "Application:",
                    "Site:",
                ],
                "Method:": [
                    "Technique:",
                    "Approach:",
                    "System:",
                    "Strategy:",
                    "Framework:",
                    "Process:",
                ],
            }
            varied_resources = []
            for i, resource in enumerate(suggestion["resources"]):
                modified = False
                for old, variations in resource_variations.items():
                    if old in resource:
                        choice_seed = (base_seed + i) % len(variations)
                        new = variations[choice_seed]
                        resource = resource.replace(old, new)
                        modified = True
                        break
                varied_resources.append(resource)
            suggestion["resources"] = varied_resources

        return suggestion

    def _customize_suggestion(
        self,
        base_suggestion: Dict,
        keywords: List[str],
        original_text: str,
        sentiment_analysis: Dict,
        pattern_insights: Dict = None,
    ) -> Dict:
        """Customize suggestions based on specific context and historical patterns with dynamic variations"""
        customized = base_suggestion.copy()

        # Determine category from keywords
        category = None
        for cat, data in self.suggestion_db.items():
            if any(kw in data["keywords"] for kw in keywords):
                category = cat
                break

        # Get skill level
        skill_level = self.determine_skill_level(
            [(cat, 1, keywords) for cat in [category] if category], sentiment_analysis
        )

        # Replace immediate actions with varied versions
        if category and category in self.suggestion_variations:
            varied_actions = []
            category_variations = (
                self.suggestion_variations[category]
                .get(skill_level, {})
                .get("actions", [])
            )

            for i in range(min(3, len(category_variations))):
                varied_action = self._get_varied_suggestion_component(
                    category, skill_level, "actions", i, original_text
                )
                if varied_action:
                    varied_actions.append(varied_action)

            if varied_actions:
                customized["immediate_actions"] = varied_actions

        # Replace weekly goals with varied versions
        if category and category in self.suggestion_variations:
            varied_goals = []
            category_variations = (
                self.suggestion_variations[category]
                .get(skill_level, {})
                .get("goals", [])
            )

            for i in range(min(3, len(category_variations))):
                varied_goal = self._get_varied_suggestion_component(
                    category, skill_level, "goals", i, original_text
                )
                if varied_goal:
                    varied_goals.append(varied_goal)

            if varied_goals:
                customized["weekly_goals"] = varied_goals

        # Add context-specific immediate actions
        context_actions = []
        if any(
            kw in ["preparation", "prepare", "unprepared", "research"]
            for kw in keywords
        ):
            options = [
                "Create a detailed study plan covering all potential interview topics for this role",
                "Research the company's products, mission, and recent developments thoroughly before your next interview",
                "Build a comprehensive preparation checklist and dedicate specific time daily to each topic",
                "Develop a structured study schedule focusing on areas commonly asked in interviews",
            ]
            seed = hashlib.md5(original_text.encode()).hexdigest()
            context_actions.append(options[int(seed[:8], 16) % len(options)])

        if any(
            kw in ["communication", "unclear", "confusing", "explain", "articulate"]
            for kw in keywords
        ):
            options = [
                "Practice answering common interview questions out loud, recording yourself to identify improvement areas",
                "Join mock interview sessions with peers or mentors to get feedback on your communication style",
                "Work on structuring your responses using frameworks like STAR for clearer communication",
                "Schedule practice sessions where you explain technical concepts to non-technical friends",
            ]
            seed = hashlib.md5((original_text + "comm").encode()).hexdigest()
            context_actions.append(options[int(seed[:8], 16) % len(options)])

        if any(kw in ["nervous", "confidence", "anxiety", "stress"] for kw in keywords):
            options = [
                "Practice mock interviews in increasingly challenging settings to build comfort with the format",
                "Develop a pre-interview routine including breathing exercises and positive visualization",
                "Start with lower-pressure practice interviews to gradually build your confidence",
                "Work on power poses and confidence-building techniques before interview situations",
            ]
            seed = hashlib.md5((original_text + "conf").encode()).hexdigest()
            context_actions.append(options[int(seed[:8], 16) % len(options)])

        if context_actions:
            customized["immediate_actions"] = context_actions + customized.get(
                "immediate_actions", []
            )

        # Add insights from historical patterns
        if pattern_insights and pattern_insights.get("recurring_themes"):
            recurring = (
                pattern_insights["recurring_themes"][0]
                if pattern_insights["recurring_themes"]
                else None
            )
            if recurring:
                alert_options = [
                    f"⚠️ Pattern Detected: This {recurring.replace('_', ' ')} concern has appeared in similar feedback. Address it systematically.",
                    f"⚠️ Recurring Theme: Past feedback shows {recurring.replace('_', ' ')} challenges. Prioritize structured improvement.",
                    f"⚠️ Historical Insight: Similar feedback highlights {recurring.replace('_', ' ')} issues. Focus on systematic resolution.",
                    f"⚠️ Trend Alert: {recurring.replace('_', ' ')} appears in related feedback. Take deliberate action to improve.",
                ]
                seed = hashlib.md5((original_text + "pattern").encode()).hexdigest()
                customized["immediate_actions"].insert(
                    0, alert_options[int(seed[:8], 16) % len(alert_options)]
                )

        if pattern_insights and pattern_insights.get("trend"):
            customized["historical_context"] = pattern_insights["trend"]

        # Add urgency level based on sentiment
        if sentiment_analysis["negative_indicators"] >= 3:
            customized["urgency"] = "high"
            timeline_options = [
                "Start implementing within 24-48 hours",
                "Begin taking action within the next 1-2 days",
                "Initiate improvements in the next day or two",
                "Launch implementation within 24 to 48 hours",
            ]
        else:
            customized["urgency"] = "medium"
            timeline_options = [
                "Begin implementation within the next week",
                "Start putting this into practice over the coming week",
                "Initiate action within the next 7 days",
                "Launch improvements in the week ahead",
            ]

        seed = hashlib.md5((original_text + "timeline").encode()).hexdigest()
        customized["timeline"] = timeline_options[
            int(seed[:8], 16) % len(timeline_options)
        ]

        # Add specific metrics to track progress
        customized["success_metrics"] = self._generate_success_metrics(
            keywords, original_text
        )

        return customized

    def _generate_success_metrics(
        self, keywords: List[str], feedback_text: str = ""
    ) -> List[str]:
        """Generate specific metrics to track improvement with varied wording"""
        metrics = []
        seed = hashlib.md5(feedback_text.encode()).hexdigest()
        base_seed = int(seed[:8], 16)

        if any(
            kw in ["communication", "presentation", "explain", "articulate"]
            for kw in keywords
        ):
            comm_metrics = [
                [
                    "Successfully explain 3+ technical concepts clearly in mock interviews",
                    "Achieve clear articulation in 90% of practice interview responses",
                    "Receive positive feedback on communication clarity from 3+ mock interviewers",
                    "Improve answer structure and clarity scores by 30% in practice sessions",
                ],
                [
                    "Reduce hesitation and filler words ('um', 'like') by 60% during responses",
                    "Cut down use of filler language by more than half in interview practice",
                    "Speak more confidently with 60% fewer verbal fillers",
                    "Decrease pauses and unclear phrasing by over half",
                ],
                [
                    "Successfully complete 5 mock interviews with improving feedback each time",
                    "Demonstrate measurable communication progress across multiple practice interviews",
                    "Show consistent improvement in interview communication assessments",
                    "Receive increasingly positive feedback on explanation clarity",
                ],
            ]
            for i, options in enumerate(comm_metrics):
                metrics.append(options[(base_seed + i) % len(options)])

        if any(
            kw in ["preparation", "prepare", "research", "knowledge", "understanding"]
            for kw in keywords
        ):
            prep_metrics = [
                [
                    "Complete 80% of planned study topics before your next interview",
                    "Cover all key subject areas with 80%+ confidence rating",
                    "Achieve thorough understanding of 4 out of 5 target interview topics",
                    "Successfully prepare 80% or more of identified weak areas",
                ],
                [
                    "Research and document insights about 5+ target companies thoroughly",
                    "Build comprehensive knowledge profiles for all companies you're applying to",
                    "Complete detailed company research for every interview opportunity",
                    "Demonstrate deep company knowledge in 90% of interview conversations",
                ],
                [
                    "Maintain consistent study schedule with 90% adherence rate",
                    "Stick to your preparation plan 9 out of 10 days",
                    "Follow through on daily study commitments at least 90% of the time",
                    "Achieve 90%+ consistency in executing your preparation routine",
                ],
            ]
            for i, options in enumerate(prep_metrics):
                metrics.append(options[(base_seed + i + 3) % len(options)])

        if any(
            kw in ["technical", "coding", "programming", "algorithm", "problem"]
            for kw in keywords
        ):
            tech_metrics = [
                [
                    "Solve 80% of medium difficulty problems independently within time limits",
                    "Successfully complete 4 out of 5 coding challenges without hints",
                    "Achieve 80%+ success rate on algorithm problems at your target difficulty",
                    "Independently solve most practice problems at medium level",
                ],
                [
                    "Explain your solution approach clearly in 90% of practice sessions",
                    "Articulate problem-solving logic effectively in 9 out of 10 attempts",
                    "Communicate your coding thought process clearly most of the time",
                    "Successfully verbalize your approach in 90%+ of practice interviews",
                ],
                [
                    "Build strong foundation covering all fundamental data structures and algorithms",
                    "Master core CS concepts with demonstrated proficiency across all basics",
                    "Achieve comprehensive understanding of essential algorithms and structures",
                    "Complete foundational knowledge covering 100% of interview basics",
                ],
            ]
            for i, options in enumerate(tech_metrics):
                metrics.append(options[(base_seed + i + 6) % len(options)])

        if any(
            kw in ["confidence", "nervous", "anxiety", "stress", "hesitant"]
            for kw in keywords
        ):
            confidence_metrics = [
                [
                    "Reduce anxiety levels by 50% through consistent mock interview practice",
                    "Feel noticeably more comfortable in interview settings after 2 weeks",
                    "Report lower stress levels in 70%+ of practice interview situations",
                    "Show measurable confidence improvement in self-assessments",
                ],
                [
                    "Successfully complete interviews without major nervousness affecting performance",
                    "Maintain composure and clear thinking in 80%+ of high-pressure questions",
                    "Demonstrate calm, confident demeanor in mock interview evaluations",
                    "Receive feedback noting improved confidence and poise",
                ],
            ]
            for i, options in enumerate(confidence_metrics):
                metrics.append(options[(base_seed + i + 9) % len(options)])

        if any(
            kw in ["project", "experience", "portfolio", "practical"] for kw in keywords
        ):
            project_metrics = [
                [
                    "Complete 2-3 quality projects demonstrating diverse skills within 6 weeks",
                    "Build portfolio of at least 2 substantial projects with full documentation",
                    "Develop 2-3 impressive projects showcasing different technical capabilities",
                    "Create multiple (2-3) well-executed projects for your portfolio",
                ],
                [
                    "Articulate project details and technical decisions confidently in mock interviews",
                    "Explain your projects clearly with 90%+ of questions answered satisfactorily",
                    "Demonstrate deep project knowledge when discussing in practice sessions",
                    "Successfully walk through projects without hesitation or gaps",
                ],
            ]
            for i, options in enumerate(project_metrics):
                metrics.append(options[(base_seed + i + 11) % len(options)])

        return (
            metrics
            if metrics
            else ["Demonstrate measurable improvement within 30 days"]
        )

    def _generate_generic_suggestion(
        self,
        sentiment_label: str,
        sentiment_analysis: Dict,
        pattern_insights: Dict = None,
        feedback_text: str = "",
        domain: str = "engineering",
    ) -> Dict:
        """Generate generic suggestions when no specific themes are identified with variations"""
        seed = hashlib.md5(feedback_text.encode()).hexdigest()
        base_seed = int(seed[:8], 16)

        base_suggestions = {
            "positive": {
                "titles": [
                    "Excellence Amplification Strategy",
                    "Success Acceleration Program",
                    "Performance Optimization Framework",
                    "Achievement Enhancement Plan",
                    "Strength Maximization Roadmap",
                    "Excellence Expansion Initiative",
                ],
                "action_sets": [
                    [
                        "Document your successful approaches and create templates for future use",
                        "Share your best practices with team members through mentoring or presentations",
                        "Identify one area where you can stretch beyond your current role",
                    ],
                    [
                        "Capture your winning strategies and develop reusable frameworks",
                        "Transfer your expertise to colleagues via coaching or teaching sessions",
                        "Pinpoint one domain for expanding your capabilities beyond current scope",
                    ],
                    [
                        "Record your effective methods and build standardized patterns",
                        "Disseminate your proven techniques to teammates through guidance or talks",
                        "Spot one sphere where you can extend past your present responsibilities",
                    ],
                    [
                        "Chronicle your success tactics and formulate repeatable templates",
                        "Distribute your effective practices among team via mentorship or workshops",
                        "Recognize one sector to grow beyond your existing boundaries",
                    ],
                ],
                "primary_focus": "growth_and_leadership",
            },
            "neutral": {
                "titles": [
                    "Performance Enhancement Plan",
                    "Capability Development Strategy",
                    "Professional Growth Framework",
                    "Skill Advancement Program",
                    "Performance Upgrade Roadmap",
                    "Competency Improvement Initiative",
                ],
                "action_sets": [
                    [
                        "Conduct a skills gap analysis to identify specific areas for improvement",
                        "Set up regular feedback sessions with your manager or mentor",
                        "Choose one new skill to develop over the next quarter",
                    ],
                    [
                        "Perform a capability assessment to pinpoint exact development opportunities",
                        "Establish recurring check-in meetings with your supervisor or coach",
                        "Select one fresh competency to build during the upcoming quarter",
                    ],
                    [
                        "Execute a proficiency evaluation to spot precise enhancement zones",
                        "Arrange consistent dialogue sessions with your leader or advisor",
                        "Pick one additional ability to cultivate over the next three months",
                    ],
                    [
                        "Run a competency audit to locate specific growth areas",
                        "Schedule periodic review conversations with your manager or guide",
                        "Identify one new expertise to strengthen throughout the coming quarter",
                    ],
                ],
                "primary_focus": "skill_development",
            },
            "negative": {
                "titles": [
                    "Comprehensive Improvement Strategy",
                    "Performance Recovery Framework",
                    "Turnaround Development Plan",
                    "Focused Enhancement Program",
                    "Corrective Action Roadmap",
                    "Intensive Growth Initiative",
                ],
                "action_sets": [
                    [
                        "Schedule a detailed feedback session to understand specific concerns",
                        "Create a 30-60-90 day improvement plan with measurable goals",
                        "Identify resources (training, mentoring, tools) to support your development",
                    ],
                    [
                        "Arrange an in-depth discussion to clarify exact areas of concern",
                        "Develop a 30-60-90 day enhancement roadmap with trackable objectives",
                        "Locate support mechanisms (courses, coaching, systems) for your growth",
                    ],
                    [
                        "Set up a comprehensive review meeting to pinpoint specific issues",
                        "Build a three-phase improvement plan with quantifiable targets",
                        "Discover available resources (education, guidance, platforms) for advancement",
                    ],
                    [
                        "Organize a thorough feedback conversation to understand particular challenges",
                        "Construct a 30-60-90 day action plan with measurable milestones",
                        "Find helpful assets (training programs, mentors, tools) to aid development",
                    ],
                ],
                "primary_focus": "performance_recovery",
            },
        }

        suggestion_data = base_suggestions.get(
            sentiment_label.lower(), base_suggestions["neutral"]
        )

        title = suggestion_data["titles"][base_seed % len(suggestion_data["titles"])]
        actions = suggestion_data["action_sets"][
            base_seed % len(suggestion_data["action_sets"])
        ]

        suggestion = {
            "title": title,
            "immediate_actions": actions.copy(),
            "primary_focus": suggestion_data["primary_focus"],
        }

        # Add pattern insights if available
        if pattern_insights and pattern_insights.get("recurring_themes"):
            insight_templates = [
                f"📊 Historical pattern shows focus needed on: {', '.join(pattern_insights['recurring_themes'][:2]).replace('_', ' ')}",
                f"📊 Similar feedback suggests prioritizing: {', '.join(pattern_insights['recurring_themes'][:2]).replace('_', ' ')}",
                f"📊 Past data indicates emphasis should be on: {', '.join(pattern_insights['recurring_themes'][:2]).replace('_', ' ')}",
                f"📊 Recurring themes point to: {', '.join(pattern_insights['recurring_themes'][:2]).replace('_', ' ')}",
            ]
            suggestion["immediate_actions"].insert(
                0, insight_templates[base_seed % len(insight_templates)]
            )

        timeline_options = [
            "Begin within the next week",
            "Start implementation over the coming week",
            "Initiate within the next 7 days",
            "Launch in the week ahead",
        ]

        metrics_options = [
            ["Regular progress check-ins show improvement trends"],
            ["Consistent monitoring reveals positive development patterns"],
            ["Ongoing assessments demonstrate advancement trajectory"],
            ["Periodic reviews indicate growth momentum"],
        ]

        return {
            "confidence_score": 0.5,
            "skill_level": "beginner",
            "sentiment_tone": sentiment_analysis["overall_tone"],
            "matched_keywords": [],
            **suggestion,
            "urgency": "medium",
            "timeline": timeline_options[base_seed % len(timeline_options)],
            "success_metrics": metrics_options[base_seed % len(metrics_options)],
            "pattern_insights": pattern_insights or {},
        }


# Global instance
suggestion_engine = AdvancedSuggestionEngine()
