import { api } from "../api/workbench.js";
import { errorText, field } from "../components/common/fields.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { table } from "../components/common/table.js";
import { submit } from "../hooks/submit.js";
import { navigate } from "../router/router.js";
import { el } from "../utils/dom.js";
import { time } from "../utils/format.js";

function queueForm(config, selected) {
  const form = el("form", {class: "queue-form"},
    field(config.parameter_label, el("input", {
      name: "parameter", type: "number", min: 1, max: config.max_parameter, required: true, value: config.default_parameter,
    })),
    el("button", {type: "submit"}, "提交执行"), errorText());
  submit(form, async values => {
    const run = await api.enqueue(selected.id, {parameter: Number(values.get("parameter"))});
    navigate(`runs/${run.id}`);
  });
  return form;
}

function registration(config, selected) {
  const data = selected ? JSON.stringify(selected.payload, null, 2) : "{}";
  const form = el("form", {id: "case-form"},
    field("名称", el("input", {name: "title", required: true, minlength: 2, maxlength: 120,
      value: selected ? `${selected.title} · 复演` : ""})),
    field("说明", el("input", {name: "description", maxlength: 420, value: selected?.description || ""})),
    field(`${config.unit}内容`, el("textarea", {name: "payload", spellcheck: "false", required: true, rows: 12}, data),
      selected ? "可以保留演示数据，也可以编辑 JSON 后保存。" : "输入业务 JSON。"),
    errorText(), el("button", {type: "submit"}, "保存资料"));
  submit(form, async values => {
    let payload;
    try {
      payload = JSON.parse(values.get("payload"));
    } catch {
      throw new Error("资料 JSON 无法解析，请检查括号、引号和逗号");
    }
    const entry = await api.createCase({title: values.get("title"), description: values.get("description"), payload});
    navigate(`cases/${entry.id}`);
  });
  return form;
}

function correctionForm(selected) {
  const form = el("form", {id: "correction-form"},
    field("勘误原因", el("input", {name: "reason", required: true, minlength: 3, maxlength: 320,
      placeholder: "例如：D-2 测记内容记错、W-1138 归属琴体应为 ORG-31"})),
    field("更正后的资料 JSON", el("textarea", {name: "payload", spellcheck: "false", required: true, rows: 12},
      JSON.stringify(selected.payload, null, 2)),
      "可更正测记、维修单归属（organ_id）及随卷资料；保存后即刻判定既有证明效力。"),
    errorText(), el("button", {type: "submit"}, "提交勘误"));
  submit(form, async values => {
    let payload;
    try {
      payload = JSON.parse(values.get("payload"));
    } catch {
      throw new Error("资料 JSON 无法解析，请检查括号、引号和逗号");
    }
    await api.correctCase(selected.id, {reason: values.get("reason"), payload});
    window.dispatchEvent(new Event("hashchange"));
  });
  return form;
}

function correctionHistory(history) {
  if (!history.length) return empty("该资料还没有勘误记录。");
  return table(["版本", "原因", "失效批次", "勘误人", "时间"], history.map(item =>
    [`v${item.version}`, item.reason,
      item.affected_runs.length ? item.affected_runs.map(id => `#${id}`).join("、") : "无",
      item.actor, time(item.created_at)]), "勘误记录");
}

export async function casesPage(config, user, route) {
  const cases = await api.cases();
  const selected = cases.find(item => item.id === route.id) ?? cases.at(-1);
  const operator = user.role === "operator";
  const history = selected ? await api.corrections(selected.id) : [];
  const detail = selected ? [
    el("p", {}, selected.description),
    operator ? queueForm(config, selected) : empty("当前账号可查看此资料。"),
    el("details", {}, el("summary", {}, "查看业务数据"), el("pre", {}, JSON.stringify(selected.payload, null, 2))),
  ] : [empty("先登记一条资料，再提交执行。")];
  const rightColumn = selected
    ? [section("提交勘误", correctionForm(selected)),
       section("登记为一条全新资料", el("details", {},
         el("summary", {}, "展开登记表单"), registration(config, selected)))]
    : [section("登记新资料", registration(config, selected))];
  return el("div", {class: "page"},
    pageHeading(config.modules[1], `${config.unit} · ${config.fixture}`),
    section("资料目录", cases.length ? table(["编号", "名称", "说明", "操作"], cases.map(item =>
      [item.code, item.title, item.description,
        el("a", {href: `#cases/${item.id}`, "aria-current": item.id === selected?.id ? "true" : null}, "选用")]),
      "资料目录") : empty("这里还没有资料。")),
    el("div", {class: "split case-split"},
      el("div", {class: "stack"},
        section(selected ? selected.title : "等待选择资料", ...detail),
        section("勘误记录", correctionHistory(history))),
      operator ? el("div", {class: "stack"}, ...rightColumn) : null));
}
