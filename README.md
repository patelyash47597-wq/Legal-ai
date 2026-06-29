# ⚖️ LegalAI — Contract Risk Analyzer

> AI-powered legal contract risk analysis. Upload a PDF contract and get instant risk assessment with clause-by-clause breakdown.

![Python](https://img.shields.io/badge/python-3.12-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688) ![React](https://img.shields.io/badge/React-18-61DAFB)

---

## ✨ Features

- 📄 **PDF Upload** — Upload any legal contract PDF
- 🔍 **Clause Extraction** — Automatically segments contract into individual clauses
- ⚠️ **Risk Detection** — Identifies HIGH / MEDIUM / LOW risk clauses using pattern matching
- 🤖 **AI Explanations** — Groq LLM explains why each clause is risky
- 🗄️ **History** — All analyses saved to PostgreSQL database
- 📊 **Dashboard** — Visual summary of risk distribution

---

## 🛠️ Tech Stack

**Backend**
- FastAPI + Uvicorn
- PostgreSQL
- spaCy (clause extraction)
- pypdf (PDF parsing)
- Groq LLM API (AI explanations)

**Frontend**
- React 18
- Deployed on Vercel

---

## 🚀 Local Setup

### Prerequisites
- Python 3.12
- Node.js 18+
- PostgreSQL

### Backend

```bash
# Clone repo
git clone https://github.com/patelyash47597-wq/Legal-ai.git
cd Legal-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Setup environment variables
cp .env.example .env
# Fill in your values in .env

# Run
python main.py
```

### Frontend

```bash
cd legal-ai-frontend
npm install
npm start
```

---

## ⚙️ Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key ([get here](https://console.groq.com/api-keys)) |
| `HF_TOKEN` | HuggingFace token ([get here](https://huggingface.co/settings/tokens)) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/analyze` | Upload & analyze PDF contract |
| `GET` | `/contracts` | List all analyzed contracts |
| `GET` | `/contracts/{id}/results` | Get results for a contract |
| `GET` | `/reports/all` | Get all analysis reports |
| `GET` | `/docs` | Swagger UI |

---

## 📁 Project Structure

```
Legal-ai/
├── main.py                     # FastAPI entry point
├── requirements.txt
├── render.yaml                 # Render deployment config
├── app/
│   ├── api/
│   │   └── routes.py           # All API endpoints
│   ├── services/
│   │   ├── parser.py           # PDF text extraction
│   │   ├── industry_clause_engine.py  # Clause segmentation
│   │   ├── risk_engine.py      # Risk scoring
│   │   └── explainer.py        # Groq AI explanations
│   ├── database/
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── models.py           # DB models
│   │   └── crud.py             # DB operations
│   └── startup.py              # App startup tasks
├── data/
│   └── processed/              # Analysis output files
└── legal-ai-frontend/          # React frontend
```

---

## 🔒 Risk Levels

| Level | Description |
|-------|-------------|
| 🔴 **HIGH** | Clauses with dangerous patterns like "no liability", "sole discretion", "terminate immediately" |
| 🟡 **MEDIUM** | Clauses with vague language like "reasonable efforts", "may terminate" |
| 🟢 **LOW** | Standard clauses like "governing law", "severability" |

---

## 👨‍💻 Author

Built by **Yash Patel**

---

## 📄 License

MIT License