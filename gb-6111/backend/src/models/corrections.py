from sqlalchemy import JSON, BigInteger, Column, ForeignKey, Integer, String, Table
from .base import metadata


corrections = Table(
    "case_corrections", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", ForeignKey("cases.id"), nullable=False, index=True),
    Column("version", Integer, nullable=False),
    Column("reason", String(320), nullable=False),
    Column("changes", JSON(none_as_null=True), nullable=False),
    Column("affected_runs", JSON(none_as_null=True), nullable=False),
    Column("actor", String(48), nullable=False),
    Column("created_at", BigInteger, nullable=False),
)
