from sqlalchemy import JSON, BigInteger, Column, ForeignKey, Integer, String, Table
from .base import metadata


runs = Table(
    "runs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", ForeignKey("cases.id"), nullable=False, index=True),
    Column("status", String(16), nullable=False, index=True),
    Column("parameter", Integer, nullable=False),
    Column("actor", String(48), nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("finished_at", BigInteger, nullable=True),
    Column("result", JSON(none_as_null=True), nullable=True),
    Column("failure", String(320), nullable=True),
    Column("digest", String(64), nullable=True),
    # 交单时冻结的资料快照，排队批次始终按这份资料完成，不受后续勘误影响。
    Column("snapshot_payload", JSON(none_as_null=True), nullable=True),
    Column("evidence_status", String(16), nullable=False, server_default="valid"),
    Column("invalidated_at", BigInteger, nullable=True),
    Column("invalidation_reason", String(320), nullable=True),
)
