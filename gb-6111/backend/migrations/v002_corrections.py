from sqlalchemy import text

from src.models import corrections  # noqa: F401  Register the new table.
from src.models.base import metadata


def upgrade(connection):
    # Version 2 adds the correction ledger and run-level evidence validity.
    metadata.create_all(connection)
    columns = {row[0] for row in connection.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'runs'"
    ))}
    additions = {
        "snapshot_payload": "ALTER TABLE runs ADD COLUMN snapshot_payload JSON",
        "evidence_status": "ALTER TABLE runs ADD COLUMN evidence_status VARCHAR(16) NOT NULL DEFAULT 'valid'",
        "invalidated_at": "ALTER TABLE runs ADD COLUMN invalidated_at BIGINT",
        "invalidation_reason": "ALTER TABLE runs ADD COLUMN invalidation_reason VARCHAR(320)",
    }
    for column, statement in additions.items():
        if column not in columns:
            connection.execute(text(statement))
    # 存量批次没有交单快照，回填为当前资料，保持其证据效力与现状一致。
    connection.execute(text(
        "UPDATE runs SET snapshot_payload = "
        "(SELECT payload FROM cases WHERE cases.id = runs.case_id) "
        "WHERE snapshot_payload IS NULL"
    ))
