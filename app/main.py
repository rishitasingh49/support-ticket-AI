from fastapi import FastAPI
from pydantic import BaseModel

from app.query_engine import answer_question
from app.anomalies import get_all_anomalies

app = FastAPI(title="Support Ticket AI System")


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/query")
def query(request: QuestionRequest):
    return answer_question(request.question)


@app.get("/anomalies")
def anomalies():
    return get_all_anomalies()