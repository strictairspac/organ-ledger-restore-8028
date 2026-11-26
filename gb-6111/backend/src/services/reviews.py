from time import time

from fastapi import HTTPException
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from src.constants.job_state import EvidenceState, JobState
from src.models.reviews import reviews
from . import audit, runs


def get(db, run_id):
    row = db.execute(select(reviews).where(reviews.c.run_id == run_id)).mappings().first()
    return dict(row) if row else None


def sign(db, run_id, data, actor):
    run = runs.get(db, run_id)
    if run["status"] != JobState.DONE:
        raise HTTPException(409, "批次执行成功后才能签核")
    if run["evidence_status"] == EvidenceState.INVALIDATED:
        raise HTTPException(409, "该证明已因勘误失效，重新执行批次后才能签核新证明")
    try:
        db.execute(insert(reviews).values(run_id=run_id, note=data.note, actor=actor, created_at=int(time())))
    except IntegrityError as exc:
        raise HTTPException(409, "该批次已经签核") from exc
    audit.record(db, "review", actor, "run", run_id)
    return get(db, run_id)
