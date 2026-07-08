import pandas as pd
from app.db import get_connection
from app.llm import ask_llm

SCHEMA_DESCRIPTION = """
Table name: tickets
Columns:
- ticket_id (TEXT)
- created_at (DATETIME, format 'YYYY-MM-DD HH:MM:SS')
- category (TEXT: Billing, Technical, General)
- priority (TEXT: Low, Medium, High, Critical)
- status (TEXT: Open, Resolved, Escalated)
- response_time_hrs (FLOAT)
- resolution_time_hrs (FLOAT, NULL if not yet resolved)
- agent_id (TEXT)
- customer_rating (FLOAT 1-5, NULL if not yet rated)
- issue_summary (TEXT)
"""
SQL_SYSTEM_PROMPT = f"""You are a SQL generator for a SQLite database.
{SCHEMA_DESCRIPTION}

Rules:
- Return ONLY a single valid SQLite SELECT query. No explanation, no markdown, no ```sql fences.
- Never use INSERT, UPDATE, DELETE, or DROP - only SELECT.
- Use standard SQLite date functions if the question involves dates (e.g. datetime('now')).
"""
def clean_sql(raw_sql: str) -> str:
    sql = raw_sql.strip()
    sql = sql.replace("```sql", "").replace("```", "")
    return sql.strip()


def is_safe_select(sql: str) -> bool:
    lowered = sql.strip().lower()
    forbidden = ["insert", "update", "delete", "drop", "alter", "attach", "pragma"]
    return lowered.startswith("select") and not any(word in lowered for word in forbidden)
def question_to_sql(question: str) -> str:
    raw = ask_llm(prompt=question, system=SQL_SYSTEM_PROMPT)
    return clean_sql(raw)


def run_sql(sql: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df
def phrase_answer(question: str, result_df: pd.DataFrame) -> str:
    if result_df.empty:
        return "I ran the query but found no matching results."

    preview = result_df.head(20).to_dict(orient="records")
    prompt = f"""The user asked: "{question}"
The query result (as JSON rows) is: {preview}

Write a short, direct, natural-language answer using only this data. Do not invent numbers."""
    return ask_llm(prompt)


def answer_question(question: str) -> dict:
    sql = question_to_sql(question)

    if not is_safe_select(sql):
        return {
            "question": question,
            "sql": sql,
            "error": "Generated query was rejected for safety reasons.",
            "answer": None,
        }

    try:
        result_df = run_sql(sql)
    except Exception as e:
        return {
            "question": question,
            "sql": sql,
            "error": f"SQL execution failed: {e}",
            "answer": None,
        }

    answer_text = phrase_answer(question, result_df)

    return {
        "question": question,
        "sql": sql,
        "row_count": len(result_df),
        "data": result_df.head(20).to_dict(orient="records"),
        "answer": answer_text,
    }