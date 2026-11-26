import { api } from "../api/workbench.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { evidenceStatus, status } from "../components/common/status.js";
import { table } from "../components/common/table.js";
import { poll } from "../hooks/poll.js";
import { el } from "../utils/dom.js";
import { time } from "../utils/format.js";

function reportState(run) {
  const invalid = run.evidence_status === "invalidated";
  return el("div", {class: "stack", id: "run-state"},
    el("p", {class: "state-line"}, status(run.status),
      run.status === "done" ? evidenceStatus(run.evidence_status) : null),
    el("p", {}, run.status === "queued" ? "后台正在处理，页面会自动更新。" : run.failure || run.result?.summary),
    invalid ? el("p", {class: "feedback", "data-testid": "invalidated"}, run.invalidation_reason) : null,
    run.status === "done" ?
      el("a", {class: "button", href: `#evidence/${run.id}`},
        invalid ? "查看失效证明" : "查看业务证据") : null);
}

export async function runsPage(config, route, signal) {
  const items = await api.runs();
  const latest = route.id ? await api.run(route.id, signal) : items[0];
  const detail = latest ? reportState(latest) : empty("进入资料页，选用一个业务样本并提交执行。");
  async function refresh() {
    try {
      const next = await api.run(latest.id, signal);
      if (!signal.aborted) {
        detail.replaceChildren(...reportState(next).childNodes);
        const badge = document.querySelector(`[data-run="${next.id}"] .status`);
        if (badge) badge.replaceWith(status(next.status));
      }
      return next.status === "queued";
    } catch (error) {
      if (!signal.aborted) detail.append(el("p", {role: "alert"}, error.message));
      return false;
    }
  }
  if (latest?.status === "queued") poll(refresh, signal);
  return el("div", {class: "page"},
    pageHeading(config.modules[2], config.parameter_label),
    latest ? section(latest.case_title, detail) : detail,
    section("执行批次", items.length ? table(["资料", "编号", "参数", "执行状态", "证明效力", "提交时间"],
      items.map(run => [el("a", {"data-run": run.id, href: `#runs/${run.id}`}, run.case_title), run.id,
        run.parameter, el("span", {"data-run": run.id}, status(run.status)),
        run.status === "done" ? evidenceStatus(run.evidence_status) : "—", time(run.created_at)]), "执行批次") :
      empty("暂无执行记录。")));
}
