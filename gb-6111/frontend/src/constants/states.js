export const States = Object.freeze({
  queued: "等待执行", done: "已完成", failed: "执行失败",
});

export const EvidenceStates = Object.freeze({
  valid: "证明有效", invalidated: "证明失效",
});

export const Actions = Object.freeze({
  create_case: "登记资料", enqueue: "提交执行", done: "执行完成", failed: "执行失败", review: "复核签署",
  correct_case: "勘误资料", invalidate_evidence: "证明失效",
});
