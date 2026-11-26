from pydantic import BaseModel, Field
from src.constants.job_state import EvidenceState, JobState


class RunInput(BaseModel):
    parameter: int = Field(strict=True, ge=1)


class RunEntry(BaseModel):
    id: int
    case_id: int
    case_title: str
    status: JobState
    parameter: int
    actor: str
    created_at: int
    finished_at: int | None
    result: dict | None
    failure: str | None
    digest: str | None
    evidence_status: EvidenceState
    invalidated_at: int | None
    invalidation_reason: str | None
