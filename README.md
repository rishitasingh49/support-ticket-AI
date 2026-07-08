# Support Ticket AI System

An AI-powered system to query customer support ticket data in plain English, and automatically flag anomalous tickets — built with FastAPI, Groq (LLM), and SQLite.

## Features

- **Natural language querying**: ask questions like "How many tickets are open?" and get real, data-grounded answers.
- **Anomaly detection**: automatically flags tickets with unusually long resolution times, and high-priority tickets left unresolved too long.
- **REST API**: 3 endpoints — health check, natural language query, and anomaly report.

```
CSV file
   │
   ▼
db.py  →  loads into SQLite (data/tickets.db)

User question
   │
   ▼
query_engine.py
   │
   ├─► llm.py (Groq) turns the question into SQL
   ├─► runs that SQL on SQLite, gets real rows back
   └─► llm.py phrases those rows into a natural sentence

anomalies.py
   │
   └─► runs pandas statistical rules directly on SQLite data (no LLM needed)

main.py (FastAPI)
   │
   └─► exposes it all via /health, /query, /anomalies
```

**Why this design:** the LLM never sees the raw ticket data — it only ever sees the table schema and generates SQL. The SQL is executed by real code, not the LLM, so answers can't be hallucinated numbers. Anomaly detection is pure statistics/rules (mean + 2×std, and a 24h SLA rule) — more reliable and explainable than asking an LLM to "guess" what's anomalous.

## Setup

1. Clone the repo and cd into it:
git clone https://github.com/rishitasingh49/support-ticket-AI.git
cd support-ticket-AI

2. Install dependencies:
pip install -r requirements.txt

3. Get a free Groq API key at https://console.groq.com and create a .env file (copy .env.example) with:
GROQ_API_KEY=your_key_here

4. Build the database from the CSV (run once):
python -m app.db

5. Start the API:
python -m uvicorn app.main:app --reload

Interactive docs: http://127.0.0.1:8000/docs

## Model / Tools Used

- **LLM**: Groq free tier, llama-3.1-8b-instant
- **API**: FastAPI + Uvicorn
- **Storage**: SQLite (via pandas to_sql)

## Sample Run (real output from this project)

**Question:** "How many tickets are currently open?"

{
  "sql": "SELECT COUNT(ticket_id) FROM tickets WHERE status = 'Open';",
  "row_count": 1,
  "data": [{ "COUNT(ticket_id)": 111 }],
  "answer": "There are 111 tickets currently open."
}

**Question:** "Which agent has the lowest average customer rating?"

{
  "sql": "SELECT agent_id FROM tickets GROUP BY agent_id ORDER BY AVG(customer_rating) ASC LIMIT 1",
  "row_count": 1,
  "data": [{ "agent_id": "AGT-08" }],
  "answer": "The agent with the lowest average customer rating is AGT-08."
}

**Anomaly detection output (excerpt):**

{
  "ticket_id": "TKT-130",
  "priority": "Medium",
  "status": "Resolved",
  "resolution_time_hrs": 114.3,
  "anomaly_reason": "Resolution time exceeds mean+2*std (59.2h)"
}

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /query | Ask a natural language question ({"question": "..."}) |
| GET | /anomalies | Get flagged anomalous tickets |

## Known Limitations

- SQL safety check only blocks non-SELECT statements; not a full SQL injection sandbox (acceptable for a local read-only SQLite file).
- LLM SQL generation can occasionally misinterpret ambiguous questions.
- No conversation memory — each question is handled independently.
- Anomaly thresholds (mean + 2×std, 24h SLA) are simple defaults.

## What I'd Improve With More Time

- Add caching for repeated questions.
- Add a retry loop: if generated SQL errors, feed the error back to the LLM to self-correct.
- Add authentication on the API endpoints.
- Add a lightweight UI (Streamlit) for non-technical users.
