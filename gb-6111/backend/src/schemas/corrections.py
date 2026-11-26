from pydantic import BaseModel, Field, field_validator


class CorrectionInput(BaseModel):
    reason: str = Field(min_length=3, max_length=320)
    payload: dict

    @field_validator("reason")
    @classmethod
    def check_reason(cls, reason):
        if len(reason.strip()) < 3:
            raise ValueError("勘误原因至少需要三个字符")
        return reason.strip()


class CorrectionEntry(BaseModel):
    id: int
    case_id: int
    version: int
    reason: str
    changes: dict
    affected_runs: list[int]
    actor: str
    created_at: int
