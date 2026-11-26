from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from sqlalchemy import text


@dataclass(frozen=True)
class Relation:
    key: str
    label: str
    columns: tuple[str, ...]
    definition: str


RELATIONS = (
    Relation("organs", "琴体", ("organ_id", "label"), "organ_id text PRIMARY KEY, label text NOT NULL"),
    Relation(
        "visits", "维修工单", ("visit_id", "organ_id", "service_day"),
        "visit_id text PRIMARY KEY, organ_id text NOT NULL REFERENCES {organs}, service_day date NOT NULL",
    ),
    Relation(
        "readings", "测记", ("reading_id", "visit_id", "detail"),
        "reading_id text PRIMARY KEY, visit_id text NOT NULL REFERENCES {visits}, detail text NOT NULL",
    ),
)


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("请输入归档对象")
    keys_by_table = {}
    for relation in RELATIONS:
        items = payload.get(relation.key)
        if not isinstance(items, list) or len(items) > 400:
            raise ValueError(f"{relation.label}应为不超过 400 行的数组")
        keys = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != set(relation.columns):
                raise ValueError(f"{relation.label}字段须为 {'、'.join(relation.columns)}")
            if any(
                not isinstance(value, str)
                or not 1 <= len(value) <= 600
                or any(char == "\x00" or 0xD800 <= ord(char) <= 0xDFFF for char in value)
                for value in item.values()
            ):
                raise ValueError(f"{relation.label}字段须为非空且不超过 600 字的文本")
            key = item[relation.columns[0]]
            if key in keys:
                raise ValueError(f"{relation.label}主键重复：{key}")
            keys.add(key)
        keys_by_table[relation.key] = keys
    for visit in payload["visits"]:
        if date.fromisoformat(visit["service_day"]).isoformat() != visit["service_day"]:
            raise ValueError("维修日期须为 YYYY-MM-DD")
        if visit["organ_id"] not in keys_by_table["organs"]:
            raise ValueError(f"工单 {visit['visit_id']} 缺少琴体")
    for reading in payload["readings"]:
        if reading["visit_id"] not in keys_by_table["visits"]:
            raise ValueError(f"测记 {reading['reading_id']} 缺少工单")
    requested = payload.get("requested")
    if not isinstance(requested, list) or not requested or len(requested) > 100:
        raise ValueError("请选择 1 到 100 张工单")
    if any(not isinstance(key, str) or key not in keys_by_table["visits"] for key in requested):
        raise ValueError("选中工单必须存在于源卷")
    if len(set(requested)) != len(requested):
        raise ValueError("选中工单双重登记")
    if payload.get("simulate_damage") not in (None, *keys_by_table):
        raise ValueError("损伤段只能是 organs、visits、readings")


def create_tables(db, kind):
    suffix = uuid4().hex[:12]
    names = {rel.key: f"organ_{kind}_{rel.key}_{suffix}" for rel in RELATIONS}
    for rel in RELATIONS:
        ddl = rel.definition.format_map(names)
        db.execute(text(f"CREATE TEMP TABLE {names[rel.key]} ({ddl}) ON COMMIT DROP"))
    return names


def write_source(db, names, payload):
    for rel in RELATIONS:
        if payload[rel.key]:
            columns = ", ".join(rel.columns)
            binds = ", ".join(
                f"CAST(:{column} AS date)" if column == "service_day" else f":{column}"
                for column in rel.columns
            )
            db.execute(text(f"INSERT INTO {names[rel.key]} ({columns}) VALUES ({binds})"), payload[rel.key])


def select_sql(source, relation):
    organs, visits = source["organs"], source["visits"]
    if relation.key == "organs":
        condition = f"WHERE organ_id IN (SELECT organ_id FROM {visits} WHERE visit_id = ANY(%s))"
    else:
        condition = "WHERE visit_id = ANY(%s)"
    return (
        f"SELECT {', '.join(relation.columns)} FROM {source[relation.key]} "
        f"{condition} ORDER BY {relation.columns[0]} COLLATE \"C\""
    )
