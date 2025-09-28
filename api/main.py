import os, hashlib, json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

from .config import load_config, pick_variant_by_bucket

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
app = FastAPI(title="AB Onboarding Service", version="0.1.0")
cfg = load_config()

def stable_bucket(user_id: str, experiment_key: str) -> int:
    h = hashlib.sha256(f"{user_id}:{experiment_key}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100

def get_assignment(user_id: str, experiment_key: str) -> Optional[str]:
    with engine.begin() as conn:
        row = conn.execute(
            text("select variant from assignments where user_id=:u and experiment_key=:e"),
            {"u": user_id, "e": experiment_key},
        ).first()
        return row[0] if row else None

def save_assignment(user_id: str, experiment_key: str, variant: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("""
                insert into assignments (user_id, experiment_key, variant)
                values (:u, :e, :v)
                on conflict (user_id, experiment_key) do nothing
            """),
            {"u": user_id, "e": experiment_key, "v": variant},
        )

class AssignResponse(BaseModel):
    experiment_key: str
    variant: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "api"

class EventIn(BaseModel):
    user_id: str
    experiment_key: str
    variant: str
    event_type: str
    metadata: Optional[Dict[str, Any]] = None

class EventOut(BaseModel):
    status: str
    id: int

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.get("/assign", response_model=AssignResponse)
def assign(user_id: str = Query(...), experiment: str = Query(...)):
    exp = cfg.experiments.get(experiment)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if not exp.enabled:
        raise HTTPException(status_code=403, detail="Experiment disabled")

    current = get_assignment(user_id=user_id, experiment_key=experiment)
    if current:
        return AssignResponse(experiment_key=experiment, variant=current)

    bucket = stable_bucket(user_id, experiment)
    variant = pick_variant_by_bucket(exp.allocation, bucket)
    save_assignment(user_id, experiment, variant)
    return AssignResponse(experiment_key=experiment, variant=variant)

@app.post("/event", response_model=EventOut)
def log_event(evt: EventIn):
    assigned = get_assignment(evt.user_id, evt.experiment_key)
    if assigned and assigned != evt.variant:
        raise HTTPException(
            status_code=400,
            detail=f"Variant mismatch: assigned {assigned}, got {evt.variant}",
        )
    if not assigned:
        save_assignment(evt.user_id, evt.experiment_key, evt.variant)

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                insert into events_raw (user_id, experiment_key, variant, event_type, metadata)
                values (:u, :e, :v, :t, :m)
                returning id
            """),
            {
                "u": evt.user_id,
                "e": evt.experiment_key,
                "v": evt.variant,
                "t": evt.event_type,
                "m": json.dumps(evt.metadata) if evt.metadata else None,
            },
        ).first()
        return EventOut(status="ok", id=row[0])
