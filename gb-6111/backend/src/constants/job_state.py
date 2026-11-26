from enum import StrEnum


class JobState(StrEnum):
    QUEUED = "queued"
    DONE = "done"
    FAILED = "failed"


class EvidenceState(StrEnum):
    VALID = "valid"
    INVALIDATED = "invalidated"
