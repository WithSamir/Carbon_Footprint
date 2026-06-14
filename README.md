# 🌿 CarbonTrace

> **Know Your Carbon. Own Your Impact.**

A full-stack carbon footprint tracking platform with AI-powered personalized recommendations, gamification, and a premium dark-mode UI.

## 🚀 Quick Start

### 1. Setup (first time only)
```bash
cd CarbonFootprint
bash setup.sh
```

### 2. Start the server
```bash
bash start.sh
```

### 3. Open your browser
Navigate to **http://localhost:5000**

---

## 🎭 Demo Account

After running `setup.sh`, a demo account is seeded with 6 months of data:

| Field    | Value                   |
|----------|-------------------------|
| Email    | `demo@carbontrace.app`  |
| Password | `demo1234`              |

---

## 📁 Project Structure

```
CarbonFootprint/
├── frontend/                   # Static HTML/CSS/JS frontend
│   ├── index.html              # Landing page
│   ├── calculator.html         # 4-step footprint wizard
│   ├── results.html            # Score reveal + benchmarks
│   ├── dashboard.html          # Tracking dashboard
│   ├── insights.html           # Personalized actions
│   ├── css/
│   │   ├── design-system.css   # Design tokens, components
│   │   └── components.css      # Page-specific styles
│   └── js/
│       ├── api.js              # Fetch wrapper + auth
│       └── ui.js               # Shared UI utilities
│
├── backend/                    # Python/Flask API
│   ├── app.py                  # App factory + routes
│   ├── config.py               # Configuration
│   ├── models.py               # SQLAlchemy models
│   ├── extensions.py           # Flask extensions
│   ├── seed_demo.py            # Demo data seeder
│   ├── requirements.txt
│   ├── data/
│   │   ├── emission_factors.json   # IPCC CO2e coefficients
│   │   └── actions_catalogue.json  # 18 curated green actions
│   ├── routes/
│   │   ├── auth.py             # /api/auth/*
│   │   ├── carbon.py           # /api/carbon/*
│   │   └── insights.py         # /api/insights/*
│   └── services/
│       ├── calculator.py       # Emission computation engine
│       ├── recommender.py      # AI recommendation engine
│       └── gamification.py     # XP, streaks, badges
│
├── setup.sh                    # One-command setup
└── start.sh                    # Quick start
```

---

## 🔌 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Sign in, get JWT |
| GET  | `/api/auth/me` | JWT | Current user |
| POST | `/api/carbon/calculate` | — | Calculate (no save) |
| POST | `/api/carbon/submit` | JWT | Calculate + save |
| GET  | `/api/carbon/history` | JWT | All entries |
| GET  | `/api/carbon/summary` | JWT | Dashboard data |
| GET  | `/api/insights/recommendations` | JWT | Ranked actions |
| POST | `/api/insights/actions/commit` | JWT | Pledge an action |
| POST | `/api/insights/actions/complete` | JWT | Mark completed |
| GET  | `/api/insights/actions/my` | JWT | My pledges |

---

## 🌱 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, Vanilla CSS, Vanilla JS |
| Charts | Chart.js 4 |
| Backend | Python 3, Flask |
| Auth | JWT (Flask-JWT-Extended) |
| Database | SQLite (dev) → PostgreSQL (prod) |
| ORM | SQLAlchemy |
| ML | scikit-learn (recommendation engine) |
| Data | IPCC AR6 emission factors |

---

## 📊 Emission Data Sources

- **Transport**: IPCC AR6 Working Group III (2022)
- **Home Energy**: UK DEFRA GHG Conversion Factors (2023)
- **Diet**: Poore & Nemecek, Science (2018)
- **Shopping**: Carbon Trust product lifecycle assessments
- **Benchmarks**: Our World in Data / Global Carbon Project

---

*Built for hackathon-speed prototyping, production-quality architecture.*
