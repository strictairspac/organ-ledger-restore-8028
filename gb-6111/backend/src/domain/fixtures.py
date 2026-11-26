BASE_RECORDS = {
    "organs": [
        {"organ_id": "ORG-17", "label": "橡山礼堂管风琴"},
        {"organ_id": "ORG-22", "label": "澄木教学厅管风琴"},
        {"organ_id": "ORG-31", "label": "青松排练厅管风琴"},
    ],
    "visits": [
        {"visit_id": "W-1126", "organ_id": "ORG-17", "service_day": "2026-11-02"},
        {"visit_id": "W-1131", "organ_id": "ORG-17", "service_day": "2026-11-10"},
        {"visit_id": "W-1138", "organ_id": "ORG-22", "service_day": "2026-11-15"},
        {"visit_id": "W-1142", "organ_id": "ORG-31", "service_day": "2026-11-18"},
    ],
    "readings": [
        {"reading_id": "D-1", "visit_id": "W-1126", "detail": "低音风箱补胶\n连续试吹十分钟"},
        {"reading_id": "D-2", "visit_id": "W-1131", "detail": "主音栓调为 441 Hz"},
        {"reading_id": "D-3", "visit_id": "W-1131", "detail": "更换演奏台触点\t四组"},
        {"reading_id": "D-4", "visit_id": "W-1138", "detail": "压力读数 78 mmH₂O"},
        {"reading_id": "D-5", "visit_id": "W-1142", "detail": "三号配重松脱"},
    ],
}
FIXTURES = [
    {
        "code": "ORG-VOL-2411",
        "title": "十一月外借维修卷",
        "description": "选 W-1131 与 W-1138 复原，工单和子测记随卷，未入选工单不应进入目标。",
        "payload": {**BASE_RECORDS, "requested": ["W-1131", "W-1138"]},
    },
    {
        "code": "ORG-VOL-2411-CORRUPT",
        "title": "测记归档受损演练",
        "description": "输入归档传输损伤标记，检查正式导入前即阻断。",
        "payload": {
            **BASE_RECORDS,
            "requested": ["W-1126"],
            "simulate_damage": "readings",
        },
    },
]
