"""勘误差异与证明影响分析。

勘误改变「所选维修单」或「随卷资料」时，对应证明即刻失效；
影响判定只看批次交单时冻结的快照与当前资料之间的差异。
"""

from src.domain.relations import RELATIONS
from src.utils.serial import canonical_json


def index_records(payload, relation):
    key = relation.columns[0]
    return {item[key]: item for item in payload.get(relation.key, [])}


def describe_changes(before, after):
    """按三张随卷表和选中工单列出结构化差异，便于审计留痕。"""
    changes = {}
    for relation in RELATIONS:
        old_rows = index_records(before, relation)
        new_rows = index_records(after, relation)
        detail = []
        for key in sorted(set(old_rows) | set(new_rows)):
            if key not in old_rows:
                detail.append({"action": "added", "record": key})
            elif key not in new_rows:
                detail.append({"action": "removed", "record": key})
            elif canonical_json(old_rows[key]) != canonical_json(new_rows[key]):
                detail.append({"action": "updated", "record": key})
        if detail:
            changes[relation.key] = detail
    old_selected = list(before.get("requested", []))
    new_selected = list(after.get("requested", []))
    if old_selected != new_selected:
        changes["requested"] = {
            "removed": [key for key in old_selected if key not in new_selected],
            "added": [key for key in new_selected if key not in old_selected],
        }
    return changes


def selection_closure(payload, requested):
    """批次实际复原范围的逐行快照：上限内工单、其父琴体及其全部子测记。"""
    visits = index_records(payload, RELATIONS[1])
    organs = index_records(payload, RELATIONS[0])
    readings = index_records(payload, RELATIONS[2])
    organ_ids = {visits[key]["organ_id"] for key in requested if key in visits}
    reading_ids = {key for key, item in readings.items() if item["visit_id"] in requested}
    return {
        # 琴体名称随卷导出，变化也要让证据失效。
        "organ_rows": {key: organs.get(key) for key in organ_ids},
        "visit_rows": {key: visits.get(key) for key in requested},
        "reading_rows": {key: readings.get(key) for key in reading_ids},
    }


def run_affected(snapshot, current, parameter):
    """证明对应的复原范围在勘误前后是否发生变化。"""
    requested = snapshot.get("requested", [])[:parameter]
    before = selection_closure(snapshot, requested)
    after = selection_closure(current, requested)
    # 选中工单缺失（被删除）或闭包内任何一行随卷资料变化，都改变这份证明的内容。
    for row_key in ("organ_rows", "visit_rows", "reading_rows"):
        if canonical_json(before[row_key]) != canonical_json(after[row_key]):
            return True
    return False
