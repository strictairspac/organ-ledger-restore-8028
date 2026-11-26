from time import time

from fastapi import HTTPException
from sqlalchemy import insert, select, update

from src.constants.job_state import EvidenceState, JobState
from src.domain import scenario
from src.domain.corrections import describe_changes, run_affected
from src.models.cases import cases
from src.models.corrections import corrections
from src.models.runs import runs
from src.utils.serial import canonical_json
from .audit import record


def list_for_case(db, case_id):
    rows = db.execute(
        select(corrections).where(corrections.c.case_id == case_id).order_by(corrections.c.version)
    ).mappings()
    return [dict(row) for row in rows]


def apply(db, case_id, data, actor):
    entry = db.execute(select(cases).where(cases.c.id == case_id)).mappings().first()
    if entry is None:
        raise HTTPException(404, "资料不存在")
    before = entry["payload"]
    after = data.payload
    if canonical_json(before) == canonical_json(after):
        raise HTTPException(422, "勘误后的资料与原值一致，没有需要更正的内容")
    validator = getattr(scenario, "validate", None)
    if validator is not None:
        try:
            validator(after)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    changes = describe_changes(before, after)
    # 只评估已完成且当前仍有效的证明；行锁让勘误与 worker 完成批次串行化，
    # 已失效的批次不因改回原值而恢复效力。
    finished = db.execute(
        select(runs).where(
            runs.c.case_id == case_id,
            runs.c.status == JobState.DONE,
            runs.c.evidence_status == EvidenceState.VALID,
        ).with_for_update()
    ).mappings().all()
    affected = [
        run["id"] for run in finished
        if run_affected(run["snapshot_payload"], after, run["parameter"])
    ]
    now = int(time())
    if affected:
        reason = f"勘误改变了所选维修单或随卷资料：{data.reason}"[:320]
        db.execute(update(runs).where(runs.c.id.in_(affected)).values(
            evidence_status=EvidenceState.INVALIDATED,
            invalidated_at=now,
            invalidation_reason=reason,
        ))
    next_version = (db.execute(
        select(corrections.c.version).where(corrections.c.case_id == case_id)
        .order_by(corrections.c.version.desc()).limit(1)
    ).scalar() or 0) + 1
    change = db.execute(insert(corrections).values(
        case_id=case_id,
        version=next_version,
        reason=data.reason,
        changes=changes,
        affected_runs=affected,
        actor=actor,
        created_at=now,
    ))
    db.execute(update(cases).where(cases.c.id == case_id).values(payload=after))
    record(db, "correct_case", actor, "case", case_id)
    for run_id in affected:
        record(db, "invalidate_evidence", actor, "run", run_id)
    saved = db.execute(
        select(corrections).where(corrections.c.id == change.inserted_primary_key[0])
    ).mappings().one()
    return dict(saved)
